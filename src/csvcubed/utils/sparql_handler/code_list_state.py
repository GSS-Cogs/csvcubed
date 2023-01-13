from dataclasses import dataclass
from functools import cached_property
from itertools import groupby
from pathlib import Path
from typing import Any, Dict, List

import rdflib

from csvcubed.models.sparqlresults import CatalogMetadataResult
from csvcubed.utils.iterables import group_by
from csvcubed.utils.sparql_handler.csvw_state import CsvWState
from csvcubed.utils.sparql_handler.sparqlquerymanager import (
    select_csvw_catalog_metadata,
)


@dataclass
class CodeListState:
    csvw_state: CsvWState

    def get_csvw_catalog_metadata(self, csv_url: str) -> CatalogMetadataResult:
        """
        todo: Access the stuff from `self.csvw_state.catalog_metadata` and return the relevant value.

        When in code_list_state, need a way to link between csv_url and concept scheme (this needs a new query).
        Filter catalog metadata results so they represent the one associated with the csv_url. (dataset url = concept scheme url)
        """
        pass
