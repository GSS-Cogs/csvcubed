"""
Catalog Metadata (DCAT)
-----------------------
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Union

from csvcubedmodels.rdf import dcat

from csvcubed.models.cube.catalog import CatalogMetadataBase
from csvcubed.models.uriidentifiable import UriIdentifiable
from csvcubed.models.validatedmodel import ValidatedModel, ValidationFunction
from csvcubed.models.validationerror import ValidateModelPropertiesError
from csvcubed.utils import validations as v
from csvcubed.utils.validations import (
    validate_list,
    validate_optional,
    validate_str_type,
    validate_uri,
)
from csvcubed.utils.validators.uri import validate_uri as pydantic_validate_uri
from csvcubed.utils.validators.uri import (
    validate_uris_in_list as pydantic_validate_uris_in_list,
)

_logger = logging.getLogger(__name__)


@dataclass
class CatalogMetadata(CatalogMetadataBase, UriIdentifiable):
    identifier: Optional[str] = None
    summary: Optional[str] = field(default=None, repr=False)
    description: Optional[str] = field(default=None, repr=False)
    creator_uri: Optional[str] = field(default=None, repr=False)
    publisher_uri: Optional[str] = field(default=None, repr=False)
    landing_page_uris: list[str] = field(default_factory=list, repr=False)
    theme_uris: list[str] = field(default_factory=list, repr=False)
    keywords: list[str] = field(default_factory=list, repr=False)
    dataset_issued: Union[datetime, date, None] = field(default=None, repr=False)
    dataset_modified: Union[datetime, date, None] = field(default=None, repr=False)
    license_uri: Optional[str] = field(default=None, repr=False)
    public_contact_point_uri: Optional[str] = field(default=None, repr=False)
    uri_safe_identifier_override: Optional[str] = field(default=None, repr=False)
    # spatial_bound_uri: Optional[str] = field(default=None, repr=False)
    # temporal_bound_uri: Optional[str] = field(default=None, repr=False)

    _creator_uri_validator = pydantic_validate_uri("creator_uri", is_optional=True)
    _publisher_uri_validator = pydantic_validate_uri("publisher_uri", is_optional=True)
    _landing_page_uris_validator = pydantic_validate_uris_in_list(
        "landing_page_uris", is_optional=True
    )
    _license_uri_validator = pydantic_validate_uri("license_uri", is_optional=True)
    # _spatial_bound_uri_validator = validate_uri("spatial_bound_uri", is_optional=True)
    # _temporal_bound_uri_validator = validate_uri("temporal_bound_uri", is_optional=True)
    _public_contact_point_uri_validator = pydantic_validate_uri(
        "public_contact_point_uri", is_optional=True
    )

    def _get_validations(self) -> Dict[str, ValidationFunction]:
        return {
            "title": validate_str_type,
            "identifier": validate_optional(validate_str_type),
            "summary": validate_optional(validate_str_type),
            "description": validate_optional(validate_str_type),
            "creator_uri": validate_optional(validate_uri),
            "publisher_uri": validate_optional(validate_uri),
            "landing_page_uris": validate_list(validate_uri),
            "theme_uris": validate_list(validate_uri),
            "keywords": validate_list(validate_str_type),
            "dataset_issued": validate_optional(
                v.any_of(v.is_instance_of(date), v.is_instance_of(datetime))
            ),
            "dataset_modified": validate_optional(
                v.any_of(v.is_instance_of(date), v.is_instance_of(datetime))
            ),
            "license_uri": validate_optional(validate_uri),
            "public_contact_point_uri": validate_optional(validate_uri),
            **UriIdentifiable._get_validations(self),
        }

    def to_json_file(self, file_path: Path) -> None:
        with open(file_path, "w+") as f:
            json.dump(self.as_json_dict(), f, indent=4)

    @classmethod
    def from_json_file(cls, file_path: Path) -> "CatalogMetadata":
        with open(file_path, "r") as f:
            dict_structure = json.load(f)

        return cls.from_dict(dict_structure)

    def get_issued(self) -> Union[datetime, date, None]:
        return self.dataset_issued

    def get_description(self) -> Optional[str]:
        return self.description

    def get_identifier(self) -> str:
        return self.identifier or self.title

    def configure_dcat_dataset(self, dataset: dcat.Dataset) -> None:
        dt_now = datetime.now()
        dt_issued = _convert_date_to_date_time(self.dataset_issued or dt_now)

        dataset.label = dataset.title = self.title
        dataset.issued = dt_issued
        dataset.modified = _convert_date_to_date_time(
            self.dataset_modified or dt_issued
        )
        dataset.comment = self.summary
        dataset.description = self.description
        dataset.license = self.license_uri
        dataset.creator = self.creator_uri
        dataset.publisher = self.publisher_uri
        dataset.landing_page = set(self.landing_page_uris)
        dataset.themes = set(self.theme_uris)
        dataset.keywords = set(self.keywords)
        dataset.contact_point = self.public_contact_point_uri
        dataset.identifier = self.get_identifier()


def _convert_date_to_date_time(dt: Union[datetime, date]) -> datetime:
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime.combine(dt, time.min)

    return dt
