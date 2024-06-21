"""
SPARQL query results
----------------------------
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import uritemplate
from csvcubedmodels.dataclassbase import DataClassBase
from rdflib.query import ResultRow

from csvcubed.definitions import QB_MEASURE_TYPE_DIMENSION_URI
from csvcubed.inspect.sparql_handler.sparql import none_or_map
from csvcubed.models.cube.cube_shape import CubeShape
from csvcubed.utils.iterables import first, group_by, single
from csvcubed.utils.qb.components import (
    ComponentPropertyType,
    get_component_property_as_relative_path,
    get_component_property_type,
)

_logger = logging.getLogger(__name__)


@dataclass
class CatalogMetadataResult:
    """
    Model to represent select catalog metadata sparql query result.
    """

    dataset_uri: str
    """`dataset` here doesn't necessarily mean the dcat:DataSet. It means either the dcat:DataSet or the skos:ConceptScheme (which is also a dcat:Dataset)."""
    graph_uri: str
    """URI representing the graph in which the Catalog Metadata was found."""
    distribution_uri: str
    """URI of the qb:Dataset/dcat:Distribution"""
    title: str
    label: str
    issued: str
    modified: str
    license: str
    creator: str
    publisher: str
    landing_pages: list[str]
    themes: list[str]
    keywords: list[str]
    contact_point: str
    identifier: str
    comment: str
    description: str
    was_generated_by: str


@dataclass
class CubeTableIdentifiers(DataClassBase):
    """
    Links the CSV URL, qb:Dataset URL, and DataStructureDefinition URI for a given cube.
    """

    csv_url: str
    dataset_url: str
    dsd_uri: str


@dataclass
class CodelistResult(DataClassBase):
    """
    Model to represent a codelist.
    """

    code_list: str
    code_list_label: Optional[str]
    cols_used_in: List[str]
    csv_url: str


@dataclass
class CSVWTableSchemaFileDependenciesResult:
    """
    Model to represent select csvw table schema file dependencies result.
    """

    table_schema_file_dependencies: List[str]


@dataclass
class CodelistsResult:
    """
    Model to represent select codelists sparql query result.
    """

    codelists: List[CodelistResult]
    num_codelists: int


@dataclass
class CodeListTableIdentifers:
    """
    Table identifiers to support mapping between csv_url and concept_scheme_url
    """

    csv_url: str
    concept_scheme_url: str


@dataclass(unsafe_hash=True)
class UnitResult:
    """
    Model to represent select single unit from dsd.
    """

    unit_uri: str
    unit_label: str


@dataclass
class PrimaryKeyColNameByDatasetUrlResult:
    """
    Model to represent select primary key column name by table url.
    """

    value: str


@dataclass
class MetadataDependenciesResult:
    """
    Model representing a metadata dependency which should be loaded to make sense of the current graph.
    """

    data_set: str
    data_dump: str
    uri_space: str


@dataclass
class TableSchemaPropertiesResult:
    """
    Model representing the about_url, csv_url and a list of primary key column names.
    """

    about_url: str
    csv_url: str
    primary_key_col_names: List[str]


@dataclass
class IsPivotedShapeResult:
    """
    A dataclass that is used to return whether a cube is in pivoted or standard shape.
    """

    csv_url: str
    is_pivoted_shape: bool


@dataclass(unsafe_hash=True)
class ColumnDefinition:
    """
    Model representing the Column Titles and Column Names of a data set.

    See https://www.w3.org/TR/2015/REC-tabular-data-model-20151217/#dfn-column for the full list of properties a CSV-W
    column can have.

    N.B. This does not contain all possible CSV-W column properties, just the ones currently used by csvcubed.
    """

    csv_url: str
    """CSV that this column is defined against."""
    about_url: Optional[str]
    data_type: Optional[str]
    name: Optional[str]
    property_url: Optional[str]
    required: bool
    suppress_output: bool
    title: Optional[str]
    """This should technically be a list according to the W3C spec."""
    value_url: Optional[str]
    virtual: bool


@dataclass
class QubeComponentResult(DataClassBase):
    """
    Model to represent a qube component.
    """

    component: str
    dsd_uri: str
    property: str
    property_label: Optional[str]
    property_type: str
    real_columns_used_in: List[ColumnDefinition]
    """The CSV columns this component is used in."""
    used_by_observed_value_columns: List[ColumnDefinition]
    """The Observed Value CSV Columns this component describes."""
    required: bool


@dataclass
class QubeComponentsResult:
    """
    Model to represent select qube components sparql query result.
    """

    qube_components: List[QubeComponentResult]
    num_components: int


