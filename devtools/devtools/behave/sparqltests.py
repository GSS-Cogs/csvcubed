"""
behave functionality to run csv-lint on some output
"""
from behave import step
import nose.tools as nose
import docker
import sys
from typing import Tuple, List


from devtools.helpers.tar import dir_to_tar
from devtools.behave.temporarydirectory import get_context_temp_dir_path


def _run_sparql_tests(context, tests_to_run: List[str] = []) -> Tuple[int, str]:
    if "all" in tests_to_run:
        tests_to_run = ["skos", "pmd", "qb"]

    client = docker.from_env()

    # Stick the ttl into a file for consumption by the test runner.
    temp_dir = get_context_temp_dir_path(context)
    with open(temp_dir / "content.ttl", "w+") as f:
        f.write(context.turtle)

    test_dir_params = " ".join([f"-t '/usr/local/tests/{t}'" for t in tests_to_run])
    sparql_test_runner = client.containers.create(
        'gsscogs/gdp-sparql-tests',
        command=f'sparql-test-runner {test_dir_params} /tmp/content.ttl'
    )

    sparql_test_runner.put_archive("/tmp", dir_to_tar(temp_dir))

    sparql_test_runner.start()
    response: dict = sparql_test_runner.wait()
    exit_code = response["StatusCode"]
    sys.stdout.write(sparql_test_runner.logs().decode('utf-8'))

    return exit_code, sparql_test_runner.logs().decode('utf-8')


@step("the RDF should pass \"{test_types}\" SPARQL tests")
def step_impl(context, test_types: str):
    exit_code, logs = _run_sparql_tests(context, test_types.split(", "))
    nose.assert_equal(exit_code, 0)


@step("the RDF should fail \"{test_types}\" SPARQL tests with \"{expected}\"")
def step_impl(context, test_types: str, expected: str):
    exit_code, logs = _run_sparql_tests(context, test_types.split(", "))
    nose.assert_equal(exit_code, 1)
    assert expected in logs
