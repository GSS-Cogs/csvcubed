"""
Data Cube Repository
--------------------

Provides access to inspect the contents of an rdflib graph containing
one of more data cubes.
"""

from dataclasses import InitVar, dataclass, field
from functools import cache, cached_property
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import pandas as pd
import uritemplate
from csvcubedmodels.rdf.namespaces import XSD
from pandas.core.arrays.categorical import Categorical

from csvcubed.definitions import QB_MEASURE_TYPE_DIMENSION_URI, SDMX_ATTRIBUTE_UNIT_URI
from csvcubed.inputs import pandas_input_to_columnar_optional_str
from csvcubed.inspect.sparql_handler.code_list_repository import CodeListRepository
from csvcubed.inspect.sparql_handler.csvw_repository import CsvWRepository
from csvcubed.inspect.sparql_handler.sparqlquerymanager import (
    select_csvw_dsd_qube_components,
    select_dataset_dsd_and_csv_url,
    select_dsd_code_list_and_cols,
    select_is_pivoted_shape_data_set,
    select_labels_for_resource_uris,
    select_units,
)
from csvcubed.models.csvcubedexception import UnsupportedComponentPropertyTypeException
from csvcubed.models.cube.cube_shape import CubeShape
from csvcubed.models.cube.qb.components.constants import ACCEPTED_DATATYPE_MAPPING
from csvcubed.models.inspect.column_component_info import ColumnComponentInfo
from csvcubed.models.inspect.sparqlresults import (
    CodelistResult,
    CodelistsResult,
    ColumnDefinition,
    CubeTableIdentifiers,
    IsPivotedShapeResult,
    QubeComponentResult,
    QubeComponentsResult,
    UnitResult,
)
from csvcubed.models.validationerror import ValidationError
from csvcubed.utils.dict import get_from_dict_ensure_exists
from csvcubed.utils.iterables import first, group_by, single
from csvcubed.utils.pandas import read_csv
from csvcubed.utils.qb.components import ComponentPropertyType, EndUserColumnType
from csvcubed.utils.uri import file_uri_to_path

_XSD_BASE_URI: str = XSD[""].toPython()


