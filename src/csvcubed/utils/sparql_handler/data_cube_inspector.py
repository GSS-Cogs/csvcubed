"""
Data Cube Inspector
-------------------

Provides access to inspect the contents of an rdflib graph containing
one of more data cubes.
"""

from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List, Optional

from csvcubed.models.csvcubedexception import UnsupportedComponentPropertyTypeException
from csvcubed.models.cube.cube_shape import CubeShape
from csvcubed.models.sparqlresults import (
    CodelistsResult,
    ColumnDefinition,
    CubeTableIdentifiers,
    IsPivotedShapeMeasureResult,
    QubeComponentResult,
    QubeComponentsResult,
    UnitResult,
)
from csvcubed.utils.dict import get_from_dict_ensure_exists
from csvcubed.utils.iterables import first, group_by
from csvcubed.utils.qb.components import ComponentPropertyType, EndUserColumnType
from csvcubed.utils.sparql_handler.column_component_info import ColumnComponentInfo
from csvcubed.utils.sparql_handler.csvw_inspector import CsvWInspector
from csvcubed.utils.sparql_handler.sparqlquerymanager import (
    select_csvw_dsd_qube_components,
    select_data_set_dsd_and_csv_url,
    select_dsd_code_list_and_cols,
    select_is_pivoted_shape_for_measures_in_data_set,
    select_units,
)


def _figure_out_end_user_column_type(
    qube_c: QubeComponentResult, cube_shape: CubeShape
) -> EndUserColumnType:
    """This function will decide the columns type for the end user"""

    component_type = ComponentPropertyType(qube_c.property_type)

    if component_type == ComponentPropertyType.Dimension:
        if qube_c.property == "http://purl.org/linked-data/cube#measureType":
            return EndUserColumnType.Measures

        return EndUserColumnType.Dimension
    elif component_type == ComponentPropertyType.Measure:
        if cube_shape == CubeShape.Pivoted:
            return EndUserColumnType.Observations

        return EndUserColumnType.Measures
    elif component_type == ComponentPropertyType.Attribute:
        if (
            qube_c.property
            == "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        ):
            return EndUserColumnType.Units

        return EndUserColumnType.Attribute
    else:
        raise UnsupportedComponentPropertyTypeException(
            property_type=qube_c.property_type
        )


@dataclass
class DataCubeInspector:
    """Provides access to inspect the data cubes contained in an rdflib graph."""

    csvw_inspector: CsvWInspector

    """
    Private cached properties.
    """

    @cached_property
    def _units(self) -> Dict[str, UnitResult]:
        """
        Gets the unit_uri for each UnitResult
        """
        results = select_units(self.csvw_inspector.rdf_graph)
        return {result.unit_uri: result for result in results}

    @cached_property
    def _cube_table_identifiers(self) -> Dict[str, CubeTableIdentifiers]:
        """
        Identifiers linking a given qb:DataSet with a csvw table (identified by the csvw:url).

        Maps from csv_url to the identifiers.
        """
        results = select_data_set_dsd_and_csv_url(self.csvw_inspector.rdf_graph)
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
            self.csvw_inspector.rdf_graph,
            self.csvw_inspector.csvw_json_path,
            map_dsd_uri_to_csv_url,
            self.csvw_inspector.column_definitions,
            self._cube_shapes,
        )

    @cached_property
    def _cube_shapes(self) -> Dict[str, CubeShape]:
        """
        A mapping of csvUrl to the given CubeShape. CSV tables which aren't cubes
         are not present here.
        """

        def _detect_shape_for_cube(
            measures_with_shape: List[IsPivotedShapeMeasureResult],
        ) -> CubeShape:
            """
            Given a metadata validator as input, returns the shape of the cube that
             metadata describes (Pivoted or Standard).
            """
            all_pivoted = True
            all_standard_shape = True
            for measure in measures_with_shape:
                all_pivoted = all_pivoted and measure.is_pivoted_shape
                all_standard_shape = all_standard_shape and not measure.is_pivoted_shape

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

        results = select_is_pivoted_shape_for_measures_in_data_set(
            self.csvw_inspector.rdf_graph, list(self._cube_table_identifiers.values())
        )

        map_csv_url_to_measure_shape = group_by(results, lambda r: r.csv_url)

        return {
            csv_url: _detect_shape_for_cube(measures_with_shape)
            for (csv_url, measures_with_shape) in map_csv_url_to_measure_shape.items()
        }

    @cached_property
    def _codelists_and_cols(self) -> Dict[str, CodelistsResult]:
        """
        Maps the csv url to the code lists/columns featured in the CSV.
        """
        return select_dsd_code_list_and_cols(
            self.csvw_inspector.rdf_graph,
            self.csvw_inspector.csvw_json_path,
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
        Get csv url, data set uri, data set label and DSD uri for the given csv url.
        """
        result: CubeTableIdentifiers = get_from_dict_ensure_exists(
            self._cube_table_identifiers, csv_url
        )
        return result

    def get_cube_identifiers_for_data_set(
        self, data_set_uri: str
    ) -> CubeTableIdentifiers:
        """
        Get csv url, data set uri, data set label and DSD uri for the given data set uri.
        """

        result = first(
            self._cube_table_identifiers.values(),
            lambda i: i.data_set_url == data_set_uri,
        )
        if result is None:
            raise KeyError(f"Could not find the data_set with URI '{data_set_uri}'.")

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

    def get_column_component_info(self, csv_url: str) -> List[ColumnComponentInfo]:
        """
        Get the ColumnComponentInfo which contains the EndUserColumnType
        and the corresponding ColumnDefinition given a csv url
        """

        list_to_return = []
        column_definitions = self.csvw_inspector.get_column_definitions_for_csv(csv_url)
        column_definitions = [x for x in column_definitions if not x.virtual]
        qube_components = self.get_dsd_qube_components_for_csv(csv_url).qube_components
        cube_shape = self.get_shape_for_csv(csv_url)
        # qube_type = [x.property_type for x in qube_type]

        observations_columns = {
            col
            for comp in qube_components
            for col in comp.used_by_observed_value_columns
        }

        def _get_column_type(
            column: ColumnDefinition,
        ) -> EndUserColumnType:
            component_definition = first(
                qube_components, lambda q: column in q.real_columns_used_in
            )

            if component_definition is None:
                if column.suppress_output:
                    return EndUserColumnType.Suppressed
                elif (
                    cube_shape == CubeShape.Standard and column in observations_columns
                ):
                    return EndUserColumnType.Observations
                else:
                    raise KeyError(
                        f"Could not find component associated with CSV column '{column.title}'"
                    )

            return _figure_out_end_user_column_type(component_definition, cube_shape)

        for column in column_definitions:
            # todo: Need to consider suppressed columns
            column_type = _get_column_type(column)
            list_to_return.append(
                ColumnComponentInfo(
                    component_type=column_type,
                    column_definition=column,
                )
            )

        return list_to_return

    def get_columns_for_component_type(
        self,
    ) -> List[ColumnDefinition]:
        pass
