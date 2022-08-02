"""
CSV-qb Writer
-------------

Output writer for CSV-qb
"""
import itertools
import json
import logging
import re
from dataclasses import field
from pathlib import Path
from typing import Tuple, Dict, Any, List, Iterable, Set

import pandas as pd

from csvcubedmodels.rdf.dependency import RdfGraphDependency
from csvcubedmodels import rdf
from csvcubedmodels.rdf import skos, rdfs
from csvcubedmodels.rdf.resource import (
    ExistingResourceWithLiteral,
    Resource,
    ExistingResource,
    maybe_existing_resource,
)

from csvcubed.models.cube import *
from csvcubed.utils.uri import (
    get_last_uri_part,
    csvw_column_name_safe,
    get_data_type_uri_from_str,
)
from csvcubed.utils.csvw import get_dependent_local_files
from csvcubed.utils.qb.cube import (
    get_columns_of_dsd_type,
    QbColumnarDsdType,
)
from csvcubed.utils.dict import rdf_resource_to_json_ld
from csvcubed.utils.qb.standardise import (
    convert_data_values_to_uri_safe_values,
    ensure_int_columns_are_ints,
)
from csvcubed.utils.file import copy_files_to_directory_with_structure
from .skoscodelistwriter import SkosCodeListWriter
from .urihelpers.skoscodelist import SkosCodeListNewUriHelper
from .urihelpers.qbcube import QbCubeNewUriHelper
from .urihelpers.skoscodelistconstants import SCHEMA_URI_IDENTIFIER
from .writerbase import WriterBase
from ..models.cube import (
    QbAttribute,
    ExistingQbAttribute,
    NewQbAttribute,
    QbMultiMeasureDimension,
    QbMultiUnits,
    QbAttributeLiteral,
)
from ..models.cube.qb.components.codelist import NewQbCodeListInCsvW
from ..models.rdf.newattributevalueresource import NewAttributeValueResource
from ..models.rdf.newunitresource import NewUnitResource
from ..models.cube.qb.components.arbitraryrdf import RdfSerialisationHint
from csvcubed.models.rdf.qbdatasetincatalog import QbDataSetInCatalog
from ..utils.qb.validation.observations import get_observation_status_columns


_logger = logging.getLogger(__name__)

VIRT_UNIT_COLUMN_NAME = "virt_unit"


