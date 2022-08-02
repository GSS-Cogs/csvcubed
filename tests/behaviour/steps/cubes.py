import datetime
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional
from unicodedata import name

import requests_mock
from behave import *
import vcr
import pandas as pd
from pandas.testing import assert_frame_equal

from csvcubeddevtools.behaviour.file import get_context_temp_dir_path
from csvcubeddevtools.helpers.file import get_test_cases_dir

from csvcubed.cli.build import build as cli_build
from csvcubed.definitions import APP_ROOT_DIR_PATH
from csvcubed.models.cube.columns import CsvColumn

_test_case_dir = get_test_cases_dir()
_cube_config_test_case_dir = _test_case_dir / "readers" / "cube-config"
_cassettes_dir = _test_case_dir / "vcrpy-cassettes"


@given('The existing tidy data csv file "{data_file}"')
def step_impl(context, data_file):
    data_file = _cube_config_test_case_dir / data_file
    if not data_file.exists():
        raise Exception(f"Could not find test-case file {data_file}")
    context.data_file = data_file


@given(
    'The config json file "{config_file}" and the existing tidy data csv file '
    '"{data_file}"'
)
def step_impl(context, config_file, data_file):
    config_file = _cube_config_test_case_dir / config_file
    if not config_file.exists():
        raise Exception(f"Could not find test-case file {config_file}")

    data_file = _cube_config_test_case_dir / data_file
    if not data_file.exists():
        raise Exception(f"Could not find test-case file {data_file}")

    context.config_file = config_file
    context.data_file = data_file


@when("The cube is created")
def step_impl(context):
    config_file = context.config_file if hasattr(context, "config_file") else None
    data_file = context.data_file
    scenario_name = context.scenario.name
    cassette_file_name = scenario_name.rsplit("]")[1]

    mocker = requests_mock.Mocker(real_http=True)
    mocker.start()

    paths_to_mock: Dict[str, Path] = {
        "https://purl.org/csv-cubed/qube-config/v1.0": APP_ROOT_DIR_PATH
        / "schema"
        / "cube-config"
        / "v1_0"
        / "schema.json",
        "https://purl.org/csv-cubed/qube-config/v1.1": APP_ROOT_DIR_PATH
        / "schema"
        / "cube-config"
        / "v1_1"
        / "schema.json",
        "https://purl.org/csv-cubed/qube-config/v1.2": APP_ROOT_DIR_PATH
        / "schema"
        / "cube-config"
        / "v1_2"
        / "schema.json",
        "https://purl.org/csv-cubed/qube-config/v1": APP_ROOT_DIR_PATH
        / "schema"
        / "cube-config"
        / "v1_2"
        / "schema.json",  # v1 defaults to latest minor version of v1.*.
        "https://purl.org/csv-cubed/code-list-config/v1.0": APP_ROOT_DIR_PATH
        / "schema"
        / "codelist-config"
        / "v1_0"
        / "schema.json",
        "https://purl.org/csv-cubed/code-list-config/v1": APP_ROOT_DIR_PATH
        / "schema"
        / "codelist-config"
        / "v1_0"
        / "schema.json",  # v1 defaults to latest minor version of v1.*.
    }

    templates_dir = (
        APP_ROOT_DIR_PATH / "readers" / "cubeconfig" / "v1_0" / "templates"
    )

    template_files = templates_dir.rglob("**/*.json*")

    if not any(template_files):
        raise ValueError(f"Couldn't find template files in {templates_dir}.")

    for template_file in template_files:
        relative_file_path = str(template_file.relative_to(templates_dir))
        paths_to_mock["https://raw.githubusercontent.com/GSS-Cogs/csvcubed/main/src/csvcubed/readers/cubeconfig/v1_0/templates/"+ relative_file_path] = template_file


    for uri, path in paths_to_mock.items():
        with open(path) as f:
            mocker.register_uri("GET", uri, text=f.read())

    context.out_dir = get_context_temp_dir_path(context) / "out"
    context.add_cleanup(lambda: mocker.stop())

    with vcr.use_cassette(str(_cassettes_dir / f"{cassette_file_name}.yaml")):

        cube, errors = cli_build(
            data_file,
            config_file,
            output_directory=context.out_dir,
            validation_errors_file_out=context.out_dir / "validation_errors.json",
        )

        context.cube = cube
        context.errors = errors

@then("There are no errors")
def step_impl(context):
    assert len(context.errors) == 0

@then("The cube Metadata should match")
def step_impl(context):
    expected_meta = eval(context.text.strip().replace("\r\n", ""))
    result_dict = context.cube.metadata.as_json_dict()

    if expected_meta != result_dict:
        # Print the mis-matched values if the whole dict is not equal
        for k, v in result_dict.items():
            true_value = result_dict[k]
            if isinstance(true_value, (datetime.datetime, datetime.date)):
                true_value = true_value.isoformat()

            if expected_meta[k] != true_value:
                raise Exception(
                    f"Key: {k} - result: {result_dict[k]} does not match expected: {expected_meta[k]}"
                )
    assert expected_meta == result_dict


@then("The cube columns should match")
def step_impl(context):
    cols: List[CsvColumn] = context.cube.columns
    print("cols:", cols)
    expected_cols: List[str] = json.loads(context.text)
    for col in cols:
        assert col.csv_column_title in expected_cols


@then("The cube data should match")
def step_impl(context):
    data: Optional[pd.DataFrame] = context.cube.data
    print("data:", data)
    expected_data = pd.read_json(context.text, orient="records", dtype=False)
    assert_frame_equal(expected_data, data, check_dtype=False, check_categorical=False)
