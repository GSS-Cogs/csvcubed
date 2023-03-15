"""
Metadata Printer
----------------

Provides functionality for validating and detecting input metadata.json file.
"""

from dataclasses import dataclass, field
from os import linesep
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from pandas import DataFrame

from csvcubed.cli.inspect.inspectdatasetmanager import (
    get_concepts_hierarchy_info,
    get_dataset_observations_info,
    get_dataset_val_counts_info,
    load_csv_to_dataframe,
)
from csvcubed.models.csvcubedexception import (
    InputNotSupportedException,
    UnsupportedNumOfPrimaryKeyColNamesException,
)
from csvcubed.models.csvwtype import CSVWType
from csvcubed.models.inspectdataframeresults import (
    CodelistHierarchyInfoResult,
    DatasetObservationsByMeasureUnitInfoResult,
    DatasetObservationsInfoResult,
)
from csvcubed.models.sparqlresults import (
    CatalogMetadataResult,
    CodelistResult,
    CodelistsResult,
    ColumnDefinition,
    CubeTableIdentifiers,
    QubeComponentsResult,
)
from csvcubed.utils.csvdataset import transform_dataset_to_canonical_shape
from csvcubed.utils.printable import (
    get_printable_list_str,
    get_printable_tabular_str_from_list,
)
from csvcubed.utils.skos.codelist import (
    CodelistPropertyUrl,
    get_codelist_col_title_by_property_url,
    get_codelist_col_title_from_col_name,
)
from csvcubed.utils.sparql_handler.code_list_inspector import CodeListInspector
from csvcubed.utils.sparql_handler.column_component_info import ColumnComponentInfo
from csvcubed.utils.sparql_handler.csvw_inspector import CsvWInspector
from csvcubed.utils.sparql_handler.data_cube_inspector import DataCubeInspector


