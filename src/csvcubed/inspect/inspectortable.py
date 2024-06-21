"""
Inspector Tables
----------------

Enables access to browse the contents of a data cube table and a
code list table, as well as their metadata. Also contains the base
Inspector class.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, OrderedDict, Union

import uritemplate

from csvcubed.inspect.inspectorcolumns import (
    AttributeColumn,
    DataCubeColumn,
    DimensionColumn,
    MeasuresColumn,
    PivotedObservationsColumn,
    StandardShapeObservationsColumn,
    SuppressedColumn,
    UnitsColumn,
)
from csvcubed.inspect.inspectors import MetadataInspector, TableInspector
from csvcubed.inspect.lazyfuncdescriptor import lazy_func_field
from csvcubed.inspect.sparql_handler.code_list_repository import CodeListRepository
from csvcubed.inspect.sparql_handler.csvw_repository import CsvWRepository
from csvcubed.inspect.sparql_handler.data_cube_repository import DataCubeRepository
from csvcubed.inspect.tableschema import CsvWRdfManager
from csvcubed.models.cube.cube_shape import CubeShape
from csvcubed.models.inspect.column_component_info import ColumnComponentInfo
from csvcubed.models.inspect.sparqlresults import CatalogMetadataResult
from csvcubed.utils.iterables import single
from csvcubed.utils.qb.components import EndUserColumnType


@dataclass(frozen=True)
class DataCubeTable(MetadataInspector, TableInspector):
    """
    Represents a DataCubeTable object inspector which allows access to the cube's shape,
    the data set URI, and a dictionary of columns.
    """

    def _get_shape(self) -> CubeShape:
        return self.data_cube_repository.get_shape_for_csv(self.csv_url)

    def _get_dataset_uri(self) -> str:
        return self.data_cube_repository.get_cube_identifiers_for_csv(
            self.csv_url
        ).dataset_url

    def _get_columns(self) -> OrderedDict[str, DataCubeColumn]:
        columns = OrderedDict[str, DataCubeColumn]()
        for c in self.data_cube_repository.get_column_component_info(self.csv_url):
            if c.column_definition.title is not None:
                columns[c.column_definition.title] = _map_to_data_cube_column(self, c)

        return columns

    shape: CubeShape = lazy_func_field(_get_shape)
    data_set_uri: str = lazy_func_field(_get_dataset_uri)
    columns: OrderedDict[str, DataCubeColumn] = lazy_func_field(
        _get_columns, repr=False
    )

    def __hash__(self):
        return hash(self.csv_url)

    def _get_metadata(self) -> CatalogMetadataResult:
        data_set_url = self._get_dataset_uri()
        return single(
            self.data_cube_repository.csvw_repository.catalog_metadata,
            lambda c: c.dataset_uri == data_set_url,
        )


@dataclass(frozen=True)
class CodeListTable(MetadataInspector, TableInspector):
    """
    Represents a CodeListTable object inspector, containing the concept scheme URI.
    """

    def _get_concept_scheme_uri(self) -> str:
        return single(
            self.code_list_repository._code_list_table_identifiers,
            lambda i: i.csv_url == self.csv_url,
        ).concept_scheme_url

    concept_scheme_uri: str = lazy_func_field(_get_concept_scheme_uri)

    def __hash__(self):
        return hash(self.csv_url)

    def _get_metadata(self) -> CatalogMetadataResult:
        return self.code_list_repository.get_catalog_metadata_for_concept_scheme(
            self._get_concept_scheme_uri()
        )


def _map_to_data_cube_column(
    table_inspector: TableInspector, info: ColumnComponentInfo
) -> DataCubeColumn:
    if info.column_type == EndUserColumnType.Dimension:
        return DimensionColumn(
            data_cube_repository=table_inspector.data_cube_repository,
            code_list_repository=table_inspector.code_list_repository,
            info=info,
        )
    elif info.column_type == EndUserColumnType.Attribute:
        return AttributeColumn(
            data_cube_repository=table_inspector.data_cube_repository,
            code_list_repository=table_inspector.code_list_repository,
            info=info,
        )
    elif info.column_type == EndUserColumnType.Units:
        return UnitsColumn(
            data_cube_repository=table_inspector.data_cube_repository,
            code_list_repository=table_inspector.code_list_repository,
            info=info,
        )
    elif info.column_type == EndUserColumnType.Measures:
        return MeasuresColumn(
            data_cube_repository=table_inspector.data_cube_repository,
            code_list_repository=table_inspector.code_list_repository,
            info=info,
        )
    elif info.column_type == EndUserColumnType.Observations:
        if info.column_definition.property_url is not None and any(
            uritemplate.variables(info.column_definition.property_url)
        ):
            return StandardShapeObservationsColumn(
                data_cube_repository=table_inspector.data_cube_repository,
                code_list_repository=table_inspector.code_list_repository,
                info=info,
            )
        else:
            return PivotedObservationsColumn(
                data_cube_repository=table_inspector.data_cube_repository,
                code_list_repository=table_inspector.code_list_repository,
                info=info,
            )
    elif info.column_type == EndUserColumnType.Suppressed:
        return SuppressedColumn(
            data_cube_repository=table_inspector.data_cube_repository,
            code_list_repository=table_inspector.code_list_repository,
            info=info,
        )
    raise ValueError(
        f"Unmatched column type {info.column_type} with column title {info.column_definition.title}"
    )


@dataclass
class Inspector:
    """
    The main Inspector object that allows access to the CSVW, data cube, and code list repositorys,
    along with the associated tables.
    """

    primary_csvw: Union[str, Path]
    _csvw_repository: CsvWRepository = field(init=False, repr=False)
    _data_cube_repository: DataCubeRepository = field(init=False, repr=False)
    _code_list_repository: CodeListRepository = field(init=False, repr=False)

    def _get_tables(self) -> List[TableInspector]:
        cube_tables = [
            DataCubeTable(
                csv_url=t.csv_url,
                data_cube_repository=self._data_cube_repository,
                code_list_repository=self._code_list_repository,
            )
            for t in self._data_cube_repository._cube_table_identifiers.values()
        ]
        code_list_tables = [
            CodeListTable(
                csv_url=t.csv_url,
                data_cube_repository=self._data_cube_repository,
                code_list_repository=self._code_list_repository,
            )
            for t in self._code_list_repository._code_list_table_identifiers
        ]

        return [*cube_tables, *code_list_tables]

    tables: List[TableInspector] = lazy_func_field(_get_tables)

    def __post_init__(self):
        csvw_path = (
            self.primary_csvw
            if isinstance(self.primary_csvw, Path)
            else Path(self.primary_csvw)
        )
        csvw_rdf_manager = CsvWRdfManager(csvw_path.expanduser())
        self._csvw_repository = csvw_rdf_manager.csvw_repository
        self._data_cube_repository = DataCubeRepository(self._csvw_repository)
        self._code_list_repository = CodeListRepository(self._csvw_repository)
