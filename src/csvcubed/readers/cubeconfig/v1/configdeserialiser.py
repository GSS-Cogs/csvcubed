"""
Config.json Loader
__________________

A loader for the v1.* config.json.
"""
import logging
from json import JSONDecodeError
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Callable

from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from csvcubed.models.cube.qb.columns import QbColumn

from csvcubed.models.cube import QbCube
from csvcubed.models.cube.columns import CsvColumn
from csvcubed.models.cube.cube import Cube
from csvcubed.models.cube.qb.catalog import CatalogMetadata
from csvcubed.models.validationerror import ValidationError
from csvcubed.utils.iterables import first
from csvcubed.utils.validators.schema import validate_dict_against_schema
from csvcubed.readers.cubeconfig.utils import (
    generate_title_from_file_name,
    load_resource,
    read_and_check_csv,
)
from csvcubed.readers.catalogmetadata.v1.catalog_metadata_reader import (
    metadata_from_dict,
)
from csvcubed.readers.cubeconfig.v1.mapcolumntocomponent import (
    map_column_to_qb_component,
)
from csvcubed.readers.cubeconfig.v1 import datatypes

from .constants import CONVENTION_NAMES

# Used to determine whether a column name matches accepted conventions
from ...preconfiguredtemplates import apply_preconfigured_values_from_template


_logger = logging.getLogger(__name__)


def get_deserialiser(
    schema_path: str,
    cube_config_minor_version: int,
) -> Callable[
    [Path, Optional[Path]],
    Tuple[QbCube, List[JsonSchemaValidationError], List[ValidationError]],
]:
    """Generates a deserialiser function which validates the JSON file against the schema at :obj:`schema_path`"""

    def get_cube_from_config_json(
        csv_path: Path,
        config_path: Optional[Path],
    ) -> Tuple[QbCube, List[JsonSchemaValidationError], List[ValidationError]]:
        """
        Generates a Cube structure from a config.json input.
        :return: tuple of cube and json schema errors (if any)
        """

        # If we have a config json file then load it and validate against its reference schema
        if config_path:
            config = load_resource(config_path.resolve())
            # Update loaded config's title if not defined, setting title from csv data file path.
            if config.get("title") is None:
                config["title"] = generate_title_from_file_name(csv_path)
            try:
                schema = load_resource(schema_path)
                schema_validation_errors = validate_dict_against_schema(
                    value=config, schema=schema
                )
            except JSONDecodeError:
                _logger.warning(
                    "Validation of the config json is not currently available, continuing without validation."
                )
                schema_validation_errors = []

        # Create a default config, setting title from csv data file path.
        else:
            config = {"title": generate_title_from_file_name(csv_path)}
            schema_validation_errors = []

        dtype = datatypes.get_pandas_datatypes(csv_path, config=config)
        _logger.info(f'csv {csv_path} has mapping of columns to datatypes: {dtype}')
        data, data_errors = read_and_check_csv(csv_path, dtype=dtype)

        (cube, code_list_schema_validation_errors) = _get_cube_from_config_json_dict(
            data,
            config,
            cube_config_minor_version,
            config_path=config_path,
        )
        schema_validation_errors += code_list_schema_validation_errors

        code_list_schema_validation_errors = _configure_remaining_columns_by_convention(
            cube,
            data,
            cube_config_minor_version,
            config_path=config_path,
        )
        schema_validation_errors += code_list_schema_validation_errors

        return cube, schema_validation_errors, data_errors

    return get_cube_from_config_json


def _get_cube_from_config_json_dict(
    data: pd.DataFrame,
    config: Dict,
    cube_config_minor_version: int,
    config_path: Optional[Path] = None,
) -> Tuple[QbCube, list[JsonSchemaValidationError]]:
    columns: List[CsvColumn] = []
    metadata: CatalogMetadata = metadata_from_dict(config)

    config_columns = config.get("columns", {})
    code_list_schema_validation_errors: list[JsonSchemaValidationError] = []
    for (column_title, column_config) in config_columns.items():
        (qb_column, validation_errors) = _get_qb_column_from_json(
            column_config,
            column_title,
            data,
            cube_config_minor_version,
            config_path=config_path,
        )
        columns.append(qb_column)
        if validation_errors:
            code_list_schema_validation_errors += validation_errors

    return (Cube(metadata, data, columns), code_list_schema_validation_errors)


def _get_qb_column_from_json(
    column_config: dict,
    column_title: str,
    data: pd.DataFrame,
    cube_config_minor_version: int,
    config_path: Optional[Path] = None,
) -> Tuple[QbColumn, Optional[list[JsonSchemaValidationError]]]:
    # When the config json contains a col definition and the col title is not in the data
    column_data = data[column_title] if column_title in data.columns else None
    # Load configuration from the "from_template": if provided.
    apply_preconfigured_values_from_template(
        column_config=column_config,
        column_name=column_title,
    )

    return map_column_to_qb_component(
        column_title,
        column_config,
        column_data,
        cube_config_minor_version,
        config_path=config_path,
    )


def _configure_remaining_columns_by_convention(
    cube: QbCube,
    data: pd.DataFrame,
    cube_config_minor_version: int,
    config_path: Optional[Path] = None,
) -> list[JsonSchemaValidationError]:
    """Update columns from csv where appropriate, i.e. config did not define the column."""
    configured_columns = {col.csv_column_title: col for col in cube.columns}
    ordered_columns: List[CsvColumn] = []
    code_list_schema_validation_errors: list[JsonSchemaValidationError] = []

    for i, column_title in enumerate(data.columns):
        # ... determine if the column_title in data matches a convention
        if column_title in configured_columns:
            ordered_columns.append(configured_columns[column_title])
            del configured_columns[column_title]
        elif column_title not in configured_columns:
            column_dict = _get_conventional_column_definition_for_title(column_title)

            (qb_column, validation_errors) = map_column_to_qb_component(
                column_title=column_title,
                column=column_dict,
                data=data[column_title].astype("category"),
                cube_config_minor_version=cube_config_minor_version,
                config_path=config_path,
            )
            if validation_errors:
                code_list_schema_validation_errors += validation_errors
            ordered_columns.append(qb_column)

    cube.columns = ordered_columns + list(configured_columns.values())
    return code_list_schema_validation_errors


def _get_conventional_column_definition_for_title(column_title: str) -> dict:
    matching_column_types = [
        standard_name
        for standard_name, options in CONVENTION_NAMES.items()
        if column_title.lower() in options
    ]
    # ... get or default the column type
    column_type = first(matching_column_types) or "dimension"
    # ... create a default config dict for the column type
    if column_type == "dimension":
        return {
            "type": column_type,
            "label": column_title,
            "code_list": True,
        }

    elif column_type == "observations":
        return {
            "type": column_type,
            "value": column_title,
            "datatype": "decimal",
        }

    elif column_type in ["measures", "units"]:
        return {"type": column_type}
    elif column_type == "attribute":
        # Note: attribute type columns are currently not supported for getting from data
        raise ValueError(
            "Conventionally named attribute columns are not current supported"
        )

    raise ValueError(f"Column type '{column_type}' is not supported.")
