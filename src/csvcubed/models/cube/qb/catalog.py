"""
Catalog Metadata (DCAT)
-----------------------
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, Optional, Union

from csvcubedmodels.rdf import dcat

from csvcubed.models.cube.catalog import CatalogMetadataBase
from csvcubed.models.uriidentifiable import UriIdentifiable
from csvcubed.models.validatedmodel import ValidationFunction
from csvcubed.utils import validations as v


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

    def _get_validations(self) -> Dict[str, ValidationFunction]:
        return {
            **CatalogMetadataBase._get_validations(self),
            "identifier": v.optional(v.string),
            "summary": v.optional(v.string),
            "description": v.optional(v.string),
            "creator_uri": v.optional(v.uri),
            "publisher_uri": v.optional(v.uri),
            "landing_page_uris": v.list(v.uri),
            "theme_uris": v.list(v.uri),
            "keywords": v.list(v.string),
            "dataset_issued": v.optional(
                v.any_of(v.is_instance_of(date), v.is_instance_of(datetime))
            ),
            "dataset_modified": v.optional(
                v.any_of(v.is_instance_of(date), v.is_instance_of(datetime))
            ),
            "license_uri": v.optional(v.uri),
            "public_contact_point_uri": v.optional(v.uri),
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

    def configure_dcat_distribution(self, distribution: dcat.Distribution) -> None:
        dt_now = datetime.now()
        dt_issued = _convert_date_to_date_time(self.dataset_issued or dt_now)
        distribution.issued = dt_issued
        distribution.label = distribution.title = self.title
        distribution.identifier = self.get_identifier()
        distribution.creator = self.creator_uri

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
