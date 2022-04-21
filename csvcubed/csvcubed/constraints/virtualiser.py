from __future__ import annotations  # allows type hinting of return self

import copy
import json
from pathlib import Path
from typing import Optional, Tuple

from rdflib import Graph
from rdflib.plugins.sparql.processor import SPARQLResult
import pandas as pd

from columns import ColumnRefList
import utils

from pyparsing import ParseException

# Maximum number of rows (of a single column/series) we want in memory at a given time
MAXIMUM_ROW_SUBSET = 2000


def _confirm_remote_resource_exists(url: str):
    """Helper to confirm a claimed url for a csv source exists"""
    raise NotImplementedError


def _confirm_local_resource_exists(path: str):
    """Helper to confirm a specified path for a csv source exists"""
    if not Path(path).exists():
        raise FileNotFoundError(f"{path} does not exist")


# NOTE: This is performance crititcal component, use light and clever hands
# if you change anything here please.
class Virtualiser:
    """
    A class that provides key functionality from a csv+csvw to provide reusable
    methods and an "rdf like" ability to validate a data source via integrity
    constraints.

    One key thing to note is we need to do without ever reading the full dataframe
    into memory or converting the file fully to rdf, as otherwise any
    dependent functions can trigger resource exhaustion (oom) upon dealing
    with larger data sources
    """

    def __init__(self, csvw_source: Path):

        with open(csvw_source) as f:
            csvw_as_dict = json.load(f)
        self.csvw_as_dict: dict = csvw_as_dict

        # TODO: neater, or from elsewhere
        csv_name: str = self.csvw_as_dict["tables"][0]["url"]
        path_to_csv_dir = "/".join(str(csvw_source.absolute()).split("/")[:-1])
        self.csv_path = Path(path_to_csv_dir, csv_name)

        # caching
        self.row_count = None
        self.start_end_indicies = None
        self.unique_column_value_cache = {}
        self.column_reference = ColumnRefList(self.csvw_as_dict)

        # TODO: MUCH neater
        if str(self.csv_path.absolute()).startswith("http://") or str(
            self.csv_path.absolute()
        ).startswith("https://"):
            _confirm_remote_resource_exists(self.csv_path)
        else:
            _confirm_local_resource_exists(self.csv_path)
            self.metadata_graph: Graph = Graph().parse(
                Path(csvw_source), format="json-ld"
            )

    def query_metadata_graph(self, query_str: str) -> SPARQLResult:
        """
        Run a sparql query against the simple metadata graph
        """
        try:
            result: SPARQLResult = self.metadata_graph.query(query_str)
        except ParseException as err:
            raise ParseException(f"Failed to parse query {query_str}") from err

        return result

    def _subset_index_yieder(self) -> Tuple[int, int]:
        """
        Given a csv of unknown length of rows, yields appropriate
        start:end rows for reading a dataframe or series taken from that
        csv as an appropriately performant slice of rows.

        i.e don't allow reading in a 3 million rows at once, we'll
        regret that.
        """

        # only calculate this once per csv
        if not self.row_count:
            self.row_count = utils.get_csv_length(self.csv_path)

        # only calculate this once per csv
        if not self.start_end_indicies:
            self.start_end_indicies = []
            i = 1
            last_row = 0

            while True:
                if i * MAXIMUM_ROW_SUBSET > self.row_count:
                    start_end_index = (last_row, self.row_count + 1)
                    self.start_end_indicies.append(start_end_index)
                    break
                else:
                    start_end_index = (last_row, i * MAXIMUM_ROW_SUBSET)
                    self.start_end_indicies.append(start_end_index)
                    last_row = i * MAXIMUM_ROW_SUBSET
                    i += 1

        # TODO: probably unnessary/OTT, needs some thought.
        # copy as a precuation ony, I'm concerned about mutabilty
        # if we're sourcing multiple genrators against the same list,
        # remove if/once it's been given some thought.
        subset_yielder = copy.deepcopy(self.start_end_indicies)
        for start_end_index in subset_yielder:
            yield start_end_index[0], start_end_index[1]

    def _column_subset_yielder(self, column_label: str) -> pd.DataFrame:
        """
        Generator that returns a sinele column dataframe representing a
        finite subset of the complete dataframe equal to a maximum
        rowcount of MAXIMUM_ROW_SUBSET
        """

        first_iteration = True

        for start, end in self._subset_index_yieder():
            # Keep track of the headers from the first iteraton and reuse them
            # (names) for later dataframe slices that don't have a header row
            if first_iteration:
                one_col_df: pd.DataFrame = pd.read_csv(
                    self.csv_path, usecols=[column_label], skiprows=start, nrows=end
                )
                headers = one_col_df.columns.values
                first_iteration = False
            else:
                one_col_df: pd.DataFrame = pd.read_csv(
                    self.csv_path,
                    names=headers,
                    usecols=[column_label],
                    skiprows=start,
                    nrows=end,
                )

            one_col_df.fillna("", inplace=True)
            yield one_col_df

    def _column_value_yielder(self, column_label: str) -> str:
        """
        A generator that yields every value sequentially from a single
        column of the source csv.

        Where feasible, you should always seek to use ._unique_column_value_yielder
        in preference for preformance reasons.
        """

        for one_col_df in self._column_subset_yielder(column_label):
            for cell_value in one_col_df[column_label]:
                yield cell_value

    def _unique_column_value_yielder(self, column_label: str) -> str:
        """
        A generator that yields one value taken from a single csv column
        """

        # If we've done this before, use the cached values
        if column_label in self.unique_column_value_cache:
            for cell_value in self.unique_column_value_cache[column_label]:
                yield cell_value

        else:
            yielded = []

            one_col_df: pd.DataFrame
            for one_col_df in self._column_subset_yielder(column_label):

                # new values
                values_we_havnt_returned = [
                    x for x in one_col_df[column_label].unique() if x not in yielded
                ]
                if not any(values_we_havnt_returned):
                    continue

                for cell_value in values_we_havnt_returned:
                    yielded.append(cell_value)
                    
            # cache for next time
            self.unique_column_value_cache[column_label] = yielded

            self._unique_column_value_yielder(column_label)