@dataclass
class MetadataPrinter:
    """
    This class produces the printables necessary for producing outputs to the CLI.
    """

    state: Union[DataCubeInspector, CodeListInspector]

    csvw_type_str: str = field(init=False)
    primary_csv_url: str = field(init=False)
    dataset: DataFrame = field(init=False)

    result_catalog_metadata: CatalogMetadataResult = field(init=False)
    # new stuff
    result_column_component_info: List[ColumnComponentInfo] = field(init=False)
    primary_cube_table_identifiers: CubeTableIdentifiers = field(init=False)
    result_qube_components: QubeComponentsResult = field(init=False)
    primary_csv_column_definitions: List[ColumnDefinition] = field(init=False)
    result_primary_csv_code_lists: CodelistsResult = field(init=False)
    result_dataset_observations_info: DatasetObservationsInfoResult = field(init=False)
    result_dataset_value_counts: DatasetObservationsByMeasureUnitInfoResult = field(
        init=False
    )
    result_code_list_cols: List[ColumnDefinition] = field(init=False)
    result_concepts_hierachy_info: CodelistHierarchyInfoResult = field(init=False)

    @staticmethod
    def get_csvw_type_str(csvw_type: CSVWType) -> str:
        if csvw_type == CSVWType.QbDataSet:
            return "data cube"
        elif csvw_type == CSVWType.CodeList:
            return "code list"
        else:
            raise InputNotSupportedException()

    def get_primary_csv_url(self) -> str:
        """Return the csv_url for the primary table in the graph."""
        primary_metadata = self.state.csvw_inspector.get_primary_catalog_metadata()
        if isinstance(self.state, DataCubeInspector):
            return self.state.get_cube_identifiers_for_data_set(
                primary_metadata.dataset_uri
            ).csv_url
        elif isinstance(self.state, CodeListInspector):
            return self.state.get_table_identifiers_for_concept_scheme(
                primary_metadata.dataset_uri
            ).csv_url
        else:
            raise InputNotSupportedException()

    @staticmethod
    def get_parent_label_unique_id_col_titles(
        columns: List[ColumnDefinition], primary_key_col: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        parent_notation_col_title = get_codelist_col_title_by_property_url(
            columns, CodelistPropertyUrl.SkosBroader
        )
        label_col_title = get_codelist_col_title_by_property_url(
            columns, CodelistPropertyUrl.RDFLabel
        )
        unique_identifier = get_codelist_col_title_from_col_name(
            columns, primary_key_col
        )

        return (parent_notation_col_title, label_col_title, unique_identifier)

    def generate_general_results(self):
        """
        Generates results related to data cubes and code lists.

        Member of :class:`./MetadataPrinter`.
        """
        csvw_inspector = self.state.csvw_inspector
        csvw_type = csvw_inspector.csvw_type

        self.csvw_type_str = self.get_csvw_type_str(csvw_type)
        self.result_catalog_metadata = csvw_inspector.get_primary_catalog_metadata()
        self.primary_csv_url = self.get_primary_csv_url()
        self.dataset = load_csv_to_dataframe(
            csvw_inspector.csvw_json_path, Path(self.primary_csv_url)
        )
        self.result_dataset_observations_info = get_dataset_observations_info(
            self.dataset,
            csvw_type,
            self.state.get_shape_for_csv(self.primary_csv_url)
            if isinstance(self.state, DataCubeInspector)
            else None,
        )

    def get_datacube_results(self):
        """
        Generates results specific to data cubes.

        Member of :class:`./MetadataPrinter`.
        """
        assert isinstance(self.state, DataCubeInspector)  # Make pyright happier

        self.result_qube_components = self.state.get_dsd_qube_components_for_csv(
            self.primary_csv_url
        )

        self.primary_cube_table_identifiers = self.state.get_cube_identifiers_for_csv(
            self.primary_csv_url
        )

        self.primary_csv_column_definitions = (
            self.state.csvw_inspector.get_column_definitions_for_csv(
                self.primary_csv_url
            )
        )
        self.result_column_component_info = self.state.get_column_component_info(
            self.primary_csv_url
        )
        self.result_primary_csv_code_lists = self.state.get_code_lists_and_cols(
            self.primary_csv_url
        )

        (
            canonical_shape_dataset,
            measure_col,
            unit_col,
        ) = transform_dataset_to_canonical_shape(
            self.state,
            self.dataset,
            self.primary_csv_url,
            self.result_qube_components.qube_components,
        )
        self.result_dataset_value_counts = get_dataset_val_counts_info(
            canonical_shape_dataset, measure_col, unit_col
        )

    def generate_codelist_results(self):
        """
        Generates results specific to code lists.

        Member of :class:`./MetadataPrinter`.
        """
        csvw_inspector = self.state.csvw_inspector
        self.result_code_list_cols = csvw_inspector.get_column_definitions_for_csv(
            self.primary_csv_url
        )
        # Retrieving the primary key column names of the code list to identify the unique identifier
        result_table_schema_properties = csvw_inspector.get_table_info_for_csv_url(
            self.primary_csv_url
        )

        primary_key_col_names = result_table_schema_properties.primary_key_col_names

        # Currently, we do not support composite primary keys.
        if len(primary_key_col_names) != 1:
            raise UnsupportedNumOfPrimaryKeyColNamesException(
                num_of_primary_key_col_names=len(primary_key_col_names),
                table_url=self.primary_csv_url,
            )
        (
            parent_col_title,
            label_col_title,
            unique_identifier,
        ) = self.get_parent_label_unique_id_col_titles(
            self.result_code_list_cols, primary_key_col_names[0]
        )
        self.result_concepts_hierachy_info = get_concepts_hierarchy_info(
            self.dataset, parent_col_title, label_col_title, unique_identifier
        )

    @staticmethod
    def _get_formated_output(list_of_info: List[ColumnComponentInfo]) -> str:
        """
        Returns the column component and column definitions informaiton is
        a formatted string output.
        """

        the_list = [
            {
                "Title": x.column_definition.title,
                "Type": x.component_type.name,
                "Required": x.column_definition.required,
                "Property URL": x.column_definition.property_url,
                "Observations Column Title": ""
                if x.component is None
                else ", ".join(
                    [
                        c.title
                        for c in x.component.used_by_observed_value_columns
                        if c.title is not None
                    ]
                ),
            }
            for x in list_of_info
        ]
        formatted = get_printable_tabular_str_from_list(the_list)

        return formatted

    def __post_init__(self):
        self.generate_general_results()
        if self.state.csvw_inspector.csvw_type == CSVWType.QbDataSet:
            self.get_datacube_results()
        elif self.state.csvw_inspector.csvw_type == CSVWType.CodeList:
            self.generate_codelist_results()

    @property
    def type_info_printable(self) -> str:
        """
        Returns a printable of file content type.

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        if self.state.csvw_inspector.csvw_type == CSVWType.QbDataSet:
            return "- This file is a data cube."
        else:
            return "- This file is a code list."

    @property
    def column_component_info_printable(self) -> str:
        """
        Returns a printable of the column titles and types.

        Member of :class:`./MetadataPrinter`.

        """
        return f" - The {self.csvw_type_str} has the following column component information: \n {self._get_formated_output(self.result_column_component_info)}"

    @property
    def catalog_metadata_printable(self) -> str:
        """
        Returns a printable of catalog metadata (e.g. title, description).

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        return f"- The {self.csvw_type_str} has the following catalog metadata:{self.result_catalog_metadata.output_str}"

    @property
    def dsd_info_printable(self) -> str:
        """
        Returns a printable of data structure definition (DSD).

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        primary_csv_suppressed_columns = [
            column_definition.title
            for column_definition in self.primary_csv_column_definitions
            if column_definition.suppress_output and column_definition.title is not None
        ]

        return f"- The {self.csvw_type_str} has the following data structure definition:\n- Dataset Label: {self.result_catalog_metadata.title}{self.result_qube_components.output_str}\n- Columns where suppress output is true: {get_printable_list_str(primary_csv_suppressed_columns)}"

    @property
    def codelist_info_printable(self) -> str:
        """
        Returns a printable of data structure definition (DSD) code list information (e.g. column name, type, etc.).

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """

        def alter_code_list_for_text_representation(code_list: CodelistResult) -> Dict:
            dict_repr = code_list.as_dict()
            dict_repr["code_list_label"] = code_list.code_list_label or ""
            dict_repr["cols_used_in"] = ", ".join(code_list.cols_used_in)
            del dict_repr["csv_url"]
            return dict_repr

        formatted_codelists = get_printable_tabular_str_from_list(
            [
                alter_code_list_for_text_representation(codelist)
                for codelist in sorted(
                    self.result_primary_csv_code_lists.codelists,
                    key=lambda c: c.code_list,
                )
            ],
            column_names=["Code List", "Code List Label", "Columns Used In"],
        )
        output_string = f"""
        - Number of Code Lists: {self.result_primary_csv_code_lists.num_codelists}
        - Code Lists:{linesep}{formatted_codelists}"""

        return f"- The {self.csvw_type_str} has the following code list information:{output_string}"

    @property
    def dataset_observations_info_printable(self) -> str:
        """
        Returns a printable of top 10 and last 10 records.

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        return f"- The {self.csvw_type_str} has the following dataset information:{self.result_dataset_observations_info.output_str}"

    @property
    def dataset_val_counts_by_measure_unit_info_printable(self) -> str:
        """
        Returns a printable of data set value counts broken-down by measure and unit.

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        return f"- The {self.csvw_type_str} has the following value counts:{self.result_dataset_value_counts.output_str}"

    @property
    def codelist_hierachy_info_printable(self) -> str:
        """
        Returns a printable of code list concepts hierarchy.

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        return f"- The {self.csvw_type_str} has the following concepts information:{self.result_concepts_hierachy_info.output_str}"