@dataclass
class QbWriter(WriterBase):
    cube: QbCube
    csv_file_name: str = field(init=False)
    raise_missing_uri_safe_value_exceptions: bool = field(default=True, repr=False)
    _new_uri_helper: QbCubeNewUriHelper = field(init=False)

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
        self._new_uri_helper = QbCubeNewUriHelper(self.cube)

    def write(self, output_folder: Path):
        # Map all labels to their corresponding URI-safe-values, where possible.
        # Also converts all appropriate columns to the pandas categorical format.

        _logger.info(f"Beginning CSV-W Generation: {self.csv_file_name}")
        
        ensure_int_columns_are_ints(self.cube)

        # Bring the pandas representation of bolleans inline with what the csvw spec requires
        # True != true, False != false
        assert isinstance(self.cube.data, pd.DataFrame)
        for pandas_column_label in self.cube.data.columns.values:
            if self.cube.data[pandas_column_label].dtype == "bool":
                self.cube.data[pandas_column_label] = self.cube.data[pandas_column_label].apply(
                    lambda x: "true" if x is True else "false" if x is False else x
                )

        _logger.info('Calling data values to uri safe values')
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
                    "aboutUrl": self._get_about_url(),
                },
            }
        ]

        tables += self._get_table_references_needed_for_foreign_keys()

        self._output_new_code_list_csvws(output_folder)

        csvw_metadata = {
            "@context": "http://www.w3.org/ns/csvw",
            "@id": self._new_uri_helper.get_dataset_uri(),
            "tables": tables,
            "rdfs:seeAlso": self._get_additional_rdf_metadata(),
        }

        metadata_json_output_path = output_folder / self.csv_metadata_file_name
        with open(metadata_json_output_path, "w+") as f:
            _logger.debug("Writing CSV-W JSON-LD to %s", metadata_json_output_path)
            json.dump(csvw_metadata, f, indent=4)

        if self.cube.data is not None:
            csv_output_file_path = output_folder / self.csv_file_name
            _logger.debug("Writing CSV to %s", csv_output_file_path)
            self.cube.data.to_csv(csv_output_file_path, index=False)

    def _get_additional_rdf_metadata(self) -> List[dict]:
        """
        :return: the additional RDF metadata to be serialised in the CSV-W.
        """
        see_also = rdf_resource_to_json_ld(self._generate_qb_dataset_dsd_definitions())

        for dependencies in self._get_rdf_file_dependencies():
            see_also += rdf_resource_to_json_ld(dependencies)

        for attribute_value in self._get_new_attribute_value_resources():
            see_also += rdf_resource_to_json_ld(attribute_value)

        for unit in self._get_new_unit_resources():
            see_also += rdf_resource_to_json_ld(unit)

        return see_also

    def _output_new_code_list_csvws(self, output_folder: Path) -> None:
        for column in get_columns_of_dsd_type(self.cube, NewQbDimension):
            code_list = column.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug(
                    "Writing code list %s to '%s' directory.", code_list, output_folder
                )

                code_list_writer = self._get_writer_for_code_list(code_list)
                code_list_writer.write(output_folder)
            elif isinstance(code_list, NewQbCodeListInCsvW):
                # find the CSV-W codelist and all dependent relative files and copy them into the output_folder
                _logger.debug(
                    "Copying legacy code list %s (with dependent files) to '%s' directory.",
                    code_list,
                    output_folder,
                )

                dependent_files = get_dependent_local_files(
                    code_list.schema_metadata_file_path
                )
                files_relative_to = code_list.schema_metadata_file_path.parent
                copy_files_to_directory_with_structure(
                    [code_list.schema_metadata_file_path] + list(dependent_files),
                    files_relative_to,
                    output_folder,
                )

    def _generate_csvw_columns_for_cube(self) -> List[Dict[str, Any]]:
        columns = [self._generate_csvqb_column(c) for c in self.cube.columns]
        virtual_columns = self._generate_virtual_columns_for_cube()
        return columns + virtual_columns

    def _get_columns_for_foreign_keys(self) -> List[QbColumn[NewQbDimension]]:
        columns = []
        for col in get_columns_of_dsd_type(self.cube, NewQbDimension):
            if col.structural_definition.code_list is not None and isinstance(
                col.structural_definition.code_list,
                (NewQbCodeList, NewQbCodeListInCsvW),
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
            elif isinstance(code_list, NewQbCodeListInCsvW):
                _logger.debug(
                    "Referencing legacy dataset-local code list %s with assumed table schema.",
                    code_list,
                )

                tables.append(
                    {
                        "url": code_list.csv_file_relative_path_or_uri,
                        # n.b. the below tableSchema works for *both* standard and composite legacy code lists
                        # due to the `notation` column supporting both `Notation` *and* `URI` as column titles.
                        "tableSchema": "https://gss-cogs.github.io/family-schemas/codelist-schema.json",
                        "suppressOutput": True,
                    }
                )
            else:
                raise ValueError(f"Unmatched codelist type {type(code_list)}")

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
            elif isinstance(code_list, NewQbCodeListInCsvW):
                _logger.debug(
                    "Configuring foreign key constraints for legacy dataset-local code list %s",
                    code_list,
                )

                foreign_keys.append(
                    {
                        "columnReference": csvw_column_name_safe(
                            col.uri_safe_identifier
                        ),
                        "reference": {
                            "resource": code_list.csv_file_relative_path_or_uri,
                            "columnReference": "notation", # NewQbCodeListInCsvW are used for historic reasons and they always use the notation key for their primary key. External users cannot create NewQbCodeListInCsvW.
                        },
                    }
                )
            else:
                raise ValueError(f"Unmatched codelist type {type(code_list)}")

        return foreign_keys

    def _generate_virtual_columns_for_cube(self) -> List[Dict[str, Any]]:
        virtual_columns = []
        for column in self.cube.columns:
            if isinstance(column, QbColumn):
                if isinstance(column.structural_definition, QbObservationValue):
                    virtual_columns += self._generate_virtual_columns_for_obs_val(
                        column.structural_definition
                    )

        return virtual_columns

    def _generate_virtual_columns_for_obs_val(
        self, obs_val: QbObservationValue
    ) -> List[Dict[str, Any]]:
        _logger.debug("Configuring per-row virtual columns.")

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
                "valueUrl": self._new_uri_helper.get_dataset_uri(),
            },
        ]
        unit = obs_val.unit
        if unit is not None:
            _logger.debug("Adding virtual unit column.")
            virtual_columns.append(
                {
                    "name": VIRT_UNIT_COLUMN_NAME,
                    "virtual": True,
                    "propertyUrl": "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure",
                    "valueUrl": self._get_unit_uri(unit),
                }
            )
        if isinstance(obs_val, QbSingleMeasureObservationValue):
            _logger.debug("Adding virtual measure column.")
            virtual_columns.append(
                {
                    "name": "virt_measure",
                    "virtual": True,
                    "propertyUrl": "http://purl.org/linked-data/cube#measureType",
                    "valueUrl": self._get_measure_uri(obs_val.measure),
                }
            )
        return virtual_columns

    def _get_qb_dataset_with_catalog_metadata(self) -> QbDataSetInCatalog:
        qb_dataset_with_metadata = QbDataSetInCatalog(
            self._new_uri_helper.get_dataset_uri()
        )
        self.cube.metadata.configure_dcat_dataset(qb_dataset_with_metadata)
        return qb_dataset_with_metadata

    def _generate_qb_dataset_dsd_definitions(self) -> QbDataSetInCatalog:
        dataset = self._get_qb_dataset_with_catalog_metadata()
        dataset.structure = rdf.qb.DataStructureDefinition(
            self._new_uri_helper.get_structure_uri()
        )
        component_ordinal = 1
        for column in self.cube.columns:
            if isinstance(column, QbColumn):
                component_specs_for_col = self._get_qb_component_specs_for_col(
                    column.uri_safe_identifier, column.structural_definition
                )
                component_properties_for_col = [
                    p for s in component_specs_for_col for p in s.componentProperties
                ]
                dataset.structure.componentProperties |= set(
                    component_properties_for_col
                )
                for component in component_specs_for_col:
                    component.order = component_ordinal
                    component_ordinal += 1

                dataset.structure.components |= set(component_specs_for_col)

        return dataset

    def _get_qb_component_specs_for_col(
        self, column_name_uri_safe: str, component: QbStructuralDefinition
    ) -> Iterable[rdf.qb.ComponentSpecification]:
        if isinstance(component, QbDimension):
            return [
                self._get_qb_dimension_specification(column_name_uri_safe, component)
            ]
        elif isinstance(component, QbAttribute):
            return [
                self._get_qb_attribute_specification(column_name_uri_safe, component)
            ]
        elif isinstance(component, QbMultiUnits):
            return [self._get_qb_units_column_specification(column_name_uri_safe)]
        elif isinstance(component, QbMultiMeasureDimension):
            return self._get_qb_measure_dimension_specifications(component)
        elif isinstance(component, QbObservationValue):
            return self._get_qb_obs_val_specifications(component)
        else:
            raise Exception(f"Unhandled component type {type(component)}")

    def _get_obs_val_data_type(self) -> str:
        observation_value_columns = get_columns_of_dsd_type(
            self.cube, QbObservationValue
        )
        # Given the data shapes we accept as input, there should always be one (and only one) Observation Value
        # column in a cube.
        observation_value_column = observation_value_columns[0]
        data_type = observation_value_column.structural_definition.data_type
        return get_data_type_uri_from_str(data_type)

    def _get_qb_units_column_specification(
        self, column_name_uri_safe: str
    ) -> rdf.qb.AttributeComponentSpecification:
        component = rdf.qb.AttributeComponentSpecification(
            self._new_uri_helper.get_component_uri(column_name_uri_safe)
        )
        component.componentRequired = True
        component.attribute = ExistingResource(
            "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        )
        component.componentProperties.add(component.attribute)

        _logger.debug(
            "Generated units component %s.",
            component.uri,
        )

        return component

    def _get_qb_obs_val_specifications(
        self, observation_value: QbObservationValue
    ) -> List[rdf.qb.ComponentSpecification]:
        specs: List[rdf.qb.ComponentSpecification] = [
            # We always output the measure-dimension style of the QB spec.
            # so each observation need to have a dimension specifying the measure type.
            self._get_measure_type_dimension_component_spec()
        ]

        unit = observation_value.unit
        if unit is not None:
            specs.append(self._get_qb_units_column_specification("unit"))

        if isinstance(observation_value, QbSingleMeasureObservationValue):
            specs.append(
                self._get_qb_measure_component_specification(observation_value.measure)
            )
        elif isinstance(observation_value, QbMultiMeasureObservationValue):
            pass
        else:
            raise Exception(
                f"Unmatched Observation value component of type {type(observation_value)}."
            )

        return specs

    def _get_measure_type_dimension_component_spec(
        self,
    ) -> rdf.qb.DimensionComponentSpecification:
        measure_dimension_spec = rdf.qb.DimensionComponentSpecification(
            self._new_uri_helper.get_component_uri("measure-type")
        )
        measure_dimension_spec.dimension = ExistingResource(
            "http://purl.org/linked-data/cube#measureType"
        )
        measure_dimension_spec.componentProperties.add(measure_dimension_spec.dimension)
        return measure_dimension_spec

    @staticmethod
    def _get_unit_uri_safe_identifier(unit: QbUnit) -> str:
        if isinstance(unit, ExistingQbUnit):
            return get_last_uri_part(unit.unit_uri)
        elif isinstance(unit, NewQbUnit):
            return unit.uri_safe_identifier
        else:
            raise Exception(f"Unhandled unit type {type(unit)}")

    def _get_qb_measure_dimension_specifications(
        self, measure_dimension: QbMultiMeasureDimension
    ) -> List[rdf.qb.MeasureComponentSpecification]:
        measure_specs: List[rdf.qb.MeasureComponentSpecification] = []
        for measure in measure_dimension.measures:
            measure_specs.append(self._get_qb_measure_component_specification(measure))

        return measure_specs

    def _get_qb_measure_component_specification(
        self, measure: QbMeasure
    ) -> rdf.qb.MeasureComponentSpecification:
        if isinstance(measure, ExistingQbMeasure):
            component_uri = self._new_uri_helper.get_component_uri(
                get_last_uri_part(measure.measure_uri)
            )
            component = rdf.qb.MeasureComponentSpecification(component_uri)
            component.measure = ExistingResource(measure.measure_uri)
            component.componentProperties.add(component.measure)

            measure.copy_arbitrary_triple_fragments_to_resources(
                {RdfSerialisationHint.Component: component}
            )
        elif isinstance(measure, NewQbMeasure):
            component = rdf.qb.MeasureComponentSpecification(
                self._new_uri_helper.get_component_uri(measure.uri_safe_identifier)
            )
            component.measure = rdf.qb.MeasureProperty(
                self._new_uri_helper.get_measure_uri(measure.uri_safe_identifier)
            )
            component.measure.label = measure.label
            component.measure.comment = measure.description
            component.measure.subPropertyOf = maybe_existing_resource(
                measure.parent_measure_uri
            )
            component.measure.source = maybe_existing_resource(measure.source_uri)
            component.measure.range = ExistingResource(self._get_obs_val_data_type())
            component.componentProperties.add(component.measure)

            measure.copy_arbitrary_triple_fragments_to_resources(
                {
                    RdfSerialisationHint.Component: component,
                    RdfSerialisationHint.Property: component.measure,
                }
            )

        else:
            raise Exception(f"Unhandled measure type {type(measure)}")

        _logger.debug(
            "Generated component %s with measure %s.",
            component.uri,
            component.measure.uri,
        )

        return component

    def _get_qb_dimension_specification(
        self, column_name_uri_safe: str, dimension: QbDimension
    ) -> rdf.qb.DimensionComponentSpecification:
        if isinstance(dimension, ExistingQbDimension):
            component = rdf.qb.DimensionComponentSpecification(
                self._new_uri_helper.get_component_uri(column_name_uri_safe)
            )
            component.dimension = ExistingResource(dimension.dimension_uri)
            dimension.copy_arbitrary_triple_fragments_to_resources(
                {RdfSerialisationHint.Component: component}
            )
        elif isinstance(dimension, NewQbDimension):
            component = rdf.qb.DimensionComponentSpecification(
                self._new_uri_helper.get_component_uri(dimension.uri_safe_identifier)
            )
            component.dimension = rdf.qb.DimensionProperty(
                self._new_uri_helper.get_dimension_uri(dimension.uri_safe_identifier)
            )
            component.dimension.label = dimension.label
            component.dimension.comment = dimension.description
            component.dimension.subPropertyOf = maybe_existing_resource(
                dimension.parent_dimension_uri
            )
            component.dimension.source = maybe_existing_resource(dimension.source_uri)
            component.dimension.range = rdfs.Class(
                self._new_uri_helper.get_class_uri(dimension.uri_safe_identifier)
            )

            dimension.copy_arbitrary_triple_fragments_to_resources(
                {
                    RdfSerialisationHint.Component: component,
                    RdfSerialisationHint.Property: component.dimension,
                }
            )

            if dimension.code_list is not None:
                component.dimension.code_list = self._get_code_list_resource(
                    dimension.code_list
                )

        else:
            raise Exception(f"Unhandled dimension component type {type(dimension)}.")

        component.componentProperties.add(component.dimension)

        _logger.debug(
            "Generated component %s with dimension %s.",
            component.uri,
            component.dimension.uri,
        )

        return component

    def _get_code_list_resource(
        self, code_list: QbCodeList
    ) -> Resource[skos.ConceptScheme]:
        if isinstance(code_list, ExistingQbCodeList):
            return ExistingResource(code_list.concept_scheme_uri)
        elif isinstance(code_list, NewQbCodeList):
            # The resource is created elsewhere. There is a separate CSV-W definition for the code-list
            return ExistingResource(
                SkosCodeListNewUriHelper(
                    code_list, self.cube.uri_style
                ).get_scheme_uri()
            )
        elif isinstance(code_list, NewQbCodeListInCsvW):
            return ExistingResource(code_list.concept_scheme_uri)
        else:
            raise Exception(f"Unhandled codelist type {type(code_list)}")

    def _get_qb_attribute_specification(
        self, column_name_uri_safe: str, attribute: QbAttribute
    ) -> rdf.qb.AttributeComponentSpecification:
        if isinstance(attribute, ExistingQbAttribute):
            component = rdf.qb.AttributeComponentSpecification(
                self._new_uri_helper.get_component_uri(column_name_uri_safe)
            )
            if isinstance(attribute, QbAttributeLiteral):
                component.attribute = ExistingResourceWithLiteral(
                    attribute.attribute_uri
                )
                component.attribute.range = ExistingResource(
                    get_data_type_uri_from_str(attribute.data_type)
                )
            else:
                component.attribute = ExistingResource(attribute.attribute_uri)

            attribute.copy_arbitrary_triple_fragments_to_resources(
                {RdfSerialisationHint.Component: component}
            )
        elif isinstance(attribute, NewQbAttribute):
            component = rdf.qb.AttributeComponentSpecification(
                self._new_uri_helper.get_component_uri(attribute.uri_safe_identifier)
            )
            component.attribute = rdf.qb.AttributeProperty(
                self._new_uri_helper.get_attribute_uri(attribute.uri_safe_identifier)
            )
            component.attribute.label = attribute.label
            component.attribute.comment = attribute.description
            component.attribute.subPropertyOf = maybe_existing_resource(
                attribute.parent_attribute_uri
            )
            component.attribute.source = maybe_existing_resource(attribute.source_uri)
            # todo: Find some way to link the codelist we have to the
            #  ComponentProperty?

            if isinstance(attribute, QbAttributeLiteral):
                component.attribute.range = ExistingResource(
                    get_data_type_uri_from_str(attribute.data_type)
                )
            attribute.copy_arbitrary_triple_fragments_to_resources(
                {
                    RdfSerialisationHint.Component: component,
                    RdfSerialisationHint.Property: component.attribute,
                }
            )
        else:
            raise Exception(f"Unhandled attribute component type {type(attribute)}.")

        component.componentRequired = attribute.is_required
        component.componentProperties.add(component.attribute)

        _logger.debug(
            "Generated component %s with attribute %s.",
            component.uri,
            component.attribute.uri,
        )

        return component

    def _get_rdf_file_dependencies(self) -> List[RdfGraphDependency]:
        """
        Define RDF dependencies of this CSV-W file which help the end-user understand the triples expressed by this CSV-W.

        :return: RDF resource models to define dependencies on other RDF files.
        """
        rdf_file_dependencies: List[RdfGraphDependency] = []

        dimension_columns = get_columns_of_dsd_type(self.cube, NewQbDimension)
        for column in dimension_columns:
            dimension = column.structural_definition
            code_list = dimension.code_list
            if isinstance(code_list, NewQbCodeList):
                dependency = RdfGraphDependency(
                    self._new_uri_helper.get_void_dataset_dependency_uri(
                        code_list.metadata.uri_safe_identifier
                    )
                )

                code_list_writer = self._get_writer_for_code_list(code_list)
                dependency.uri_space = (
                    code_list_writer.uri_helper.get_uri_prefix_for_doc()
                )

                dependency.dependent_rdf_file_location = ExistingResource(
                    f"./{code_list_writer.csv_metadata_file_name}"
                )

                rdf_file_dependencies.append(dependency)

        return rdf_file_dependencies

    def _get_writer_for_code_list(self, code_list) -> SkosCodeListWriter:
        return SkosCodeListWriter(code_list, self.cube.uri_style)

    def _get_new_attribute_value_resources(self) -> List[NewAttributeValueResource]:
        """
        :return: RDF resource models to define New Attribute Values
        """
        new_attribute_value_resources: List[NewAttributeValueResource] = []
        attribute_columns = get_columns_of_dsd_type(self.cube, QbAttribute)
        for column in attribute_columns:
            if isinstance(column.structural_definition, NewQbAttribute):
                column_identifier = column.structural_definition.uri_safe_identifier
            else:
                column_identifier = column.uri_safe_identifier

            for value in column.structural_definition.new_attribute_values:  # type: ignore
                assert isinstance(value, NewQbAttributeValue)

                attribute_value_uri = self._new_uri_helper.get_attribute_value_uri(
                    column_identifier, value.uri_safe_identifier
                )
                new_attribute_value_resource = NewAttributeValueResource(
                    attribute_value_uri
                )
                new_attribute_value_resource.label = value.label
                new_attribute_value_resource.comment = value.description
                new_attribute_value_resource.source_uri = maybe_existing_resource(
                    value.source_uri
                )
                new_attribute_value_resource.parent_attribute_value_uri = (
                    maybe_existing_resource(value.parent_attribute_value_uri)
                )

                _logger.debug(
                    "Generated New Attribute Value %s.",
                    new_attribute_value_resource.uri,
                )

                new_attribute_value_resources.append(new_attribute_value_resource)

        return new_attribute_value_resources

    def _get_new_unit_resources(self) -> List[NewUnitResource]:
        """
        :return: RDF Resources to defined new units
        """
        units: Set[QbUnit] = {
            u
            for col in get_columns_of_dsd_type(self.cube, QbMultiUnits)
            for u in col.structural_definition.units  # type: ignore
        }

        units |= {
            col.structural_definition.unit
            for col in get_columns_of_dsd_type(self.cube, QbObservationValue)
            if col.structural_definition.unit is not None
        }

        def get_new_base_units(u: QbUnit) -> set[QbUnit]:
            if (
                isinstance(u, NewQbUnit)
                and u.base_unit is not None
                and isinstance(u.base_unit, NewQbUnit)
            ):
                new_base_units = get_new_base_units(u.base_unit)
                new_base_units.add(u.base_unit)

                return new_base_units

            return set()

        units |= {base_unit for u in units for base_unit in get_new_base_units(u)}

        new_units: Set[NewQbUnit] = {u for u in units if isinstance(u, NewQbUnit)}

        new_unit_resources: List[NewUnitResource] = []
        for unit in new_units:
            unit_uri = self._get_unit_uri(unit)
            new_unit_resource = NewUnitResource(unit_uri)
            new_unit_resource.label = unit.label
            new_unit_resource.comment = unit.description
            new_unit_resource.source_uri = maybe_existing_resource(unit.source_uri)

            maybe_unit_uri = (
                None if unit.base_unit is None else self._get_unit_uri(unit.base_unit)
            )

            new_unit_resource.base_unit_uri = maybe_existing_resource(maybe_unit_uri)
            new_unit_resource.base_unit_scaling_factor = unit.base_unit_scaling_factor

            new_unit_resource.has_qudt_quantity_kind = maybe_existing_resource(
                unit.qudt_quantity_kind_uri
            )
            new_unit_resource.qudt_conversion_multiplier = (
                unit.si_base_unit_conversion_multiplier
            )

            _logger.debug("Generated new unit resource %s.", new_unit_resource.uri)

            new_unit_resources.append(new_unit_resource)

        return new_unit_resources

    def _generate_csvqb_column(self, column: CsvColumn) -> Dict[str, Any]:
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
            raise Exception(
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

        (
            property_url,
            default_value_url,
        ) = self._get_default_property_value_uris_for_column(column)

        _logger.debug(
            "Column has default propertyUrl '%s' and default valueUrl '%s'.",
            property_url,
            default_value_url,
        )

        if property_url is not None:
            csvw_col["propertyUrl"] = property_url

        if column.csv_column_uri_template is not None:
            # User-specified value overrides our default guess.
            csvw_col["valueUrl"] = column.csv_column_uri_template
        elif isinstance(column.structural_definition, QbAttributeLiteral):
            _logger.debug("Column valueUrl is left unset.")
            pass
        elif default_value_url is not None:
            csvw_col["valueUrl"] = default_value_url

        if isinstance(column.structural_definition, QbObservationValue):
            _logger.debug(
                "Setting CSV-W datatype to %s.", column.structural_definition.data_type
            )
            csvw_col["datatype"] = column.structural_definition.data_type
        elif isinstance(column.structural_definition, QbAttributeLiteral):
            _logger.debug(
                "Setting CSV-W datatype to %s.", column.structural_definition.data_type
            )
            csvw_col["datatype"] = column.structural_definition.data_type

        is_required = (
            isinstance(
                column.structural_definition,
                (QbDimension, QbMultiUnits, QbMultiMeasureDimension),
            )
            or (
                isinstance(column.structural_definition, QbAttribute)
                and column.structural_definition.get_is_required()
            )
            or (
                isinstance(column.structural_definition, QbObservationValue)
                and len(get_observation_status_columns(self.cube)) == 0
                # We cannot mark an observation value column as `required` if there are `obsStatus` columns defined
                # since we permit missing observation values where an `obsStatus` explains the reason.
            )
        )

        if is_required:
            _logger.debug("Column is required.")
        else:
            _logger.debug("Column is not required.")

        csvw_col["required"] = is_required

    def _get_default_property_value_uris_for_multi_units(
        self, column: QbColumn, multi_units: QbMultiUnits
    ) -> Tuple[str, str]:
        column_template_fragment = self._get_column_uri_template_fragment(column)
        all_units_new = all([isinstance(u, NewQbUnit) for u in multi_units.units])
        all_units_existing = all(
            [isinstance(u, ExistingQbUnit) for u in multi_units.units]
        )

        unit_value_uri: str
        if all_units_new:
            _logger.debug("All units are new; they define the column's valueUrl.")
            unit_value_uri = self._new_uri_helper.get_unit_uri(column_template_fragment)
        elif all_units_existing:
            _logger.debug("All units are existing.")
            unit_value_uri = column_template_fragment
        else:
            # todo: Come up with a solution for this!
            raise Exception(
                "Cannot handle a mix of new units and existing defined units."
            )

        return (
            "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure",
            unit_value_uri,
        )

    def _get_default_property_value_uris_for_multi_measure(
        self, column: QbColumn[QbMultiMeasureDimension]
    ) -> Tuple[str, str]:
        measure_value_uri = self._get_measure_dimension_column_measure_template_uri(
            column
        )

        return "http://purl.org/linked-data/cube#measureType", measure_value_uri

    def _get_measure_dimension_column_measure_template_uri(
        self, column: QbColumn[QbMultiMeasureDimension]
    ):
        all_measures_new = all(
            [isinstance(m, NewQbMeasure) for m in column.structural_definition.measures]
        )
        all_measures_existing = all(
            [
                isinstance(m, ExistingQbMeasure)
                for m in column.structural_definition.measures
            ]
        )

        column_template_fragment = self._get_column_uri_template_fragment(column)
        if all_measures_new:
            _logger.debug("All measures are new; they define the column's valueUrl.")
            return self._new_uri_helper.get_measure_uri(column_template_fragment)
        elif all_measures_existing:
            _logger.debug("All measures are existing.")
            if column.csv_column_uri_template is None:
                raise ValueError(
                    "A URI value template must be defined when a measures column reuses existing measures."
                )
            return column.csv_column_uri_template
        else:
            # todo: Come up with a solution for this!
            raise Exception(
                "Cannot handle a mix of new measures and existing defined measures."
            )

    def _get_default_property_value_uris_for_column(
        self, column: QbColumn
    ) -> Tuple[Optional[str], Optional[str]]:
        if isinstance(column.structural_definition, QbDimension):
            return self._get_default_property_value_uris_for_dimension(column)
        elif isinstance(column.structural_definition, QbAttribute):
            return self._get_default_property_value_uris_for_attribute(column)
        elif isinstance(column.structural_definition, QbMultiUnits):
            return self._get_default_property_value_uris_for_multi_units(
                column, column.structural_definition
            )
        elif isinstance(column.structural_definition, QbMultiMeasureDimension):
            return self._get_default_property_value_uris_for_multi_measure(column)
        elif isinstance(column.structural_definition, QbObservationValue):
            return self._get_default_property_value_uris_for_observation_value(
                column.structural_definition
            )
        else:
            raise Exception(
                f"Unhandled component type {type(column.structural_definition)}"
            )

    def _get_default_property_value_uris_for_observation_value(
        self,
        observation_value: QbObservationValue,
    ):
        if isinstance(observation_value, QbSingleMeasureObservationValue):
            _logger.debug(
                "Single-measure observation value propertyUrl defined by measure %s",
                observation_value.measure,
            )
            return self._get_measure_uri(observation_value.measure), None
        elif isinstance(observation_value, QbMultiMeasureObservationValue):
            multi_measure_dimension_col = self._get_single_column_of_type(
                QbMultiMeasureDimension
            )
            _logger.debug(
                "Multi-measure observation value propertyUrl defined by measure column %s",
                multi_measure_dimension_col.csv_column_title,
            )

            measure_uri_template = (
                self._get_measure_dimension_column_measure_template_uri(
                    multi_measure_dimension_col
                )
            )
            return measure_uri_template, None
        else:
            raise ValueError(
                f"Unmatched Observation Value type {type(observation_value)}"
            )

    def _get_single_column_of_type(
        self, t: Type[QbColumnarDsdType]
    ) -> QbColumn[QbColumnarDsdType]:
        cols = get_columns_of_dsd_type(self.cube, t)
        if len(cols) != 1:
            raise ValueError(
                f"Found {len(cols)} columns with component type {t} in cube. Expected 1."
            )
        return cols[0]

    def _get_default_property_value_uris_for_dimension(
        self, column: QbColumn[QbDimension]
    ) -> Tuple[str, Optional[str]]:
        dimension = column.structural_definition
        if isinstance(dimension, ExistingQbDimension):
            return (
                dimension.dimension_uri,
                self._get_column_uri_template_fragment(column),
            )
        elif isinstance(dimension, NewQbDimension):
            local_dimension_uri = self._new_uri_helper.get_dimension_uri(
                dimension.uri_safe_identifier
            )
            value_uri = self._get_column_uri_template_fragment(column)
            if dimension.code_list is None:
                _logger.debug(
                    "Dimension does not have code list; valueUrl defaults directly to column's value."
                )
            else:
                _logger.debug(
                    "Dimension valueUrl determined by code list %s.",
                    dimension.code_list,
                )
                value_uri = self._get_default_value_uri_for_code_list_concepts(
                    column, dimension.code_list
                )
            return local_dimension_uri, value_uri
        else:
            raise Exception(f"Unhandled dimension type {type(dimension)}")

    def _get_default_property_value_uris_for_attribute(
        self, column: QbColumn[QbAttribute]
    ) -> Tuple[str, str]:
        attribute = column.structural_definition
        column_uri_fragment = self._get_column_uri_template_fragment(column)
        value_uri = self._get_column_uri_template_fragment(column)
        if isinstance(attribute, ExistingQbAttribute):
            if len(attribute.new_attribute_values) > 0:
                _logger.debug(
                    "Existing Attribute has new attribute values which define the valueUrl."
                )
                # NewQbAttributeValues defined here.
                value_uri = self._new_uri_helper.get_attribute_value_uri(
                    column.uri_safe_identifier, column_uri_fragment
                )
            else:
                _logger.debug("Existing Attribute does not have new attribute values.")

            # N.B. We can't do mix-and-match New/Existing attribute values.

            return attribute.attribute_uri, value_uri
        elif isinstance(attribute, NewQbAttribute):
            local_attribute_uri = self._new_uri_helper.get_attribute_uri(
                attribute.uri_safe_identifier
            )

            if len(attribute.new_attribute_values) > 0:
                _logger.debug(
                    "New Attribute has new attribute values which define the valueUrl."
                )
                # NewQbAttributeValues defined here.
                value_uri = self._new_uri_helper.get_attribute_value_uri(
                    attribute.uri_safe_identifier, column_uri_fragment
                )
            else:
                _logger.debug("New Attribute does not have new attribute values.")

            # N.B. We can't do mix-and-match New/Existing attribute values.

            return local_attribute_uri, value_uri
        else:
            raise Exception(f"Unhandled attribute type {type(attribute)}")

    def _get_column_uri_template_fragment(
        self, column: CsvColumn, escape_value: bool = False
    ) -> str:
        if escape_value:
            return "{" + csvw_column_name_safe(column.uri_safe_identifier) + "}"

        return "{+" + csvw_column_name_safe(column.uri_safe_identifier) + "}"

    _legacy_external_code_list_pattern = re.compile("^(.*)/concept-scheme/(.*)$")
    _legacy_dataset_local_code_list_pattern = re.compile("^(.*)#scheme/(.*)$")
    _csvcubed_code_list_pattern = re.compile(
        "^(.*)#" + re.escape(SCHEMA_URI_IDENTIFIER) + "$"
    )

    def _get_default_value_uri_for_code_list_concepts(
        self, column: CsvColumn, code_list: QbCodeList
    ) -> str:
        column_uri_fragment = self._get_column_uri_template_fragment(column)

        if isinstance(code_list, ExistingQbCodeList):
            legacy_external_match = self._legacy_external_code_list_pattern.match(
                code_list.concept_scheme_uri
            )
            legacy_local_match = self._legacy_dataset_local_code_list_pattern.match(
                code_list.concept_scheme_uri
            )
            csvcubed_match = self._csvcubed_code_list_pattern.match(
                code_list.concept_scheme_uri
            )
            if legacy_external_match:
                _logger.debug(
                    "Existing concept scheme URI %s matches legacy family/global style.",
                    code_list.concept_scheme_uri,
                )
                m: re.Match = legacy_external_match
                # ConceptScheme URI:
                # http://gss-data.org.uk/def/concept-scheme/{code-list-name}
                # Concept URI:
                # http://gss-data.org.uk/def/concept-scheme/{code-list-name}/{notation}
                return f"{m.group(1)}/concept-scheme/{m.group(2)}/{column_uri_fragment}"
            elif legacy_local_match:
                _logger.debug(
                    "Existing concept scheme URI %s matches legacy dataset-local style.",
                    code_list.concept_scheme_uri,
                )
                m: re.Match = legacy_local_match
                # ConceptScheme URI:
                # http://gss-data.org.uk/data/gss_data/{family-name}/{dataset-root-name}#scheme/{code-list-name}
                # Concept URI:
                # http://gss-data.org.uk/data/gss_data/{family-name}/{dataset-root-name}#concept/{code-list-name}/{notation}
                return f"{m.group(1)}#concept/{m.group(2)}/{column_uri_fragment}"
            elif csvcubed_match:
                _logger.debug(
                    "Existing concept scheme URI %s matches csvcubed style.",
                    code_list.concept_scheme_uri,
                )
                m: re.Match = csvcubed_match
                # ConceptScheme URI:
                # {code-list-uri}#code-list
                # Concept URI:
                # {code-list-uri}#{notation}
                return f"{m.group(1)}#{column_uri_fragment}"
            else:
                _logger.warning(
                    "Existing code list URI %s does not match expected any known convention.",
                    code_list.concept_scheme_uri,
                )
                # Unexpected code-list URI. Does not match expected conventions.
                return column_uri_fragment
        elif isinstance(code_list, NewQbCodeList):
            _logger.debug(
                "valueUrl defined by new dataset-local code list %s",
                code_list.metadata.title,
            )
            return SkosCodeListNewUriHelper(
                code_list, self.cube.uri_style
            ).get_concept_uri(column_uri_fragment)
        elif isinstance(code_list, NewQbCodeListInCsvW):
            _logger.debug(
                "valueUrl defined by legacy dataset-local code list %s",
                code_list.concept_scheme_uri,
            )
            return re.sub(
                r"\{.?notation\}", column_uri_fragment, code_list.concept_template_uri
            )
        else:
            raise Exception(f"Unhandled codelist type {type(code_list)}")

    def _get_unit_uri(self, unit: QbUnit) -> str:
        if isinstance(unit, ExistingQbUnit):
            return unit.unit_uri
        elif isinstance(unit, NewQbUnit):
            return self._new_uri_helper.get_unit_uri(unit.uri_safe_identifier)
        else:
            raise Exception(f"Unmatched unit type {type(unit)}")

    def _get_measure_uri(self, measure: QbMeasure) -> str:
        if isinstance(measure, ExistingQbMeasure):
            return measure.measure_uri
        elif isinstance(measure, NewQbMeasure):
            return self._new_uri_helper.get_measure_uri(measure.uri_safe_identifier)
        else:
            raise Exception(f"Unmatched measure type {type(measure)}")

    def _get_about_url(self) -> str:
        # Todo: Dimensions are currently appended in the order in which the appear in the cube.
        #       We may want to alter this in the future so that the ordering is from
        #       least entropic dimension -> most entropic.
        #       E.g. http://base-uri/observations/male/1996/all-males-1996
        dimension_columns_templates: List[str] = []
        multi_measure_col_template: Optional[str] = None

        for c in self.cube.columns:
            if isinstance(c, QbColumn):
                if isinstance(c.structural_definition, QbDimension):
                    dimension_columns_templates.append(
                        f"{{{csvw_column_name_safe(c.uri_safe_identifier)}}}"
                    )
                elif isinstance(c.structural_definition, QbMultiMeasureDimension):
                    multi_measure_col_template = (
                        f"{{{csvw_column_name_safe(c.uri_safe_identifier)}}}"
                    )

        about_url_template = self._new_uri_helper.get_observation_uri(
            dimension_columns_templates, multi_measure_col_template
        )

        _logger.debug("aboutUrl template is %s", about_url_template)
        return about_url_template

    def _get_primary_key_columns(self) -> List[str]:
        dimension_columns: Iterable[QbColumn] = itertools.chain(
            get_columns_of_dsd_type(self.cube, QbDimension),
            get_columns_of_dsd_type(self.cube, QbMultiMeasureDimension),
        )

        primary_key_columns = [
            csvw_column_name_safe(c.csv_column_title) for c in dimension_columns
        ]

        _logger.debug("Primary key columns are %s", primary_key_columns)
        return primary_key_columns