@dataclass
class DataCubeRepository:
    """Provides access to inspect the data cubes contained in an rdflib graph."""

    csvw_repository: CsvWRepository
    code_list_repository_in: InitVar[Optional[CodeListRepository]] = None
    _code_list_repository: CodeListRepository = field(init=False)

    def __post_init__(self, code_list_repository_in: Optional[CodeListRepository]):
        self._code_list_repository = code_list_repository_in or CodeListRepository(
            self.csvw_repository
        )

    def __hash__(self):
        """
        Necessary for `@cache` attributes above function definitions within this class.

        We *don't* want to make use of the dataclass hashing functionality, since it may end up evaluating all of
        our cached properties which would mean they're no longer lazy-loading.

        The csvw_repository can uniquely identify us by the file we originally loaded.
        """
        return hash(self.csvw_repository)

    """
    Private cached properties.
    """

    @cached_property
    def _units(self) -> Dict[str, UnitResult]:
        """
        Gets the unit_uri for each UnitResult
        """
        results = select_units(self.csvw_repository.rdf_graph)
        return {result.unit_uri: result for result in results}

    @cached_property
    def _cube_table_identifiers(self) -> Dict[str, CubeTableIdentifiers]:
        """
        Identifiers linking a given qb:DataSet with a csvw table (identified by the csvw:url).

        Maps from csv_url to the identifiers.
        """
        results = select_dataset_dsd_and_csv_url(self.csvw_repository.rdf_graph)
        results_dict: Dict[str, CubeTableIdentifiers] = {}
        for result in results:
            results_dict[result.csv_url] = result
        return results_dict

    @cached_property
    def _dsd_qube_components(self) -> Dict[str, QubeComponentsResult]:
        """
        Maps csv_url to the qb:DataStructureDefinition components associated with it.
        """
        map_dsd_uri_to_csv_url = {
            i.dsd_uri: i.csv_url for i in self._cube_table_identifiers.values()
        }

        return select_csvw_dsd_qube_components(
            self.csvw_repository.rdf_graph,
            self.csvw_repository.csvw_json_path,
            map_dsd_uri_to_csv_url,
            self.csvw_repository.column_definitions,
            self._cube_shapes,
        )

    @cached_property
    def _cube_shapes(self) -> Dict[str, CubeShape]:
        """
        A mapping of csvUrl to the given CubeShape. CSV tables which aren't cubes
         are not present here.
        """

        def _detect_shape_for_cube(
            csv_url_with_shape: List[IsPivotedShapeResult],
        ) -> CubeShape:
            """
            Given a metadata validator as input, returns the shape of the cube that
             metadata describes (Pivoted or Standard).
            """
            all_pivoted = True
            all_standard_shape = True
            for csv_url in csv_url_with_shape:
                all_pivoted = all_pivoted and csv_url.is_pivoted_shape
                all_standard_shape = all_standard_shape and not csv_url.is_pivoted_shape

            if all_pivoted:
                return CubeShape.Pivoted
            elif all_standard_shape:
                return CubeShape.Standard
            else:
                raise TypeError(
                    "The input metadata is invalid as the shape of the cube it represents is "
                    "not supported. More specifically, the input contains some observation values "
                    "that are pivoted and some are not pivoted."
                )

        results = select_is_pivoted_shape_data_set(
            self.csvw_repository.rdf_graph, list(self._cube_table_identifiers.values())
        )

        map_csv_url_to_shape = group_by(results, lambda r: r.csv_url)

        return {
            csv_url: _detect_shape_for_cube(csv_url_with_shape)
            for (csv_url, csv_url_with_shape) in map_csv_url_to_shape.items()
        }

    @cached_property
    def _codelists_and_cols(self) -> Dict[str, CodelistsResult]:
        """
        Maps the csv url to the code lists/columns featured in the CSV.
        """
        return select_dsd_code_list_and_cols(
            self.csvw_repository.rdf_graph,
            self.csvw_repository.csvw_json_path,
        )

    """
    Public getters for the cached properties.
    """

    def get_unit_for_uri(self, uri: str) -> Optional[UnitResult]:
        """
        Get a specific unit, by its uri.
        """
        return self._units.get(uri)

    def get_units(self) -> List[UnitResult]:
        """
        Returns all units defined in the graph.
        """
        return list(self._units.values())

    def get_cube_identifiers_for_csv(self, csv_url: str) -> CubeTableIdentifiers:
        """
        Get CSV URL, dataset URI and DSD URI for the given csv url.
        """
        result: CubeTableIdentifiers = get_from_dict_ensure_exists(
            self._cube_table_identifiers, csv_url
        )
        return result

    def get_cube_identifiers_for_dataset(
        self, dataset_uri: str
    ) -> CubeTableIdentifiers:
        """
        Get CSV URL, dataset URI and DSD URI for the given dataset URI.
        """

        result = first(
            self._cube_table_identifiers.values(),
            lambda i: i.dataset_url == dataset_uri,
        )
        if result is None:
            raise KeyError(f"Could not find the dataset with URI '{dataset_uri}'.")

        return result

    def get_dsd_qube_components_for_csv(self, csv_url: str) -> QubeComponentsResult:
        """
        Get DSD Qube Components for the given csv url.
        """
        return get_from_dict_ensure_exists(self._dsd_qube_components, csv_url)

    def get_shape_for_csv(self, csv_url: str) -> CubeShape:
        """
        Get the cube shape.
        """
        return get_from_dict_ensure_exists(self._cube_shapes, csv_url)

    def get_code_lists_and_cols(self, csv_url: str) -> CodelistsResult:
        """
        Get the codelists and columns associated with the given csv url.
        """

        return self._codelists_and_cols.get(csv_url, CodelistsResult([], 0))

    @cache
    def get_column_component_info(self, csv_url: str) -> List[ColumnComponentInfo]:
        """
        Gets a list of columns in the requested CSV file, their types (in the nomenclature of the qube-config.json
          format), and an RDF Data Cube DataStructureDefinition component directly associated with them.

        Columns are defined in the same order as in the CSV file.
        """

        real_columns = [
            c
            for c in self.csvw_repository.get_column_definitions_for_csv(csv_url)
            if not c.virtual
        ]
        qube_components = self.get_dsd_qube_components_for_csv(csv_url).qube_components
        cube_shape = self.get_shape_for_csv(csv_url)

        observations_columns = {
            col
            for comp in qube_components
            for col in comp.used_by_observed_value_columns
        }

        column_component_infos = []
        for column in real_columns:
            (column_type, component) = _get_column_type_and_component(
                column, qube_components, cube_shape, observations_columns
            )
            column_component_infos.append(
                ColumnComponentInfo(
                    column_definition=column,
                    column_type=column_type,
                    component=component,
                )
            )

        return column_component_infos

    def get_columns_of_type(
        self, csv_url: str, column_type: EndUserColumnType
    ) -> List[ColumnDefinition]:
        """
        Gets a list of the columns in a CSV given the requested type (as defined in the qube-config.json format).

        Columns are defined in the same order as in the CSV file.
        """
        return [
            c.column_definition
            for c in self.get_column_component_info(csv_url)
            if c.column_type == column_type
        ]

    def get_measure_uris_and_labels(self, csv_url: str) -> Dict[str, str]:
        """
        Returns a dictionary containing the measure URIs and labels from the input csv's qube components.
        """
        qube_components = self.get_dsd_qube_components_for_csv(csv_url).qube_components

        results_dict = {}
        for component in qube_components:
            if component.property_type == ComponentPropertyType.Measure.value:
                results_dict[component.property] = component.property_label

        return results_dict

    def get_attribute_value_uris_and_labels(
        self, csv_url: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary of the column name mapped to a dictionary of attribute value uris and their labels
        """
        (
            map_col_name_to_title,
            map_resource_attr_col_name_to_value_url,
        ) = self._map_column_name_to_title_to_attribute_value_url(csv_url)

        map_col_name_to_attr_val_uris = self._map_col_name_to_attr_val_uris(
            csv_url, map_col_name_to_title, map_resource_attr_col_name_to_value_url
        )

        return self._map_col_title_to_attr_val_uris_and_labels(
            map_col_name_to_attr_val_uris, map_col_name_to_title
        )

    def get_primary_csv_url(self) -> str:
        """
        Retrieves the csv_url for the primary CSV defined in the CSV-W.
        This will only work if the primary file loaded into the graph was a
        data cube.
        """
        primary_catalog_metadata = self.csvw_repository.get_primary_catalog_metadata()
        return self.get_cube_identifiers_for_dataset(
            primary_catalog_metadata.distribution_uri
        ).csv_url

    def get_dataframe(
        self,
        csv_url: str,
        include_suppressed_cols: bool = True,
        dereference_uris: bool = True,
    ) -> Tuple[pd.DataFrame, List[ValidationError]]:
        """
        Get the pandas dataframe for the csv url of the cube wishing to be loaded.
        Returns DuplicateColumnTitleError in the event of two instances of the
        same columns being defined.
        include_suppressed_cols=True means Suppressed columns will be included in the returned dataframe (not dereferenced to labels)
        dereference_uris=True means URIs of column values are converted to their human readable labels.
        """
        cols = self.get_column_component_info(csv_url)
        dict_of_types = _get_data_types_of_all_cols(cols)
        absolute_csv_url = file_uri_to_path(
            urljoin(self.csvw_repository.csvw_json_path.as_uri(), csv_url)
        )
        (df, _errors) = read_csv(absolute_csv_url, dtype=dict_of_types)
        if dereference_uris:
            code_lists = self.get_code_lists_and_cols(csv_url).codelists
            for col in cols:
                col_values = df[col.column_definition.title].values
                # Exclude suppressed columns from dereferencing as we don't know what component type they are in order to call the correct dereferencing function
                if col.column_type.value != "Suppressed":
                    if isinstance(col_values, Categorical):
                        df[col.column_definition.title] = col_values.rename_categories(
                            self._get_new_category_labels_for_col(
                                csv_url, col, col_values.categories, code_lists
                            )
                        )
        if not include_suppressed_cols:
            cols_to_drop = [
                col.column_definition.title
                for col in cols
                if col.column_type.value == "Suppressed"
            ]
            df = df.drop(cols_to_drop, axis=1)
        return df, _errors

    def _get_new_category_labels_for_col(
        self,
        csv_url: str,
        col: ColumnComponentInfo,
        col_categories: pd.Index,
        code_lists: List[CodelistResult],
    ) -> List[str]:
        """
        Identifies the type of column being used and applies the appropriate dereferencing function.
        """
        value_url = col.column_definition.value_url

        if col.column_type.value == "Attribute" and value_url is not None:
            return self._dereference_uris_for_attributes(
                col, value_url, csv_url, col_categories
            )
        elif col.column_type.value == "Measures" and value_url is not None:
            return self._dereference_uris_for_measures(
                col, value_url, csv_url, col_categories
            )
        elif col.column_type.value == "Units" and value_url is not None:
            return self._dereference_uris_for_units(col, value_url, col_categories)
        elif col.column_type.value == "Dimension":
            return self._dereference_uris_for_dimensions(code_lists, col)
        # Column is either an Attribute Literal or Observations
        raise ValueError(
            f"Unhandled column type/configuration - {col.column_type.value}, {col.column_definition}"
        )

    def _dereference_uris_for_attributes(
        self,
        col: ColumnComponentInfo,
        value_url: str,
        csv_url: str,
        col_categories: pd.Index,
    ) -> List[str]:
        """
        Returns the list of dereferenced URIs for Attribute Resource-type column values.
        """
        if col.column_definition.name is None:
            raise ValueError(f"Column name is not defined - {col.column_definition}")
        if col.column_definition.title is None:
            raise ValueError(f"Column title is not defined - {col.column_definition}")

        col_uris = [
            uritemplate.expand(value_url, {col.column_definition.name: cat})
            for cat in col_categories
        ]
        attribute_vals = self.get_attribute_value_uris_and_labels(csv_url)
        return [attribute_vals[col.column_definition.title][uri] for uri in col_uris]

    def _dereference_uris_for_measures(
        self,
        col: ColumnComponentInfo,
        value_url: str,
        csv_url: str,
        col_categories: pd.Index,
    ) -> List[str]:
        """
        Returns the list of dereferenced URIs for Measures-type column values.
        """
        if col.column_definition.name is None:
            raise ValueError(f"Column name is not defined - {col.column_definition}")

        col_uris = [
            uritemplate.expand(value_url, {col.column_definition.name: cat})
            for cat in col_categories
        ]
        measure_uris_and_labels = self.get_measure_uris_and_labels(csv_url)
        return [measure_uris_and_labels[uri] for uri in col_uris]

    def _dereference_uris_for_units(
        self,
        col: ColumnComponentInfo,
        value_url: str,
        col_categories: pd.Index,
    ) -> List[str]:
        """
        Returns the list of dereferenced URIs for Units-type column values.
        """
        if col.column_definition.name is None:
            raise ValueError(f"Column name is not defined - {col.column_definition}")

        col_uris = [
            uritemplate.expand(value_url, {col.column_definition.name: cat})
            for cat in col_categories
        ]
        unit_labels = []
        for col_uri in col_uris:
            maybe_unit = self.get_unit_for_uri(col_uri)
            if maybe_unit is None:
                raise ValueError(f"Unit {col_uri} could not be retrieved.")
            unit_labels.append(maybe_unit.unit_label)
        return unit_labels

    def _dereference_uris_for_dimensions(
        self, code_lists: List[CodelistResult], col: ColumnComponentInfo
    ) -> List[str]:
        """
        Returns the list of dereferenced URIs for Dimension-type column values.
        """
        if col.column_definition.title is None:
            raise ValueError(f"Column title is not defined - {col.column_definition}")

        code_list = single(
            code_lists, lambda c: col.column_definition.title in c.cols_used_in
        )
        concept_scheme_uri = code_list.code_list
        uri_labels_dict = self._code_list_repository.get_map_code_list_uri_to_label(
            concept_scheme_uri
        )

        return list(uri_labels_dict.values())

    def _map_column_name_to_title_to_attribute_value_url(
        self, csv_url: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Returns dictionaries of column name to column title and resource attribute column name to value url
        """
        column_components = self.get_column_component_info(csv_url)

        map_col_name_to_title = {
            component.column_definition.name: component.column_definition.title
            for component in column_components
            if component.column_definition.name is not None
            and component.column_definition.title is not None
        }

        map_resource_attr_col_name_to_value_url = {
            component.column_definition.name: component.column_definition.value_url
            for component in column_components
            if component.column_type == EndUserColumnType.Attribute
            and component.column_definition.name is not None
            and component.column_definition.value_url is not None
        }

        return (map_col_name_to_title, map_resource_attr_col_name_to_value_url)

    def _map_col_name_to_attr_val_uris(
        self,
        csv_url,
        map_col_name_to_title: Dict[str, str],
        map_resource_attr_col_name_to_value_url: Dict[str, str],
    ) -> Dict[str, List[str]]:
        """
        Returns a dictionary of column name mapped to a list of all attribute value uris for that column
        """
        absolute_csv_url = file_uri_to_path(
            urljoin(self.csvw_repository.csvw_json_path.as_uri(), csv_url)
        )
        (dataframe, _) = read_csv(
            absolute_csv_url,
            usecols=[
                map_col_name_to_title[col_name]
                for col_name in map_resource_attr_col_name_to_value_url.keys()
            ],
            dtype={
                col_name: "string"
                for col_name in map_resource_attr_col_name_to_value_url.keys()
            },
        )
        return {
            name: [
                uritemplate.expand(value_url, {name: av})
                for av in pandas_input_to_columnar_optional_str(
                    dataframe[map_col_name_to_title[name]].unique()
                )
                if av is not None
            ]
            for name, value_url in map_resource_attr_col_name_to_value_url.items()
        }

    def _map_col_title_to_attr_val_uris_and_labels(
        self,
        map_col_name_to_attribute_value_uris: Dict[str, List[str]],
        map_col_name_to_title: Dict[str, str],
    ) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary of the column title mapped to a dictionary of attribute value uris and their labels
        """
        map_uri_to_col_name: Dict[str, str] = {
            uri: col_name
            for col_name, uri_list in map_col_name_to_attribute_value_uris.items()
            for uri in uri_list
        }

        uris_to_query = list(map_uri_to_col_name.keys())

        sparql_results = select_labels_for_resource_uris(
            self.csvw_repository.rdf_graph, uris_to_query
        )

        map_col_title_to_attr_val_uris_and_labels: Dict[str, Dict[str, str]] = {}
        for uri, label in sparql_results.items():
            col_name = map_uri_to_col_name[uri]
            col_title = map_col_name_to_title[col_name]
            results_for_col_title = map_col_title_to_attr_val_uris_and_labels.get(
                col_title, {}
            )
            results_for_col_title[uri] = label
            map_col_title_to_attr_val_uris_and_labels[col_title] = results_for_col_title

        return map_col_title_to_attr_val_uris_and_labels


def _get_column_type_and_component(
    column: ColumnDefinition,
    qube_components: List[QubeComponentResult],
    cube_shape: CubeShape,
    observations_columns: Set[ColumnDefinition],
) -> Tuple[EndUserColumnType, Optional[QubeComponentResult]]:
    """
    We *assume* that all components which claim to be 'used' in a column express the same information about the
    column. i.e. if two or more components claim to be 'used' in the column, it shouldn't matter whether we pick the
    first or the second component, we should draw the same conclusions about the type of the column.
    """
    component_definition = first(
        qube_components, lambda q: column in q.real_columns_used_in
    )

    if component_definition is None:
        if column.suppress_output:
            return EndUserColumnType.Suppressed, None
        elif cube_shape == CubeShape.Standard and column in observations_columns:
            return EndUserColumnType.Observations, None
        else:
            raise KeyError(
                f"Could not find component associated with CSV column '{column.title}'"
            )

    return (
        _figure_out_end_user_column_type(component_definition, cube_shape),
        component_definition,
    )


def _figure_out_end_user_column_type(
    qube_c: QubeComponentResult, cube_shape: CubeShape
) -> EndUserColumnType:
    """This function will decide the columns type for the end user"""

    component_type = ComponentPropertyType(qube_c.property_type)

    if component_type == ComponentPropertyType.Dimension:
        if qube_c.property == QB_MEASURE_TYPE_DIMENSION_URI:
            return EndUserColumnType.Measures

        return EndUserColumnType.Dimension
    elif component_type == ComponentPropertyType.Measure:
        if cube_shape == CubeShape.Pivoted:
            return EndUserColumnType.Observations

        return EndUserColumnType.Measures
    elif component_type == ComponentPropertyType.Attribute:
        if qube_c.property == SDMX_ATTRIBUTE_UNIT_URI:
            return EndUserColumnType.Units

        return EndUserColumnType.Attribute
    else:
        raise UnsupportedComponentPropertyTypeException(
            property_type=qube_c.property_type
        )


def _get_data_types_of_all_cols(cols: List[ColumnComponentInfo]) -> Dict:
    """
    Returns a dictionary containing the column titles and the data type of their
    values. This will be 'str' for most column types except for observations and
    attribute literal columns.
    """
    dict_of_types = {}
    for col in cols:
        is_attribute_literal = (
            col.column_type == EndUserColumnType.Attribute
            and col.column_definition.value_url is None
        )

        if col.column_type == EndUserColumnType.Observations or is_attribute_literal:
            if col.column_definition.data_type is None:
                raise ValueError(
                    f"Expected a defined datatype in column '{col.column_definition.title}' but got 'None' instead."
                )

            col_data_type = col.column_definition.data_type.removeprefix(_XSD_BASE_URI)

            if col_data_type in ACCEPTED_DATATYPE_MAPPING:
                dict_of_types[col.column_definition.title] = ACCEPTED_DATATYPE_MAPPING[
                    col_data_type
                ]
            else:
                raise ValueError(
                    f"Unhandled data type '{col.column_definition.data_type}' in column '{col.column_definition.title}'."
                )
        else:
            dict_of_types[col.column_definition.title] = "category"

    return dict_of_types