@dataclass
class ResourceURILabelResult:
    """
    Model to represent a resource attribute's URI and label.
    """

    resource_uri: str
    resource_label: str


@dataclass
class CsvcubedVersionResult:
    dataset_url: str
    build_activity: str
    github_url: str


def map_catalog_metadata_results(
    sparql_results: List[ResultRow],
) -> List[CatalogMetadataResult]:
    """
    Maps the sparql query results to a list of `CatalogMetadataResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `List[CatalogMetadataResult]`
    """
    results: List[CatalogMetadataResult] = []
    for row in sparql_results:
        result_dict = row.asdict()

        result = CatalogMetadataResult(
            graph_uri=str(result_dict["graph"]),
            dataset_uri=str(result_dict["dataset"]),
            title=str(result_dict["title"]),
            label=str(result_dict["label"]),
            issued=str(result_dict["issued"]),
            modified=str(result_dict["modified"]),
            distribution_uri=none_or_map(result_dict.get("distribution"), str)
            or "None",
            comment=none_or_map(result_dict.get("comment"), str) or "None",
            description=none_or_map(result_dict.get("description"), str) or "None",
            license=none_or_map(result_dict.get("license"), str) or "None",
            creator=none_or_map(result_dict.get("creator"), str) or "None",
            publisher=none_or_map(result_dict.get("publisher"), str) or "None",
            landing_pages=str(result_dict["landingPages"]).split("|"),
            themes=str(result_dict["themes"]).split("|"),
            keywords=str(result_dict["keywords"]).split("|"),
            contact_point=none_or_map(result_dict.get("contactPoint"), str) or "None",
            identifier=none_or_map(result_dict.get("identifier"), str) or "None",
            was_generated_by=none_or_map(result_dict.get("buildActivity"), str)
            or "None",
        )
        results.append(result)

    return results


def map_data_set_dsd_csv_url_result(
    sparql_results: List[ResultRow],
) -> List[CubeTableIdentifiers]:
    """
    Maps the SPARQL results of `select_data_set_dsd_csv_url.sparql` into `CubeTableIdentifiers`.
    """

    def map_row(row_result: Dict[str, Any]) -> CubeTableIdentifiers:
        return CubeTableIdentifiers(
            csv_url=str(row_result["csvUrl"]),
            dataset_url=str(row_result["dataSet"]),
            dsd_uri=str(row_result["dsd"]),
        )

    return [map_row(row.asdict()) for row in sparql_results]


def _map_qube_component_sparql_result(
    sparql_result: ResultRow, json_path: Path
) -> QubeComponentResult:
    """
    Maps sparql query result to `QubeComponentResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `QubeComponentResult`
    """
    result_dict = sparql_result.asdict()
    _logger.debug("result_dict: %s", result_dict)

    result = QubeComponentResult(
        component=str(result_dict["component"]),
        dsd_uri=str(result_dict["dsdUri"]),
        property=get_component_property_as_relative_path(
            json_path, str(result_dict["componentProperty"])
        ),
        property_label=(
            none_or_map(result_dict.get("componentPropertyLabel"), str) or ""
        ),
        property_type=get_component_property_type(
            str(result_dict["componentPropertyType"])
        ),
        required=none_or_map(result_dict.get("required"), bool) or False,
        # The following two properties are populated later using the results from the CSV-W columns query.
        real_columns_used_in=[],
        used_by_observed_value_columns=[],
    )
    return result


def map_qube_components_sparql_result(
    sparql_results_dsd_components: List[ResultRow],
    json_path: Path,
    map_dsd_uri_to_csv_url: Dict[str, str],
    map_csv_url_to_column_definitions: Dict[str, List[ColumnDefinition]],
    map_csv_url_to_cube_shape: Dict[str, CubeShape],
) -> Dict[str, QubeComponentsResult]:
    """
    Returns a map of csv_url to `QubeComponentsResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `Dict[str, QubeComponentsResult]`
    """
    components: List[QubeComponentResult] = [
        _map_qube_component_sparql_result(r, json_path)
        for r in sparql_results_dsd_components
    ]

    map_dsd_uri_to_components = group_by(components, lambda c: c.dsd_uri)

    for dsd_uri, components in map_dsd_uri_to_components.items():
        csv_url = map_dsd_uri_to_csv_url[dsd_uri]
        cube_shape = map_csv_url_to_cube_shape[csv_url]
        csv_column_definitions = map_csv_url_to_column_definitions[csv_url]

        measure_uris = {
            c.property
            for c in components
            if c.property_type == str(ComponentPropertyType.Measure.value)
        }

        observed_value_columns = [
            c
            for c in csv_column_definitions
            if (not c.virtual) and c.property_url in measure_uris
        ]

        for component in components:
            _set_columns_on_component(
                component, cube_shape, csv_column_definitions, observed_value_columns
            )
            component.required = component.required or any(
                c.required for c in component.real_columns_used_in
            )

    return {
        map_dsd_uri_to_csv_url[dsd_uri]: QubeComponentsResult(
            qube_components=components, num_components=len(components)
        )
        for (dsd_uri, components) in map_dsd_uri_to_components.items()
    }


