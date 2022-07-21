"""
Pandas Utils
------------

This file provides additional utilities for pandas typoe commands
"""
import logging
from typing import Dict, List, Tuple

import pandas as pd

from pathlib import Path

from csvcubed.models.validationerror import ValidationError

from csvcubed.models.cube.validationerrors import DuplicateColumnTitleError


_logger = logging.getLogger(__name__)

# Values used in place of NA in dataframe reads
SPECIFIED_NA_VALUES = {
    "",
}

def read_csv(csv_path: Path, **kwargs) -> Tuple[pd.DataFrame, List[ValidationError]]:
    """
    """
    # Set default but allow interventions for advanced users
    if "keep_default_na" not in kwargs: kwargs["keep_default_na"] = False
    if "na_values" not in kwargs: kwargs["na_values"] = SPECIFIED_NA_VALUES

    df = pd.read_csv(csv_path, **kwargs)
    if not isinstance(df, pd.DataFrame):
        _logger.debug("Expected a pandas dataframe when reading from CSV, value was %s", df)
        raise ValueError(
            f"Expected a pandas dataframe when reading from CSV, value was {type(df)}"
        )

    # Read first row as values rather than headers, so we can check for duplicate column titles
    col_title_counts = pd.read_csv(csv_path, header=None, nrows=1).iloc[0, :].value_counts()  # type: ignore
    duplicate_titles = list(col_title_counts[col_title_counts > 1].keys())

    return df, [
            DuplicateColumnTitleError(csv_column_title=dupe_title)
            for dupe_title in duplicate_titles
        ]
