"""
Cube
----
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set, TypeVar, Generic, Iterable, Tuple

import pandas as pd
import uritemplate

from csvcubed.definitions import URI_TEMPLATE_SPECIAL_PROPERTIES
from csvcubed.models.cube.columns import CsvColumn
from csvcubed.models.cube.qb.columns import QbColumn
from csvcubed.models.cube.catalog import CatalogMetadataBase
from csvcubed.models.cube.validationerrors import (
    DuplicateColumnTitleError,
    ColumnNotFoundInDataError,
    MissingColumnDefinitionError,
    ColumnValidationError,
    UriTemplateNameError,
)
from csvcubed.models.pydanticmodel import PydanticModel
from csvcubed.models.validationerror import (
    ValidationError,
)
from csvcubed.utils.log import log_exception
from csvcubed.utils.uri import (
    csvw_column_name_safe,
)
from .uristyle import URIStyle

_logger = logging.getLogger(__name__)

TMetadata = TypeVar("TMetadata", bound=CatalogMetadataBase, covariant=True)


@dataclass
class Cube(Generic[TMetadata], PydanticModel):
    metadata: TMetadata
    data: Optional[pd.DataFrame] = field(default=None, repr=False)
    columns: List[CsvColumn] = field(default_factory=lambda: [], repr=False)
    uri_style: URIStyle = URIStyle.Standard
    

    def validate(self) -> List[ValidationError]:
        errors: List[ValidationError] = []
        try:
            errors += self.pydantic_validation()
            errors += self._validate_columns()
        except Exception as e:
            log_exception(_logger, e)
            errors.append(ValidationError(str(e)))
            errors.append(
                ValidationError("An error occurred and validation Failed to Complete")
            )

        return errors

    @staticmethod
    def _get_validation_error_for_exception_in_col(
        csv_column_title: str, error: Exception
    ) -> ColumnValidationError:
        log_exception(_logger, error)
        return ColumnValidationError(csv_column_title, error)

    def _validate_columns(self) -> List[ValidationError]:
        errors: List[ValidationError] = []
        existing_col_titles: Set[str] = set()
        for col in self.columns:
            try:
                if col.csv_column_title in existing_col_titles:
                    errors.append(DuplicateColumnTitleError(col.csv_column_title))
                else:
                    existing_col_titles.add(col.csv_column_title)

                maybe_column_data = None
                if self.data is not None:
                    if col.csv_column_title in self.data.columns:
                        maybe_column_data = self.data[col.csv_column_title]
                    else:
                        errors.append(ColumnNotFoundInDataError(col.csv_column_title))

                if maybe_column_data is not None:
                    errors += col.validate_data(maybe_column_data)
            except Exception as e:
                errors.append(
                    self._get_validation_error_for_exception_in_col(
                        col.csv_column_title, e
                    )
                )

        if self.data is not None:
            defined_column_titles = [c.csv_column_title for c in self.columns]
            for column in list(self.data.columns):
                try:
                    column = str(column)
                    if column not in defined_column_titles:
                        errors.append(MissingColumnDefinitionError(column))
                except Exception as e:
                    errors.append(
                        self._get_validation_error_for_exception_in_col(column, e)
                    )

        # Check for uri template naming errors
        safe_column_names = [
            csvw_column_name_safe(c.uri_safe_identifier) for c in self.columns
        ]
        for uri_template, names in self._csv_column_uri_templates_to_names():
            defined_names = safe_column_names + URI_TEMPLATE_SPECIAL_PROPERTIES
            for name in names:
                if name not in defined_names:
                    _logger.debug('Unable to find name %s in %s', name, safe_column_names)
                    errors.append(UriTemplateNameError(safe_column_names, uri_template))

        return errors


    def _csv_column_uri_templates_to_names(self) -> Iterable[Tuple]:
        """
        Generates tuples of any configured and not None csv column
        uri templates within the cube, along with the column name
        specified within it.

        Example:
        A cube containing just the following csv column uri templates

        "http://example.com/dimensions/{+foo}"
        "http://example.com/dimensions/{bar}#things"

        yields:
        - "http://example.com/dimensions/{+foo}": "foo",
        then
        - "http://example.com/dimensions/{bar}#things": "bar"
        """

        csv_column_uri_templates = [
            c.csv_column_uri_template for c in self.columns if isinstance(c, QbColumn)
        ]

        template_to_name_map = {
            c: uritemplate.variables(c)
            for c in csv_column_uri_templates if c
        }

        return template_to_name_map.items()
