"""
Standardise
-----------

Utilities for standardising cubes and their corresponding data values.
"""
from typing import List, Dict

import pandas as pd
from pandas.core.arrays.categorical import Categorical

from .cube import get_all_units, get_all_measures, get_columns_of_dsd_type
from csvcubed.models.cube import QbCube, QbColumn
from csvcubed.models.cube.qb.components import (
    NewQbMeasure,
    NewQbUnit,
    QbAttribute,
    QbDimension,
    NewQbDimension,
    NewQbCodeList,
    QbMultiMeasureDimension,
    QbMultiUnits,
    QbAttributeLiteral,
    QbObservationValue,
)


_unsigned_integer_data_types = {
    "unsignedLong",
    "unsignedInt",
    "unsignedShort",
    "unsignedByte",
    "nonNegativeInteger",
    "positiveInteger",
}
_signed_integer_data_types = {
    "integer",
    "long",
    "int",
    "short",
    "byte",
    "nonPositiveInteger",
    "negativeInteger",
}


def ensure_qbcube_data_is_categorical(cube: QbCube) -> None:
    """Convert each of the appropriate coumns in a QbCube's dataframe to categorical data. Does the change in-place."""
    if cube.data is None:
        return

    for column in cube.columns:
        is_categorical_column = (
            isinstance(column, QbColumn)
            and isinstance(
                column.structural_definition,
                (QbDimension, QbAttribute, QbMultiMeasureDimension, QbMultiUnits),
            )
            and not isinstance(column.structural_definition, QbAttributeLiteral)
        )

        if is_categorical_column:
            column_data = cube.data[column.csv_column_title]
            assert column_data is not None
            if not isinstance(column_data.values, Categorical):
                cube.data[column.csv_column_title] = column_data.astype("category")


def ensure_int_columns_are_ints(cube: QbCube) -> None:
    """
    Given a :obj:`~csvcubed.models.cube.qb.QbCube`, ensure that any column which claims to contain integer values is
     coerced so that even if values are missing (pandas represents these as NaN), all of the remaining values remain
     as integers.
    """
    if cube.data is None:
        return

    def _coerce_to_int_values_if_int(column_title: str, data_type: str):
        assert cube.data is not None
        try:
            if data_type in _signed_integer_data_types:
                cube.data[column_title] = cube.data[column_title].astype(pd.Int64Dtype())
            elif data_type in _unsigned_integer_data_types:
                cube.data[column_title] = cube.data[column_title].astype(pd.UInt64Dtype())
        except Exception as err:
            raise Exception(f'Column {column_title} failing,csvw  data type was {data_type}, pandas data type was {cube.data[column_title].dtype}') from err

    for obs_val_col in get_columns_of_dsd_type(cube, QbObservationValue):
        _coerce_to_int_values_if_int(
            obs_val_col.csv_column_title,
            obs_val_col.structural_definition.data_type,
        )

    for attribute_literal_col in get_columns_of_dsd_type(cube, QbAttributeLiteral):
        _coerce_to_int_values_if_int(
            attribute_literal_col.csv_column_title,
            attribute_literal_col.structural_definition.data_type,
        )


def convert_data_values_to_uri_safe_values(
    cube: QbCube, raise_missing_value_exceptions: bool = True
) -> None:
    """
    Given a :obj:`~csvcubed.models.cube.qb.QbCube`, **replace** all of the text-values which should be represented by URIs
    in the CSV-W output with the appropriate URIs.

    Also converts all appropriate columns to the pandas categorical format.
    """

    # We want to ensure all appropriate data is represented as categorical before we start replacing category labels.
    ensure_qbcube_data_is_categorical(cube)

    new_units = [u for u in get_all_units(cube) if isinstance(u, NewQbUnit)]
    map_unit_label_to_uri_identifier = {
        u.label: u.uri_safe_identifier for u in new_units
    }
    multi_units_columns_with_new_units = [
        c
        for c in get_columns_of_dsd_type(cube, QbMultiUnits)
        if all([isinstance(u, NewQbUnit) for u in c.structural_definition.units])
    ]
    _overwrite_labels_for_columns(
        cube,
        multi_units_columns_with_new_units,
        map_unit_label_to_uri_identifier,
        raise_missing_value_exceptions,
    )

    new_measures = [m for m in get_all_measures(cube) if isinstance(m, NewQbMeasure)]
    map_measure_label_to_uri_identifier = {
        m.label: m.uri_safe_identifier for m in new_measures
    }
    multi_measure_dimension_columns_defining_new_measures = [
        meas
        for meas in get_columns_of_dsd_type(cube, QbMultiMeasureDimension)
        if all(
            [isinstance(m, NewQbMeasure) for m in meas.structural_definition.measures]
        )
    ]
    _overwrite_labels_for_columns(
        cube,
        multi_measure_dimension_columns_defining_new_measures,
        map_measure_label_to_uri_identifier,
        raise_missing_value_exceptions,
    )

    for dimension_column in get_columns_of_dsd_type(cube, NewQbDimension):
        if isinstance(dimension_column.structural_definition.code_list, NewQbCodeList):
            new_code_list = dimension_column.structural_definition.code_list
            map_dim_val_labels_to_uri_identifiers = dict(
                [
                    (concept.label, concept.uri_safe_identifier)
                    for concept in new_code_list.concepts
                ]
            )

            _overwrite_labels_for_columns(
                cube,
                [dimension_column],
                map_dim_val_labels_to_uri_identifiers,
                raise_missing_value_exceptions,
            )

    for attribute_column in get_columns_of_dsd_type(cube, QbAttribute):
        attribute = attribute_column.structural_definition
        new_attribute_values: List[NewQbAttributeValue] = attribute.new_attribute_values  # type: ignore
        if (
            not isinstance(attribute, QbAttributeLiteral)
            and len(new_attribute_values) > 0
        ):
            map_attr_val_labels_to_uri_identifiers = dict(
                [
                    (new_attribute_value.label, new_attribute_value.uri_safe_identifier)
                    for new_attribute_value in new_attribute_values
                ]
            )

            _overwrite_labels_for_columns(
                cube,
                [attribute_column],
                map_attr_val_labels_to_uri_identifiers,
                raise_missing_value_exceptions,
            )


def _overwrite_labels_for_columns(
    cube: QbCube,
    affected_columns: List[QbColumn],
    map_unit_label_to_new_value: Dict[str, str],
    raise_missing_values_exceptions: bool,
) -> None:
    if cube.data is None:
        return
        
    for column in affected_columns:
        column_data = cube.data[column.csv_column_title]
        assert column_data is not None
        column_values = column_data.values
        assert isinstance(column_values, Categorical)
        new_category_labels: List[str] = []
        for c in column_values.categories:
            c = str(c)
            new_category_label = map_unit_label_to_new_value.get(c)
            if new_category_label is None:
                if raise_missing_values_exceptions:
                    raise ValueError(
                        f"Unable to find new category label for term '{c}' in column '{column.csv_column_title}'."
                    )
                else:
                    # Can't raise exception here, just leave the value as-is.
                    new_category_labels.append(c)
            else:
                new_category_labels.append(new_category_label)

        column_values.categories = new_category_labels