def _set_columns_on_component(
    component: QubeComponentResult,
    cube_shape: CubeShape,
    csv_column_definitions: List[ColumnDefinition],
    observed_value_columns: List[ColumnDefinition],
) -> None:
    if (
        cube_shape == CubeShape.Standard
        and component.property_type == ComponentPropertyType.Measure.value
    ):
        measure_column = first(
            csv_column_definitions,
            lambda c: c.property_url == QB_MEASURE_TYPE_DIMENSION_URI,
        )

        if measure_column is None:
            raise KeyError("Could not find standard shape measure column.")

        component.real_columns_used_in = [measure_column]

        obs_val_column = single(
            csv_column_definitions,
            lambda c: c.property_url is not None
            and c.data_type is not None
            and measure_column is not None  # Here to satisfy buggy pyright.
            # We *assume* that a column with a property_url template containing
            # the measure column is the observed value column in the standard
            # shape.
            and measure_column.name in uritemplate.variables(c.property_url),
            "standard shape observations column",
        )

        component.used_by_observed_value_columns = [obs_val_column]
    else:
        all_columns_used_in = [
            c for c in csv_column_definitions if c.property_url == component.property
        ]

        component.real_columns_used_in = [
            c for c in all_columns_used_in if (not c.virtual)
        ]

        columns_using_this_component_about_urls = {
            c.about_url for c in all_columns_used_in
        }

        component.used_by_observed_value_columns = [
            c
            for c in observed_value_columns
            if c.about_url in columns_using_this_component_about_urls
        ]


def _map_codelist_sparql_result(
    sparql_result: ResultRow, json_path: Path
) -> CodelistResult:
    """
    Maps sparql query result to `CodelistResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `CodelistResult`
    """
    result_dict = sparql_result.asdict()

    result = CodelistResult(
        code_list=get_component_property_as_relative_path(
            json_path, str(result_dict["codeList"])
        ),
        code_list_label=none_or_map(result_dict.get("codeListLabel"), str),
        cols_used_in=str(result_dict["csvColumnsUsedIn"]).split("|"),
        csv_url=str(result_dict["csvUrl"]),
    )
    return result


def map_codelists_sparql_result(
    sparql_results: List[ResultRow],
    json_path: Path,
) -> Dict[str, CodelistsResult]:
    """
    Maps sparql query result to `CodelistsModel`

    Member of :file:`./models/sparqlresults.py`

    :return: `Dict[str, CodelistsResult]`
    """
    codelists = map(
        lambda result: _map_codelist_sparql_result(result, json_path),
        sparql_results,
    )

    map_csv_url_to_codelists = group_by(codelists, lambda c: c.csv_url)
    return {
        csv_url: CodelistsResult(codelists=code_lists, num_codelists=len(code_lists))
        for (csv_url, code_lists) in map_csv_url_to_codelists.items()
    }


def map_csvw_table_schemas_file_dependencies_result(
    sparql_results: List[ResultRow],
) -> CSVWTableSchemaFileDependenciesResult:
    """
    Maps sparql query result to `CSVWTableSchemaFileDependenciesResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `CSVWTableSchemaFileDependenciesResult`
    """
    results = CSVWTableSchemaFileDependenciesResult(
        table_schema_file_dependencies=[
            str(sparql_result["tableSchema"]) for sparql_result in sparql_results
        ],
    )
    return results


def map_units(sparql_results: List[ResultRow]) -> List[UnitResult]:
    """
    Maps sparql query result to `UnitResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `UnitResult`
    """

    def map_row(row_result: Dict[str, Any]) -> UnitResult:
        return UnitResult(
            unit_uri=str(row_result["unit"]), unit_label=str(row_result["unitLabel"])
        )

    return [map_row(row.asdict()) for row in sparql_results]


