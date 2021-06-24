from typing import Optional, List
from abc import ABC

import pandas as pd

from csvqb.utils.uri import uri_safe
from .datastructuredefinition import ColumnarQbDataStructureDefinition
from csvqb.models.cube.qb.components.codelist import QbCodeList, ExistingQbCodeList, NewQbCodeList, NewQbConcept
from csvqb.models.validationerror import ValidationError


class QbDimension(ColumnarQbDataStructureDefinition, ABC):

    def __init__(self, code_list: Optional[QbCodeList]):
        self.code_list: Optional[QbCodeList] = code_list

    def validate(self) -> List[ValidationError]:
        if self.code_list is not None:
            return self.code_list.validate()

        return []

    def validate_data(self, data: pd.Series) -> List[ValidationError]:
        if self.code_list is not None:
            return self.code_list.validate_data(data)

        return []


class ExistingQbDimension(QbDimension):

    def __init__(self,
                 dimension_uri: str,
                 code_list: Optional[ExistingQbCodeList] = None,
                 range_uri: Optional[str] = None):
        QbDimension.__init__(self, code_list)
        self.dimension_uri: str = dimension_uri
        self.range_uri: Optional[str] = range_uri

    def __str__(self) -> str:
        return f"ExistingQbDimension('{self.dimension_uri}')"

    def validate(self) -> List[ValidationError]:
        return QbDimension.validate(self)  # TODO: add more validation checks

    def validate_data(self, data: pd.Series) -> List[ValidationError]:
        return QbDimension.validate_data(self, data)  # TODO: add more validation checks


class NewQbDimension(QbDimension):

    def __init__(self,
                 label: str,
                 description: Optional[str] = None,
                 uri_safe_identifier: Optional[str] = None,
                 code_list: Optional[QbCodeList] = None,
                 parent_dimension_uri: Optional[str] = None,
                 source_uri: Optional[str] = None):
        QbDimension.__init__(self, code_list)
        self.label: str = label
        self.description: Optional[str] = description
        self.uri_safe_identifier: str = uri_safe_identifier if uri_safe_identifier is not None else uri_safe(label)
        self.parent_dimension_uri: Optional[str] = parent_dimension_uri
        self.source_uri: Optional[str] = source_uri

    def __str__(self) -> str:
        return f"NewQbDimension('{self.label}')"

    @staticmethod
    def from_data(label: str,
                  data: pd.Series,
                  description: Optional[str] = None,
                  uri_safe_identifier: Optional[str] = None,
                  parent_dimension_uri: Optional[str] = None,
                  source_uri: Optional[str] = None) -> "NewQbDimension":
        """
            Creates a new dimension and code list from the columnar data provided.
        :param label:
        :param data:
        :param description:
        :param uri_safe_identifier:
        :param parent_dimension_uri:
        :param source_uri:
        :return: NewQbDimension
        """
        return NewQbDimension(label,
                              description=description,
                              uri_safe_identifier=uri_safe_identifier,
                              code_list=NewQbCodeList.from_data(label, data),
                              parent_dimension_uri=parent_dimension_uri,
                              source_uri=source_uri)

    def validate(self) -> List[ValidationError]:
        return QbDimension.validate(self)  # TODO: add more validation checks

    def validate_data(self, data: pd.Series) -> List[ValidationError]:
        return QbDimension.validate_data(self, data)  # TODO: add more validation checks
