"""
behave functionality to run csv-lint on some output
"""
from behave import *
from nose.tools import *
from pathlib import Path
import docker
import sys
from typing import Tuple

from devtools.helpers.tar import dir_to_tar
from devtools.behave.temporarydirectory import get_context_temp_dir_path


def _run_csvlint(metadata_file_path: Path) -> Tuple[int, str]:
    client = docker.from_env()
    csvlint = client.containers.create(
        "gsscogs/csvlint", command=f"csvlint -s '/tmp/{metadata_file_path.name}'"
    )
    csvlint.put_archive("/tmp", dir_to_tar(metadata_file_path.parent))
    csvlint.start()
    response: dict = csvlint.wait()
    exit_code = response["StatusCode"]
    sys.stdout.write(csvlint.logs().decode("utf-8"))
    return exit_code, csvlint.logs().decode("utf-8")


@step('csvlint validation of "{file}" should succeed')
def step_impl(context, file: str):
    temp_dir = get_context_temp_dir_path(context)
    exit_code, logs = _run_csvlint(temp_dir / file)
    assert_equal(exit_code, 0)


@step('csvlint validation of "{file}" should fail with "{expected}"')
def step_impl(context, file: str, expected: str):
    temp_dir = get_context_temp_dir_path(context)
    exit_code, logs = _run_csvlint(temp_dir / file)
    assert_equal(exit_code, 1)
    assert expected in logs