def _map_primary_key_col_name_by_csv_url_result(
    sparql_result: ResultRow,
) -> PrimaryKeyColNameByDatasetUrlResult:
    """
    Maps sparql query result to `PrimaryKeyColNameByDatasetUrlResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `PrimaryKeyColNameByDatasetUrlResult`
    """
    result_dict = sparql_result.asdict()

    result = PrimaryKeyColNameByDatasetUrlResult(
        value=str(result_dict["tablePrimaryKey"]),
    )
    return result


def map_primary_key_col_names_by_csv_url_result(
    sparql_results: List[ResultRow],
) -> List[PrimaryKeyColNameByDatasetUrlResult]:
    """
    Maps sparql query result to `PrimaryKeyColNamesByDatasetUrlResult`

    Member of :file:`./models/sparqlresults.py`

    :return: `PrimaryKeyColNamesByDatasetUrlResult`
    """
    return list(
        map(
            lambda result: _map_primary_key_col_name_by_csv_url_result(result),
            sparql_results,
        )
    )


def map_metadata_dependency_results(
    sparql_results: List[ResultRow],
) -> List[MetadataDependenciesResult]:
    def map_row(row_result: Dict[str, Any]) -> MetadataDependenciesResult:
        return MetadataDependenciesResult(
            data_set=str(row_result["dataset"]),
            data_dump=str(row_result["dataDump"]),
            uri_space=str(row_result["uriSpace"]),
        )

    return [map_row(row.asdict()) for row in sparql_results]


def map_table_schema_properties_results(
    sparql_results: List[ResultRow],
) -> List[TableSchemaPropertiesResult]:
    """
    Maps sparql query result to `List[TableSchemaPropertiesResult]`

    Member of :file:`./models/sparqlresults.py`

    :return: `List[TableSchemaPropertiesResult]`
    """

    def map_row(row_result: Dict[str, Any]) -> TableSchemaPropertiesResult:
        return TableSchemaPropertiesResult(
            about_url=str(row_result["tableAboutUrl"]),
            csv_url=str(row_result["csvUrl"]),
            primary_key_col_names=str(row_result["tablePrimaryKeys"]).split("|"),
        )

    return [map_row(row.asdict()) for row in sparql_results]


def map_is_pivoted_shape_data_set(
    sparql_results: List[ResultRow],
) -> List[IsPivotedShapeResult]:
    """
    Maps the sparql query result to objects of type IsPivotedShapeResult that are then returned.
    """

    def map_row(row_result: Dict[str, Any]) -> IsPivotedShapeResult:
        return IsPivotedShapeResult(
            csv_url=str(row_result["csvUrl"]),
            is_pivoted_shape=bool(row_result["isPivotedShape"]),
        )

    return [map_row(row.asdict()) for row in sparql_results]


def map_labels_for_resource_uris(
    sparql_results: List[ResultRow],
) -> Dict[str, str]:
    """
    Maps resource value uris to labels
    """
    results: Dict[str, str] = {}
    for row in sparql_results:
        if str(row["resourceValUri"]) in results:
            raise KeyError("Duplicate URIs or multiple labels for URI in CSV-W")
        else:
            results[str(row["resourceValUri"])] = str(row["resourceLabel"])
    return results


def map_column_definition_results(
    sparql_results: List[ResultRow],
) -> List[ColumnDefinition]:
    """
    Maps SPARQL query results to 'ColumnDefinition's.
    """

    def map_row(row_result: Dict[str, Any]) -> ColumnDefinition:
        return ColumnDefinition(
            csv_url=str(row_result["csvUrl"]),
            about_url=none_or_map(row_result.get("aboutUrl"), str),
            data_type=none_or_map(row_result.get("dataType"), str),
            name=none_or_map(row_result.get("name"), str),
            property_url=none_or_map(row_result.get("propertyUrl"), str),
            required=bool(row_result["required"]),
            suppress_output=bool(row_result["suppressOutput"]),
            title=none_or_map(row_result.get("title"), str),
            value_url=none_or_map(row_result.get("valueUrl"), str),
            virtual=bool(row_result.get("virtual")),
        )

    return [map_row(row.asdict()) for row in sparql_results]


def map_build_activity_results(
    sparql_results: List[ResultRow],
) -> List[CsvcubedVersionResult]:
    """
    Map SPARQL query results to `CsvcubedVersionResult`s
    """
    results: List[CsvcubedVersionResult] = []
    for row in sparql_results:
        result_dict = row.asdict()

        result = CsvcubedVersionResult(
            dataset_url=str(result_dict["dataset"]),
            build_activity=str(result_dict["buildActivity"]),
            github_url=str(result_dict["csvcubedVersion"]),
        )
        results.append(result)
    return results
