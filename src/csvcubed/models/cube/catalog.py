"""
Catalog Metadata (base)
-----------------------
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Union
from abc import ABC, abstractmethod

from csvcubed.models.pydanticmodel import PydanticModel


@dataclass
class CatalogMetadataBase(PydanticModel, ABC):
    title: str

    @abstractmethod
    def get_description(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_issued(self) -> Union[datetime, date, None]:
        pass
