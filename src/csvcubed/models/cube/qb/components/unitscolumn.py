"""
Units Column
------------

Define a units column in an RDF Data Cube.
"""

from dataclasses import dataclass
from typing import List

import pandas as pd
import uritemplate
from pydantic import validator

from csvcubed.inputs import PandasDataTypes, pandas_input_to_columnar_str
from csvcubed.utils.qb.validation.uri_safe import ensure_no_uri_safe_conflicts
from .datastructuredefinition import QbColumnStructuralDefinition
from .unit import (
    QbUnit,
    NewQbUnit,
    ExistingQbUnit,
)
from .validationerrors import UndefinedUnitUrisError, EmptyQbMultiUnitsError
from csvcubed.models.validationerror import ValidationError


@dataclass
class QbMultiUnits(QbColumnStructuralDefinition):
    """
    Represents multiple units used/defined in a cube, typically used in multi-measure cubes.
    """

    units: List[QbUnit]

    @validator("units")
    def _validate_units_non_conflicting(cls, units: List[QbUnit]) -> List[QbUnit]:
        """
        Ensure that there are no collisions where multiple new units map to the same URI-safe value.
        """
        ensure_no_uri_safe_conflicts(
            [
                (unit.label, unit.uri_safe_identifier)
                for unit in units
                if isinstance(unit, NewQbUnit)
            ],
            QbMultiUnits,
        )

        return units

    @staticmethod
    def new_units_from_data(data: PandasDataTypes) -> "QbMultiUnits":
        """
        Automatically generates new units from a units column.
        """
        return QbMultiUnits(
            [NewQbUnit(label=u) for u in set(pandas_input_to_columnar_str(data))]
        )

    @staticmethod
    def existing_units_from_data(
        data: PandasDataTypes, csvw_column_name: str, csv_column_uri_template: str
    ) -> "QbMultiUnits":
        columnar_data = pandas_input_to_columnar_str(data)
        return QbMultiUnits(
            [
                ExistingQbUnit(
                    uritemplate.expand(csv_column_uri_template, {csvw_column_name: m})
                )
                for m in sorted(set(columnar_data))
            ]
        )

    def validate_data(
        self,
        data: pd.Series,
        csvw_column_name: str,
        csv_column_uri_template: str,
        column_csv_title: str,
    ) -> List[ValidationError]:
        if len(self.units) == 0:
            return [EmptyQbMultiUnitsError()]
        else:
            unique_values = set(data.unique())

            map_label_to_new_uri_value = {}
            for u in self.units:
                if isinstance(u, NewQbUnit):
                    map_label_to_new_uri_value.update({u.label: u.uri_safe_identifier})

            if map_label_to_new_uri_value:
                unique_values = {
                    map_label_to_new_uri_value.get(v, v) for v in unique_values
                }

            unique_expanded_uris = {
                uritemplate.expand(csv_column_uri_template, {csvw_column_name: s})
                for s in unique_values
            }
            expected_uris = set()
            for unit in self.units:
                if isinstance(unit, ExistingQbUnit):
                    expected_uris.add(unit.unit_uri)
                elif isinstance(unit, NewQbUnit):
                    expected_uris.add(
                        uritemplate.expand(
                            csv_column_uri_template,
                            {csvw_column_name: unit.uri_safe_identifier},
                        )
                    )
                else:
                    raise Exception(f"Unhandled unit type {type(unit)}")

            undefined_uris = unique_expanded_uris - expected_uris
            if any(undefined_uris):
                return [UndefinedUnitUrisError(self, undefined_uris)]

        return []
