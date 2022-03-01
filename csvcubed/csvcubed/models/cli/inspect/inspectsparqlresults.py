"""
Inspect SPARQL query results
----------------------------
"""

from os import linesep
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from csvcubed.utils.qb.components import get_printable_component_property
from rdflib import URIRef

from rdflib.query import ResultRow

from csvcubed.utils.sparql import none_or_map
from csvcubed.utils.printable import get_printable_list_str, get_printable_tabular_str


@dataclass()
class CatalogMetadataSparqlResult:
    """
    Model to represent result of the `select_csvw_catalog_metadata` sparql query.
    """

    sparql_result: ResultRow

    @property
    def output_str(self) -> str:
        formatted_landing_pages = get_printable_list_str(self.landing_pages)
        formatted_themes = get_printable_list_str(self.themes)
        formatted_keywords = get_printable_list_str(self.keywords)
        return f"{linesep}\t- Title: {self.title}{linesep}\t- Label: {self.label}{linesep}\t- Issued: {self.issued}{linesep}\t- Modified: {self.modified}{linesep}\t- License: {self.license}{linesep}\t- Creator: {self.creator}{linesep}\t- Publisher: {self.publisher}{linesep}\t- Landing Pages: {formatted_landing_pages}{linesep}\t- Themes: {formatted_themes}{linesep}\t- Keywords: {formatted_keywords}{linesep}\t- Contact Point: {self.contact_point}{linesep}\t- Identifier: {self.identifier}{linesep}\t- Comment: {self.comment}{linesep}\t- Description: {self.description}"

    def __post_init__(self):
        result_dict = self.sparql_result.asdict()

        self.title: str = result_dict["title"]
        self.label: str = result_dict["label"]
        self.issued: str = result_dict["issued"]
        self.modified: str = result_dict["modified"]
        self.license: str = none_or_map(result_dict.get("license"), str)
        self.creator: str = none_or_map(result_dict.get("creator"), str)
        self.publisher: str = none_or_map(result_dict.get("publisher"), str)
        self.landing_pages: list[str] = str(result_dict["landingPages"]).split("|")
        self.themes: list[str] = str(result_dict["themes"]).split("|")
        self.keywords: list[str] = str(result_dict["keywords"]).split("|")
        self.contact_point: str = none_or_map(result_dict.get("contact_point"), str)
        self.identifier: str = result_dict["identifier"]
        self.comment: str = none_or_map(result_dict.get("comment"), str)
        self.description: str = str(
            none_or_map(result_dict.get("description"), str)
        ).replace(linesep, f"{linesep}\t\t")


@dataclass()
class DSDLabelURISparqlResult:
    """
    Model to represent result of the `select_csvw_dsd_dataset_label_and_dsd_def_uri` sparql query.
    """

    sparql_result: ResultRow

    @property
    def output_str(self) -> str:
        return f"{linesep}\t- Dataset Label: {self.dataset_label}"

    def __post_init__(self):
        result_dict = self.sparql_result.asdict()

        self.dataset_label: str = result_dict["dataSetLabel"]
        self.dsd_uri: URIRef = result_dict["dataStructureDefinition"]


@dataclass()
class QubeComponent:
    """
    Model to represent the result of an individual component.
    """

    component_result: ResultRow
    csvw_metadata_json_path: Path

    def to_dict(self) -> Dict:
        return {
            "Property": self.property,
            "Property Label": self.property_label,
            "Property Type": self.property_type,
            "Column Title": self.csv_col_title,
            "Required": self.required,
        }

    def __post_init__(self):
        self.property = get_printable_component_property(
            self.csvw_metadata_json_path, self.component_result["componentProperty"]
        )
        self.property_label = (
            none_or_map(self.component_result.get("componentPropertyLabel"), str) or ""
        )
        self.property_type = (
            none_or_map(self.component_result.get("componentPropertyType"), str) or ""
        )
        self.csv_col_title = (
            none_or_map(self.component_result.get("csvColumnTitle"), str) or ""
        )
        self.required = none_or_map(self.component_result.get("required"), str)


@dataclass()
class QubeComponentsSparqlResult:
    """
    Model to represent result of the `select_csvw_dsd_qube_components` sparql query.
    """

    sparql_results: List[ResultRow]
    csvw_metadata_json_path: Path

    @property
    def output_str(self) -> str:
        formatted_components = get_printable_tabular_str(
            [component.to_dict() for component in self.qube_components]
        )
        return f"{linesep}\t- Number of Components: {self.num_components}{linesep}\t- Components:{linesep}{formatted_components}"

    def __post_init__(self):
        self.qube_components: List[QubeComponent] = list(
            map(
                lambda result: QubeComponent(result, self.csvw_metadata_json_path),
                self.sparql_results,
            )
        )
        self.num_components: int = len(self.qube_components)


@dataclass()
class ColsWithSupressOutputTrueSparlqlResult:
    """
    Model to represent result of the `select_cols_where_supress_output_is_true` sparql query.
    """

    sparql_results: List[ResultRow]

    @property
    def output_str(self) -> str:
        return f"{linesep}- Columns where suppress output is true: {get_printable_list_str(self.columns)}"

    def __post_init__(self):
        self.columns = list(
            map(
                lambda result: str(result["csvColumnTitle"]),
                self.sparql_results,
            )
        )
