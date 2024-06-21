"""
CSV-qb Writer
-------------

Output writer for CSV-qb
"""

import itertools
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

import pandas as pd

from csvcubed import feature_flags
from csvcubed.definitions import SDMX_ATTRIBUTE_UNIT_URI
from csvcubed.models.cube.columns import CsvColumn, SuppressedCsvColumn
from csvcubed.models.cube.cube import QbCube
from csvcubed.models.cube.qb.columns import QbColumn
from csvcubed.models.cube.qb.components.attribute import (
    NewQbAttribute,
    QbAttribute,
    QbAttributeLiteral,
)
from csvcubed.models.cube.qb.components.codelist import NewQbCodeList
from csvcubed.models.cube.qb.components.dimension import NewQbDimension, QbDimension
from csvcubed.models.cube.qb.components.measuresdimension import QbMultiMeasureDimension
from csvcubed.models.cube.qb.components.observedvalue import QbObservationValue
from csvcubed.models.cube.qb.components.unitscolumn import QbMultiUnits
from csvcubed.utils.csvw import get_dependent_local_files
from csvcubed.utils.file import copy_files_to_directory_with_structure
from csvcubed.utils.qb.standardise import (
    convert_data_values_to_uri_safe_values,
    ensure_int_columns_are_ints,
)
from csvcubed.utils.qb.validation.observations import get_observation_status_columns
from csvcubed.utils.uri import csvw_column_name_safe
from csvcubed.writers.helpers.qbwriter.dsdtordfmodelshelper import DsdToRdfModelsHelper
from csvcubed.writers.helpers.qbwriter.urihelper import UriHelper
from csvcubed.writers.skoscodelistwriter import SkosCodeListWriter
from csvcubed.writers.writerbase import WriterBase

_logger = logging.getLogger(__name__)

VIRT_UNIT_COLUMN_NAME = "virt_unit"


