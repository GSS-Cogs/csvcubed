from pathlib import Path

import pytest
from rdflib import ConjunctiveGraph

from csvcubed.models.csvwtype import CSVWType
from csvcubed.utils.sparql_handler.csvw_state import CsvWState
from csvcubed.utils.sparql_handler.sparql import path_to_file_uri_for_rdflib
from csvcubed.utils.tableschema import CsvwRdfManager
from tests.unit.test_baseunit import get_test_cases_dir

_test_case_base_dir = get_test_cases_dir() / "cli" / "inspect"


def get_path_to_file(folder_name: str, file_name: str) -> Path:

    csvw_metadata_json_path = _test_case_base_dir / folder_name / file_name
    return csvw_metadata_json_path


csvw_rdf_manager = CsvwRdfManager(
    get_path_to_file("pivoted-single-measure-dataset", "qb-id-10004.csv-metadata.json")
)


def test_get_primary_catalog_metadata():
    """
    Tests that primary catalog metadata can correctly be retrieved from an input
    csvw metadata json file's CsvwRdfManager object, by accessing its csvw_state and
    running the function.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )
    # csvw_rdf_manager = CsvwRdfManager(csvw_metadata_json_path)
    primary_graph_identifier = path_to_file_uri_for_rdflib(csvw_metadata_json_path)

    test_catalog_metadata_result = (
        csvw_rdf_manager.csvw_state.get_primary_catalog_metadata()
    )

    assert test_catalog_metadata_result.graph_uri == primary_graph_identifier


def test_get_primary_catalog_metadata_key_error():
    """
    Test to ensure that when primary catalog metadata cannot be returned for a
    particular graph, the API function returns a KeyError instead.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )

    rdf_graph = ConjunctiveGraph()

    csvw_inspector = CsvWState(rdf_graph, csvw_metadata_json_path)

    with pytest.raises(KeyError) as exception:
        assert csvw_inspector.get_primary_catalog_metadata()

    assert (
        f"Could not find catalog metadata in primary graph '{csvw_inspector.primary_graph_uri}'."
        in str(exception.value)
    )


def test_detect_csvw_type_qb_dataset():
    """
    Tests the detection of the csvw_type of an input metadata json file that has a CsvwRdfManager
    object created from it, in this case to correctly detect a QbDataset csvw type from its csvw_state.
    """

    csvw_type = csvw_rdf_manager.csvw_state.csvw_type
    assert csvw_type == CSVWType.QbDataSet


def test_csvw_type_key_error():
    """
    Test to ensure that when a conjunctive graph that is not recognised by the
    csvw_type() function as a code list or a qb data set returns a type error.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )

    rdf_graph = ConjunctiveGraph()

    csvw_inspector = CsvWState(rdf_graph, csvw_metadata_json_path)

    with pytest.raises(TypeError) as exception:
        assert csvw_inspector.csvw_type()

    assert (
        "The input metadata is invalid as it is not a data cube or a code list."
        in str(exception.value)
    )


def test_detect_csvw_type_code_list():
    """
    Tests the detection of the csvw_type of an input metadata json file that has a CsvwRdfManager
    object created from it, in this case to correctly detect a CodeList csvw type from its csvw_state.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "some-dimension.csv-metadata.json"
    )
    csvw_rdf_manager = CsvwRdfManager(csvw_metadata_json_path)

    csvw_type = csvw_rdf_manager.csvw_state.csvw_type
    assert csvw_type == CSVWType.CodeList
