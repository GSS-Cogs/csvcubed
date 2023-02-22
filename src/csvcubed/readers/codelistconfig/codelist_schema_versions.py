"""
Code List Schema Versions
---------------

Contains an enum listing the code-list-config.json schema versions recognised by csvcubed.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from csvcubed.models.codelistconfig.code_list_config import CodeListConfig
from csvcubed.models.cube.qb.components.codelist import NewQbCodeList
from csvcubed.models.jsonvalidationerrors import JsonSchemaValidationError
from csvcubed.models.validationerror import ValidationError
from csvcubed.readers.cubeconfig.utils import load_resource
from csvcubed.readers.cubeconfig.v1 import configdeserialiser as v1_configdeserialiser
from csvcubed.utils.validators.schema import (
    map_to_internal_validation_errors,
    validate_dict_against_schema,
)

_logger = logging.getLogger(__name__)


CodeListConfigDeserialiser = Callable[
    [Path],
    Tuple[NewQbCodeList, List[JsonSchemaValidationError], List[ValidationError]],
]


"""
In order to update the MINOR version of code-list config, please follow the below steps.
    Step 1: Define a new constant to hold the PURL of the new schema (e.g. _v1_3_SCHEMA_URL).
    Step 2: Update the _LATEST_V1_CODELIST_SCHEMA_URL and _LATEST_CODELIST_SCHEMA_URL so that they are assigned to the constant defined in Step 1.
    Step 3: Add a new enum to the CodeListConfigJsonSchemaMinorVersion to represent the new version.
    Step 4: Add a new elif to the _get_schema_version() to represent the new version.
    Step 5: Add the new URL and file path to _hard_coded_map_url_to_file_path in /utils/cache.py and update the value of the default path (denoted with a comment in the map).
    Step 6: Add a new behaviour test to cube.feature file for validating the code-list generation using new version of the schema (e.g. "Successfully outputs a code-list using schema v1.3" behave scenario).
    Step 7: Update the `test_get_schema_code_list_version_1_latest()` unit test in the test_codelist.py.
"""

_v1_0_CODELIST_SCHEMA_URL = "https://purl.org/csv-cubed/code-list-config/v1.0"
_v1_1_CODELIST_SCHEMA_URL = "https://purl.org/csv-cubed/code-list-config/v1.1"

V1_CODELIST_SCHEMA_URL = "https://purl.org/csv-cubed/code-list-config/v1"  # v1 defaults to the latest minor version of v1.*.


_LATEST_V1_CODELIST_SCHEMA_URL = _v1_1_CODELIST_SCHEMA_URL
"""
    This holds the URL identifying the latest minor version of the V1 schema.

    When adding a new minor version to the V1 schema, you must update this variable.
"""

_LATEST_CODELIST_SCHEMA_URL = _v1_1_CODELIST_SCHEMA_URL
"""
    This holds the URL identifying the latest version of the schema.

    When adding a new schema version, you must update this variable.
"""


class CodeListConfigJsonSchemaMajorVersion(Enum):
    """
    Major versions of the code list config schema.
    """

    v1 = 1


class CodeListConfigJsonSchemaMinorVersion(Enum):
    """
    Minor versions of the code list config schema.
    """

    v0 = 0
    v1 = 1


def _extract_and_validate_code_list_v1(
    code_list_config_path: Path,
) -> Tuple[NewQbCodeList, List[JsonSchemaValidationError], List[ValidationError]]:
    """Fill this in"""
    code_list_config, code_list_config_dict = CodeListConfig.from_json_file(
        code_list_config_path
    )
    schema = load_resource(code_list_config.schema)

    unmapped_schema_validation_errors = validate_dict_against_schema(
        value=code_list_config_dict, schema=schema
    )

    code_list_schema_validation_errors = map_to_internal_validation_errors(
        schema, unmapped_schema_validation_errors
    )

    code_list = NewQbCodeList(
        code_list_config.metadata, code_list_config.new_qb_concepts
    )
    return (
        code_list,
        code_list_schema_validation_errors,
        code_list.pydantic_validation(),
    )


def get_deserialiser_for_code_list_schema(
    maybe_schema_path: Optional[str],
) -> CodeListConfigDeserialiser:
    """
    Provides a versioned deserialiser function appropriate to the referenced schema.
    """
    # Default to the latest version of the schema.
    schema_path = (
        _LATEST_CODELIST_SCHEMA_URL if maybe_schema_path is None else maybe_schema_path
    )

    schema_version_major, schema_version_minor = _get_schema_code_list_version(
        schema_path
    )
    _logger.info(
        "Using schema version %s.%s",
        schema_version_major.value,
        schema_version_minor.value,
    )

    if schema_version_major == CodeListConfigJsonSchemaMajorVersion.v1:
        return _extract_and_validate_code_list_v1
    else:
        raise ValueError(f"Unhandled major schema version {schema_version_major}")


def _get_schema_code_list_version(
    schema_path: str,
) -> Tuple[CodeListConfigJsonSchemaMajorVersion, CodeListConfigJsonSchemaMinorVersion]:
    if schema_path == V1_CODELIST_SCHEMA_URL:
        schema_path = _LATEST_V1_CODELIST_SCHEMA_URL

    if schema_path == _v1_0_CODELIST_SCHEMA_URL:
        return (
            CodeListConfigJsonSchemaMajorVersion.v1,
            CodeListConfigJsonSchemaMinorVersion.v0,
        )
    # The second condition in the following makes v1 defaults to the latest minor version of v1.*.
    elif schema_path == _v1_1_CODELIST_SCHEMA_URL:
        return (
            CodeListConfigJsonSchemaMajorVersion.v1,
            CodeListConfigJsonSchemaMinorVersion.v1,
        )
    else:
        raise ValueError(
            f"The $schema '{schema_path}' referenced in the code list config file is not recognised. Please check for any updates to your csvcubed installation."
        )