@dataclass
class QbWriter(WriterBase):
    cube: QbCube
    csv_file_name: str = field(init=False)
    raise_missing_uri_safe_value_exceptions: bool = field(default=True, repr=False)
    _uris: UriHelper = field(init=False)
    _dsd: DsdToRdfModelsHelper = field(init=False)

    @property
    def csv_metadata_file_name(self) -> str:
        return f"{self.csv_file_name}-metadata.json"

    def __post_init__(self):
        self.csv_file_name = f"{self.cube.metadata.uri_safe_identifier}.csv"
        _logger.debug(
            "Initialising %s with CSV output set to '%s'",
            QbWriter.__name__,
            self.csv_file_name,
        )
        self._uris = UriHelper(self.cube)
        self._dsd = DsdToRdfModelsHelper(self.cube, self._uris)

    def write(self, output_folder: Path):
        # Map all labels to their corresponding URI-safe-values, where possible.
        # Also converts all appropriate columns to the pandas categorical format.
        _logger.debug("Beginning CSV-W Generation: '%s'", self.csv_file_name)

        ensure_int_columns_are_ints(self.cube)

        # Bring the pandas representation of booleans inline with what the csvw spec requires
        # True != true, False != false
        if isinstance(self.cube.data, pd.DataFrame):
            for pandas_column_label in self.cube.data.columns.values:
                if self.cube.data[pandas_column_label].dtype == "bool":
                    self.cube.data[pandas_column_label] = self.cube.data[
                        pandas_column_label
                    ].apply(
                        lambda x: "true" if x is True else "false" if x is False else x
                    )

        _logger.debug("Calling data values to uri safe values")
        convert_data_values_to_uri_safe_values(
            self.cube, self.raise_missing_uri_safe_value_exceptions
        )

        tables = [
            {
                "url": self.csv_file_name,
                "tableSchema": {
                    "columns": self._generate_csvw_columns_for_cube(),
                    "foreignKeys": self._generate_foreign_keys_for_cube(),
                    "primaryKey": self._get_primary_key_columns(),
                    "aboutUrl": self._uris.get_about_url(),
                },
            }
        ]

        tables += self._get_table_references_needed_for_foreign_keys()

        csvw_metadata = {
            "@context": "http://www.w3.org/ns/csvw",
            "@id": self._uris.get_distribution_uri(),
            "tables": tables,
            "rdfs:seeAlso": self._dsd.generate_data_structure_definitions(),
        }

        self._output_new_code_list_csvws(output_folder)

        metadata_json_output_path = output_folder / self.csv_metadata_file_name
        with open(metadata_json_output_path, "w+") as f:
            _logger.debug("Writing CSV-W JSON-LD to %s", metadata_json_output_path)
            json.dump(csvw_metadata, f, indent=4)

        if self.cube.data is not None:
            csv_output_file_path = output_folder / self.csv_file_name
            _logger.debug("Writing CSV to %s", csv_output_file_path)
            self.cube.data.to_csv(csv_output_file_path, index=False)

    def _output_new_code_list_csvws(self, output_folder: Path) -> None:
        for column in self.cube.get_columns_of_dsd_type(NewQbDimension):
            code_list = column.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug(
                    "Writing dimension code list %s to '%s' directory.",
                    code_list,
                    output_folder,
                )

                code_list_writer = self._get_writer_for_code_list(code_list)
                code_list_writer.write(output_folder)

        for column in self.cube.get_columns_of_dsd_type(NewQbAttribute):
            if feature_flags.ATTRIBUTE_VALUE_CODELISTS:
                code_list = column.structural_definition.code_list
                if isinstance(code_list, NewQbCodeList):
                    _logger.debug(
                        "Writing attribute code list %s to '%s' directory.",
                        code_list,
                        output_folder,
                    )

                    code_list_writer = self._get_writer_for_code_list(code_list)
                    code_list_writer.write(output_folder)

    def _generate_csvw_columns_for_cube(self) -> List[Dict[str, Any]]:
        columns = [self._generate_csvw_column_definition(c) for c in self.cube.columns]
        if self.cube.is_pivoted_shape:
            _logger.debug("The cube is in pivoted shape")
            columns += (
                self._generate_virtual_columns_for_obs_vals_in_pivoted_shape_cube()
            )
        else:
            _logger.debug("The cube is in standard shape")
            columns += self._generate_virtual_columns_for_standard_shape_cube()
        return columns

    def _get_columns_for_foreign_keys(
        self,
    ) -> List[QbColumn[Union[NewQbDimension, NewQbAttribute]]]:
        columns = []
        for col in self.cube.get_columns_of_dsd_type(NewQbDimension):
            if col.structural_definition.code_list is not None and isinstance(
                col.structural_definition.code_list, NewQbCodeList
            ):
                columns.append(col)
        if feature_flags.ATTRIBUTE_VALUE_CODELISTS:
            for col in self.cube.get_columns_of_dsd_type(NewQbAttribute):
                if col.structural_definition.code_list is not None and isinstance(
                    col.structural_definition.code_list, NewQbCodeList
                ):
                    columns.append(col)
        return columns

    def _get_table_references_needed_for_foreign_keys(self) -> List[dict]:
        tables = []
        for col in self._get_columns_for_foreign_keys():
            code_list = col.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug("Referencing dataset-local code list %s.", code_list)

                tables.append(
                    {
                        "url": f"{code_list.metadata.uri_safe_identifier}.csv",
                        "tableSchema": f"{code_list.metadata.uri_safe_identifier}.table.json",
                        "suppressOutput": True,
                    }
                )
            else:
                raise TypeError(f"Unmatched codelist type {type(code_list)}")

        return tables

    def _generate_foreign_keys_for_cube(self) -> List[dict]:
        foreign_keys: List[dict] = []
        for col in self._get_columns_for_foreign_keys():
            code_list = col.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug(
                    "Configuring foreign key constraints for dataset-local code list %s",
                    code_list,
                )
                foreign_keys.append(
                    {
                        "columnReference": csvw_column_name_safe(
                            col.uri_safe_identifier
                        ),
                        "reference": {
                            "resource": f"{code_list.metadata.uri_safe_identifier}.csv",
                            "columnReference": "uri_identifier",
                        },
                    }
                )
            else:
                raise TypeError(f"Unmatched codelist type {type(code_list)}")

        return foreign_keys

    def _generate_virtual_columns_for_obs_val_in_pivoted_shape_cube(
        self, obs_column: QbColumn[QbObservationValue]
    ) -> List[dict]:
        _logger.debug(
            "Generating virtual columns for obs val col '%s' in pivoted shape cube",
            obs_column.csv_column_title,
        )

        virtual_columns: List[dict] = []

        observation_uri = self._uris.get_observation_uri_for_pivoted_shape_data_set(
            obs_column
        )
        csvw_safe_obs_column_name = csvw_column_name_safe(obs_column.csv_column_title)
        measure = obs_column.structural_definition.measure
        assert measure is not None

        # Creates a virtual col for `?sliceUri qb:observation ?obsUri`
        virtual_columns.append(
            {
                "name": f"virt_obs_{csvw_safe_obs_column_name}",
                "virtual": True,
                "propertyUrl": "qb:observation",
                "valueUrl": observation_uri,
            }
        )
        # Creates a virtual col for `?obsUri qb:measureType ?measureUri`
        virtual_columns.append(
            {
                "name": f"virt_obs_{csvw_safe_obs_column_name}_meas",
                "virtual": True,
                "aboutUrl": observation_uri,
                "propertyUrl": "qb:measureType",
                "valueUrl": self._uris.get_measure_uri(measure),
            }
        )

        if obs_column.structural_definition.unit is not None:
            virtual_columns.append(
                {
                    "name": f"virt_obs_{csvw_safe_obs_column_name}_unit",
                    "virtual": True,
                    "aboutUrl": observation_uri,
                    "propertyUrl": SDMX_ATTRIBUTE_UNIT_URI,
                    "valueUrl": self._uris.get_unit_uri(
                        obs_column.structural_definition.unit
                    ),
                }
            )

        # For each dimension in the cube, creates the `?obsUri ?dimUri ?valueUri` triple.
        dimension_columns = self.cube.get_columns_of_dsd_type(QbDimension)
        for dimension_col in dimension_columns:
            _logger.debug(
                "Generating virtual column for dimension column with title '%s'",
                dimension_col.csv_column_title,
            )
            (
                property_url,
                value_url,
            ) = self._uris.get_default_property_value_uris_for_column(dimension_col)

            if dimension_col.csv_column_uri_template is not None:
                _logger.debug(
                    "Dimension column with title '%s'has a csv column uri template '%s' defined",
                    dimension_col.csv_column_title,
                    dimension_col.csv_column_uri_template,
                )
                value_url = dimension_col.csv_column_uri_template

            virtual_columns.append(
                {
                    "name": (
                        f"virt_dim_{csvw_safe_obs_column_name}_"
                        + csvw_column_name_safe(dimension_col.csv_column_title)
                    ),
                    "virtual": True,
                    "aboutUrl": observation_uri,
                    "propertyUrl": property_url,
                    "valueUrl": value_url,
                }
            )
        # Creates the virtual column for the triple `?obsUri rdf:type qb:Observation`
        virtual_columns.append(
            {
                "name": f"virt_obs_{csvw_safe_obs_column_name}_type",
                "virtual": True,
                "aboutUrl": observation_uri,
                "propertyUrl": "rdf:type",
                "valueUrl": "qb:Observation",
            }
        )
        # Creates a virtual column for the triple `?obsUri qb:dataSet ?dataSetUri`
        virtual_columns.append(
            {
                "name": f"virt_dataSet_{csvw_safe_obs_column_name}",
                "virtual": True,
                "aboutUrl": observation_uri,
                "propertyUrl": "qb:dataSet",
                "valueUrl": self._uris.get_distribution_uri(),
            }
        )

        return virtual_columns

    def _generate_virtual_columns_for_obs_vals_in_pivoted_shape_cube(
        self,
    ) -> List[Dict[str, Any]]:
        _logger.debug("Generating virtual columns for pivoted shape cube")

        virtual_columns: List[dict] = [
            # Generates the virtual column defining the `?sliceUri rdf:type qb:Slice` triple.
            {
                "name": "virt_slice",
                "virtual": True,
                "propertyUrl": "rdf:type",
                "valueUrl": "qb:Slice",
            },
            # Generates the virtual column defining the `?sliceUri qb:sliceStructure ?valueUrl` triple.
            {
                "name": "virt_slice_structure",
                "virtual": True,
                "propertyUrl": "qb:sliceStructure",
                "valueUrl": self._uris.get_slice_key_across_measures_uri(),
            },
        ]

        observation_value_columns = self.cube.get_columns_of_dsd_type(
            QbObservationValue
        )
        for obs_column in observation_value_columns:
            virtual_columns.extend(
                self._generate_virtual_columns_for_obs_val_in_pivoted_shape_cube(
                    obs_column
                )
            )

        return virtual_columns

    def _generate_virtual_columns_for_standard_shape_cube(self) -> List[Dict[str, Any]]:
        _logger.debug("Generating virtual columns for standard shape cube")

        virtual_columns = []
        for column in self.cube.columns:
            if isinstance(column, QbColumn):
                if isinstance(column.structural_definition, QbObservationValue):
                    _logger.debug(
                        "The column with title '%s' is an observation value column.",
                        column.csv_column_title,
                    )
                    virtual_columns += self._generate_virtual_columns_for_obs_val_in_standard_shape_cube(
                        column.structural_definition
                    )

        return virtual_columns

    def _generate_virtual_columns_for_obs_val_in_standard_shape_cube(
        self, obs_val: QbObservationValue
    ) -> List[Dict[str, Any]]:
        _logger.debug("Generating virtual columns for standard shape cube")

        virtual_columns: List[dict] = [
            {
                "name": "virt_type",
                "virtual": True,
                "propertyUrl": "rdf:type",
                "valueUrl": "http://purl.org/linked-data/cube#Observation",
            },
            {
                "name": "virt_dataset",
                "virtual": True,
                "propertyUrl": "http://purl.org/linked-data/cube#dataSet",
                "valueUrl": self._uris.get_distribution_uri(),
            },
        ]
        unit = obs_val.unit
        if unit is not None:
            _logger.debug("Adding virtual unit column for '%s'.", unit)
            virtual_columns.append(
                {
                    "name": VIRT_UNIT_COLUMN_NAME,
                    "virtual": True,
                    "propertyUrl": SDMX_ATTRIBUTE_UNIT_URI,
                    "valueUrl": self._uris.get_unit_uri(unit),
                }
            )

        return virtual_columns

    def _get_writer_for_code_list(self, code_list) -> SkosCodeListWriter:
        return SkosCodeListWriter(code_list, self.cube.uri_style)

    def _generate_csvw_column_definition(self, column: CsvColumn) -> Dict[str, Any]:
        _logger.debug(
            "Generating CSV-W Column Definition for '%s'", column.csv_column_title
        )

        csvw_col: Dict[str, Any] = {
            "titles": column.csv_column_title,
            "name": csvw_column_name_safe(column.uri_safe_identifier),
        }

        if isinstance(column, SuppressedCsvColumn):
            csvw_col["suppressOutput"] = True
            _logger.debug("'%s' is a suppressed column", column.csv_column_title)
        elif isinstance(column, QbColumn):
            self._define_csvw_column_for_qb_column(csvw_col, column)
        else:
            raise TypeError(
                f"Unhandled column type ({type(column)}) with title '{column.csv_column_title}'"
            )

        return csvw_col

    def _define_csvw_column_for_qb_column(
        self, csvw_col: dict, column: QbColumn
    ) -> None:
        _logger.debug(
            "Expanding CSV-W column definition for DSD column '%s' (%s).",
            column.csv_column_title,
            column.structural_definition.__class__.__name__,
        )

        # If the cube is in pivoted shape, check what the column represents to set the aboutUrl
        if self.cube.is_pivoted_shape:
            about_url = self._uris.get_about_url_for_csvw_col_in_pivoted_shape_cube(
                column
            )
            _logger.debug(
                "aboutUrl for column with title '%s' is '%s'",
                column.csv_column_title,
                about_url,
            )
            if about_url is not None:
                csvw_col["aboutUrl"] = about_url

        (
            property_url,
            default_value_url,
        ) = self._uris.get_default_property_value_uris_for_column(column)

        _logger.debug(
            "Column '%s' has default propertyUrl '%s' and default valueUrl '%s'.",
            column.csv_column_title,
            property_url,
            default_value_url,
        )

        if property_url is not None:
            csvw_col["propertyUrl"] = property_url

        if column.csv_column_uri_template is not None:
            # User-specified value overrides our default guess.
            csvw_col["valueUrl"] = column.csv_column_uri_template
        elif isinstance(column.structural_definition, QbAttributeLiteral):
            _logger.debug(
                "Column '%s' is Attribute Literal; valueUrl is left unset.",
                column.csv_column_title,
            )
        elif default_value_url is not None:
            csvw_col["valueUrl"] = default_value_url

        if isinstance(column.structural_definition, QbObservationValue):
            _logger.debug(
                "Setting CSV-W datatype for %s to %s.",
                column.csv_column_title,
                column.structural_definition.data_type,
            )
            csvw_col["datatype"] = column.structural_definition.data_type
        elif isinstance(column.structural_definition, QbAttributeLiteral):
            _logger.debug(
                "Setting CSV-W datatype for %s to %s.",
                column.csv_column_title,
                column.structural_definition.data_type,
            )
            csvw_col["datatype"] = column.structural_definition.data_type

        is_required = self._determine_whether_column_is_required(column)
        if is_required:
            _logger.debug("Column %s is required.", column.csv_column_title)
        else:
            _logger.debug("Column %s is not required.", column.csv_column_title)

        csvw_col["required"] = is_required

    def _get_primary_key_columns(self) -> List[str]:
        dimension_columns: Iterable[QbColumn[Any]] = itertools.chain(
            self.cube.get_columns_of_dsd_type(QbDimension),
            self.cube.get_columns_of_dsd_type(QbMultiMeasureDimension),
        )

        primary_key_columns = [
            csvw_column_name_safe(c.csv_column_title) for c in dimension_columns
        ]

        _logger.debug("Primary key columns are %s", primary_key_columns)
        return primary_key_columns

    def _determine_whether_column_is_required(self, column: QbColumn) -> bool:
        if isinstance(
            column.structural_definition,
            (QbDimension, QbMultiUnits, QbMultiMeasureDimension),
        ):
            return True
        elif (
            isinstance(column.structural_definition, QbAttribute)
            and column.structural_definition.get_is_required()
        ):
            obs_val_cols = self.cube.get_columns_of_dsd_type(QbObservationValue)
            if self.cube.is_pivoted_shape and len(obs_val_cols) > 1:
                # If the cube is in pivoted multi-measure shape, the attribute columns cannot be set to required.
                _logger.warning(
                    "Attribute column '%s' was marked as required, but the cube has multiple observed values columns. Attributes in multi-measure pivoted cubes cannot currently be marked as required.",
                    column.csv_column_title,
                )
                return False
            return True
        elif (
            isinstance(column.structural_definition, QbObservationValue)
            and len(get_observation_status_columns(self.cube)) == 0
        ):
            # We cannot mark an observation value column as `required` if there are `obsStatus` columns defined
            # since we permit missing observation values where an `obsStatus` explains the reason.
            return True

        return False
