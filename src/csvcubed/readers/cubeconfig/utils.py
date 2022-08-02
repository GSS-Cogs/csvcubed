from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from pandas import DataFrame

from csvcubed.utils.json import load_json_document
from csvcubed.utils.uri import looks_like_uri
from csvcubed.models.validationerror import ValidationError
from csvcubed.utils.pandas import read_csv


def load_resource(resource_path: Union[str, Path]) -> dict:
    """
    Loads a json schema document from either a File or URI
    """
    if isinstance(resource_path, str):
        if looks_like_uri(resource_path):
            return load_json_document(str(resource_path))
        else:
            resource_path = Path(resource_path)

    if not resource_path.is_absolute():
        resource_path = resource_path.resolve()
    return load_json_document(resource_path)


def generate_title_from_file_name(csv_path: Path) -> str:
    """
    Formats a file Path, stripping -_ and returning the capitalised file name without extn
    e.g. Path('./csv-data_file.csv') -> 'Csv Data File'
    """
    return " ".join(
        [
            word.capitalize()
            for word in csv_path.stem.replace("-", " ").replace("_", " ").split(" ")
        ]
    )


def read_and_check_csv(
    csv_path: Path, dtype: Optional[Dict[str, str]] = None
) -> Tuple[DataFrame, List[ValidationError]]:
    """
    Reads the csv data file and performs rudimentary checks.
    """

    data, data_errors = read_csv(csv_path, dtype=dtype)

    if isinstance(data, DataFrame):
        if len(data) == 0:
            # Must have 2 or more rows, a heading row and a data row
            raise ValueError(
                "CSV input must contain header row and at least one row of data "
            )
    else:
        raise TypeError("There was a problem reading the csv file as a dataframe")

    return data, data_errors
