from typing import Optional, List
import pandas as pd
from abc import ABC


from .datastructuredefinition import MultiQbDataStructureDefinition, QbDataStructureDefinition
from .measure import QbMeasure, QbMeasureTypeDimension
from .unit import QbUnit
from csvqb.models.validationerror import ValidationError


class QbObservationValue(MultiQbDataStructureDefinition, ABC):

    def __init__(self, data_type: Optional[str]):
        self.data_type: str = data_type if data_type is not None else "number"


class QbMultiMeasureObservationValue(QbObservationValue):
    def __init__(self, data_type: Optional[str] = None):
        QbObservationValue.__init__(self, data_type)

    def __str__(self) -> str:
        return f"QbMultiMeasureObservationValue('{self.data_type}')"

    def validate(self) -> List[ValidationError]:
        return []  # TODO: implement this

    def validate_data(self, data: pd.Series) -> List[ValidationError]:
        return []  # TODO: implement this

    def get_qb_components(self) -> List[QbDataStructureDefinition]:
        return []


class QbSingleMeasureObservationValue(QbObservationValue):
    """
        Represents the unit/measure/datatype components necessary to define a simple qb:Observation.

        N.B. Requires `virt_unit` and `virt_measure` columns to be added to CSV-W metadata
    """

    def __init__(self,
                 measure: QbMeasure,
                 unit: QbUnit,
                 data_type: Optional[str] = None):
        QbObservationValue.__init__(self, data_type)
        self.measure: QbMeasure = measure
        self.unit: QbUnit = unit

    def __str__(self) -> str:
        return f"QbMultiMeasureObservationValue({self.measure}, {self.unit})"

    def validate(self) -> List[ValidationError]:
        return []  # TODO: implement this

    def validate_data(self, data: pd.Series) -> List[ValidationError]:
        return []  # TODO: implement this

    def get_qb_components(self) -> List[QbDataStructureDefinition]:
        return [self.measure, QbMeasureTypeDimension, self.unit]
