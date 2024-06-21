"""
Metadata Printer
----------------

Provides functionality for validating and detecting input metadata.json file.
"""

from dataclasses import dataclass, field
from os import linesep
from pathlib import Path
from textwrap import indent
from typing import Dict, List, Optional, Tuple, Union

from pandas import DataFrame

from csvcubed.inspect.inspectdatasetmanager import (
    get_concepts_hierarchy_info,
    get_dataset_observations_info,
    get_dataset_val_counts_info,
    load_csv_to_dataframe,
)
from csvcubed.inspect.sparql_handler.code_list_repository import CodeListRepository
from csvcubed.inspect.sparql_handler.csvw_repository import CsvWRepository
from csvcubed.inspect.sparql_handler.data_cube_repository import DataCubeRepository
from csvcubed.models.csvcubedexception import (
    InputNotSupportedException,
    UnsupportedNumOfPrimaryKeyColNamesException,
)
from csvcubed.models.csvwtype import CSVWType
from csvcubed.models.inspect.column_component_info import ColumnComponentInfo
from csvcubed.models.inspect.inspectdataframeresults import (
    CodelistHierarchyInfoResult,
    DatasetObservationsByMeasureUnitInfoResult,
    DatasetObservationsInfoResult,
)
from csvcubed.models.inspect.sparqlresults import (
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


@dataclass
class MetadataPrinter:
    """
    This class produces the printables necessary for producing outputs to the CLI.
    """

    state: Union[DataCubeRepository, CodeListRepository]

    csvw_type_str: str = field(init=False)
    primary_csv_url: str = field(init=False)
    dataset: DataFrame = field(init=False)
    result_build_minor_version: int = field(init=False)
    result_catalog_metadata: CatalogMetadataResult = field(init=False)
    result_column_component_infos: List[ColumnComponentInfo] = field(init=False)
    primary_cube_table_identifiers: CubeTableIdentifiers = field(init=False)
    primary_csv_column_definitions: List[ColumnDefinition] = field(init=False)
    result_primary_csv_code_lists: CodelistsResult = field(init=False)
    result_dataset_observations_info: DatasetObservationsInfoResult = field(init=False)
    result_dataset_value_counts: DatasetObservationsByMeasureUnitInfoResult = field(
        init=False
    )
    result_code_list_cols: List[ColumnDefinition] = field(init=False)
    result_concepts_hierachy_info: CodelistHierarchyInfoResult = field(init=False)

    def __post_init__(self):
        self.generate_general_results()
        if self.state.csvw_repository.csvw_type == CSVWType.QbDataSet:
            self.get_datacube_results()
        elif self.state.csvw_repository.csvw_type == CSVWType.CodeList:
            self.generate_codelist_results()

    @staticmethod
    def get_csvw_type_str(csvw_type: CSVWType) -> str:
        """
        Returns the type of csvw being evaluated as a string.
        E.g. 'data cube' or 'code list'.
        """
        if csvw_type == CSVWType.QbDataSet:
            return "data cube"
        elif csvw_type == CSVWType.CodeList:
            return "code list"
        else:
            raise InputNotSupportedException()

    def get_build_minor_version(self) -> int:
        """Return the minor version of csvcubed used to build the cube."""
        # TODO Create a class to store csvcubed version information similar to readers/cubeconfig/schema_versions.py
        build_info = self.state.csvw_repository.get_build_information()[0]
        csvcubed_version = build_info.github_url.split("/")[-1]
        csvcubed_version_parts = csvcubed_version.split(".")
        csvcubed_minor_version = int(csvcubed_version_parts[1])
        return csvcubed_minor_version

    def get_primary_csv_url(self) -> str:
        """Return the csv_url for the primary table in the graph."""
        primary_metadata = self.state.csvw_repository.get_primary_catalog_metadata()
        if isinstance(self.state, DataCubeRepository):
            # Get csv_url based on whether cube identifiers are recorded against the dataset or the distribution
            if self.result_build_minor_version >= 5:
                return self.state.get_cube_identifiers_for_dataset(
                    primary_metadata.distribution_uri
                ).csv_url
            else:
                return self.state.get_cube_identifiers_for_dataset(
                    primary_metadata.dataset_uri
                ).csv_url
        elif isinstance(self.state, CodeListRepository):
            return self.state.get_table_identifiers_for_concept_scheme(
                primary_metadata.dataset_uri
            ).csv_url
        else:
            raise InputNotSupportedException()

    @staticmethod
    def get_parent_label_unique_id_col_titles(
        columns: List[ColumnDefinition], primary_key_col: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Returns a tuple containing the parent, label and unique id column titles
        in a code list.
        """
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
        csvw_repository = self.state.csvw_repository
        csvw_type = csvw_repository.csvw_type

        self.csvw_type_str = self.get_csvw_type_str(csvw_type)
        self.result_catalog_metadata = csvw_repository.get_primary_catalog_metadata()
        if isinstance(self.state, DataCubeRepository):
            self.result_build_minor_version = self.get_build_minor_version()
        self.primary_csv_url = self.get_primary_csv_url()
        self.dataset = load_csv_to_dataframe(
            csvw_repository.csvw_json_path, Path(self.primary_csv_url)
        )
        self.result_dataset_observations_info = get_dataset_observations_info(
            self.dataset,
            csvw_type,
            (
                self.state.get_shape_for_csv(self.primary_csv_url)
                if isinstance(self.state, DataCubeRepository)
                else None
            ),
        )

    def get_datacube_results(self):
        """
        Generates results specific to data cubes.

        Member of :class:`./MetadataPrinter`.
        """
        assert isinstance(self.state, DataCubeRepository)  # Make pyright happier

        self.primary_cube_table_identifiers = self.state.get_cube_identifiers_for_csv(
            self.primary_csv_url
        )

        self.primary_csv_column_definitions = (
            self.state.csvw_repository.get_column_definitions_for_csv(
                self.primary_csv_url
            )
        )
        self.result_column_component_infos = self.state.get_column_component_info(
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
            self.state.get_dsd_qube_components_for_csv(
                self.primary_csv_url
            ).qube_components,
        )
        self.result_dataset_value_counts = get_dataset_val_counts_info(
            canonical_shape_dataset, measure_col, unit_col
        )

    def generate_codelist_results(self):
        """
        Generates results specific to code lists.

        Member of :class:`./MetadataPrinter`.
        """
        csvw_repository = self.state.csvw_repository
        self.result_code_list_cols = csvw_repository.get_column_definitions_for_csv(
            self.primary_csv_url
        )
        # Retrieving the primary key column names of the code list to identify the unique identifier
        result_table_schema_properties = csvw_repository.get_table_info_for_csv_url(
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
    def _get_column_component_info_for_output(
        column_component_infos: List[ColumnComponentInfo],
    ) -> List[Dict[str, Union[str, bool, None]]]:
        """
        Returns the column component and column definitions information ready for outputting into a table.
        """

        return [
            {
                "Title": c.column_definition.title,
                "Type": c.column_type.name,
                "Required": c.column_definition.required,
                "Property URL": c.column_definition.property_url,
                "Observations Column Titles": (
                    ""
                    if c.component is None
                    else ", ".join(
                        [
                            c.title
                            for c in c.component.used_by_observed_value_columns
                            if c.title is not None
                        ]
                    )
                ),
            }
            for c in column_component_infos
        ]

    @property
    def type_info_printable(self) -> str:
        """
        Returns a printable of file content type.

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        if self.state.csvw_repository.csvw_type == CSVWType.QbDataSet:
            return "- This file is a data cube."
        else:
            return "- This file is a code list."

    @property
    def column_component_info_printable(self) -> str:
        """
        Returns a printable of the column titles and types.

        Member of :class:`./MetadataPrinter`.

        """
        primary_csv_suppressed_columns = [
            column_definition.title
            for column_definition in self.primary_csv_column_definitions
            if column_definition.suppress_output and column_definition.title is not None
        ]
        formatted_column_info = get_printable_tabular_str_from_list(
            self._get_column_component_info_for_output(
                self.result_column_component_infos
            )
        )
        return (
            f" - The {self.csvw_type_str} has the following column component information: \n"
            + indent(
                f"- Dataset Label: {self.result_catalog_metadata.label}\n"
                + f"- Columns: \n{formatted_column_info}\n"
                + f"- Columns where suppress output is true: {get_printable_list_str(primary_csv_suppressed_columns)}",
                prefix="    ",
            )
        )

    @property
    def catalog_metadata_printable(self) -> str:
        """
        Returns a printable of catalog metadata (e.g. title, description).

        Member of :class:`./MetadataPrinter`.

        :return: `str` - user-friendly string which will be output to CLI.
        """
        formatted_landing_pages: str = get_printable_list_str(
            self.result_catalog_metadata.landing_pages
        )
        formatted_themes: str = get_printable_list_str(
            self.result_catalog_metadata.themes
        )
        formatted_keywords: str = get_printable_list_str(
            self.result_catalog_metadata.keywords
        )
        formatted_description: str = self.result_catalog_metadata.description.replace(
            linesep, f"{linesep}\t\t"
        )
        return f"""
        - The {self.csvw_type_str} has the following catalog metadata:
          - Title: {self.result_catalog_metadata.title}
          - Label: {self.result_catalog_metadata.label}
          - Issued: {self.result_catalog_metadata.issued}
          - Modified: {self.result_catalog_metadata.modified}
          - License: {self.result_catalog_metadata.license}
          - Creator: {self.result_catalog_metadata.creator}
          - Publisher: {self.result_catalog_metadata.publisher}
          - Landing Pages: {formatted_landing_pages}
          - Themes: {formatted_themes}
          - Keywords: {formatted_keywords}
          - Contact Point: {self.result_catalog_metadata.contact_point}
          - Identifier: {self.result_catalog_metadata.identifier}
          - Comment: {self.result_catalog_metadata.comment}
          - Description: {formatted_description}
        """

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
