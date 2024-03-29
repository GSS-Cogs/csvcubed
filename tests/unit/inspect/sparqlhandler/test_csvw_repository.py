from pathlib import Path

import pytest
from rdflib import ConjunctiveGraph

from csvcubed.inspect.sparql_handler.csvw_repository import CsvWRepository
from csvcubed.inspect.sparql_handler.sparql import path_to_file_uri_for_rdflib
from csvcubed.models.csvwtype import CSVWType
from csvcubed.models.inspect.sparqlresults import ColumnDefinition
from tests.helpers.repository_cache import (
    get_code_list_repository,
    get_csvw_rdf_manager,
    get_data_cube_repository,
)
from tests.unit.test_baseunit import get_test_cases_dir

_test_case_base_dir = get_test_cases_dir() / "cli" / "inspect"


def test_get_primary_catalog_metadata():
    """
    Tests that primary catalog metadata can correctly be retrieved from an input
    csvw metadata json file's CsvWRdfManager object, by accessing its csvw_repository and
    running the function.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )
    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository
    primary_graph_identifier = path_to_file_uri_for_rdflib(csvw_metadata_json_path)

    test_catalog_metadata_result = csvw_repository.get_primary_catalog_metadata()

    assert test_catalog_metadata_result.graph_uri == primary_graph_identifier


def test_get_primary_catalog_metadata_key_error():
    """
    Test to ensure that when primary catalog metadata cannot be returned for a
    particular graph, the API function returns a KeyError instead.
    """
    rdf_graph = ConjunctiveGraph()

    csvw_repository = CsvWRepository(
        rdf_graph, Path("does-not-exist.csv-metadata.json")
    )

    with pytest.raises(KeyError) as exception:
        assert csvw_repository.get_primary_catalog_metadata()

    assert (
        f"Could not find catalog metadata in primary graph '{csvw_repository.primary_graph_uri}'."
        in str(exception.value)
    )


def test_detect_csvw_type_qb_dataset():
    """
    Tests the detection of the csvw_type of an input metadata json file that has a CsvWRdfManager
    object created from it, in this case to correctly detect a QbDataset csvw type from its csvw_repository.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )
    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository
    csvw_type = csvw_repository.csvw_type

    assert csvw_type == CSVWType.QbDataSet


def test_csvw_type_key_error():
    """
    Test to ensure that when a conjunctive graph that is not recognised by the
    csvw_type() function as a code list or a qb data set returns a type error.
    """

    rdf_graph = ConjunctiveGraph()

    csvw_repository = CsvWRepository(
        rdf_graph, Path("does-not-exist.csv-metadata.json")
    )

    with pytest.raises(TypeError) as exception:
        assert csvw_repository.csvw_type()

    assert (
        "The input metadata is invalid as it is not a data cube or a code list."
        in str(exception.value)
    )


def test_detect_csvw_type_code_list():
    """
    Tests the detection of the csvw_type of an input metadata json file that has a CsvWRdfManager
    object created from it, in this case to correctly detect a CodeList csvw type from its csvw_repository.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "some-dimension.csv-metadata.json"
    )
    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository
    csvw_type = csvw_repository.csvw_type

    assert csvw_type == CSVWType.CodeList


def test_get_table_info_for_csv_url():
    """
    Ensures that the correct table schema properties are returned for the given code list.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "some-dimension.csv-metadata.json"
    )
    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository

    result = csvw_repository.get_table_info_for_csv_url("some-dimension.csv")

    assert result.about_url == "some-dimension.csv#{+uri_identifier}"
    assert result.csv_url == "some-dimension.csv"
    assert result.primary_key_col_names == ["uri_identifier"]


def test_get_table_info_multiple_tables():
    """
    Tests retrieval of all tables from a data cube that contains multiple tables.
    """
    csvw_metadata_json_path = _test_case_base_dir / "datacube.csv-metadata.json"
    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository

    result = csvw_repository._table_schema_properties

    assert len(result) == 4

    assert (
        result["alcohol-bulletin.csv"].about_url
        == "alcohol-bulletin.csv#obs/{+period}/{+alcohol_type}/{+alcohol_sub_type}/{+alcohol_content}/{+clearance_origin}/{+measure_type}"
    )
    assert result["alcohol-content.csv"].about_url == "alcohol-content.csv#{+notation}"
    assert (
        result["alcohol-sub-type.csv"].about_url == "alcohol-sub-type.csv#{+notation}"
    )
    assert (
        result["clearance-origin.csv"].about_url == "clearance-origin.csv#{+notation}"
    )

    assert set(result["alcohol-bulletin.csv"].primary_key_col_names) == {
        "alcohol_content",
        "alcohol_sub_type",
        "alcohol_type",
        "clearance_origin",
        "measure_type",
        "period",
    }
    assert result["alcohol-content.csv"].primary_key_col_names == ["notation"]
    assert result["clearance-origin.csv"].primary_key_col_names == ["notation"]
    assert result["alcohol-sub-type.csv"].primary_key_col_names == ["notation"]


def test_get_data_cube_column_definitions_for_csv():
    """
    Ensures that the `ColumnDefinition`s with different property values can be correctly loaded from as CSV-W file.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)
    csv_url = data_cube_repository.get_primary_csv_url()

    results = {
        c.name: c
        for c in data_cube_repository.csvw_repository.get_column_definitions_for_csv(
            csv_url
        )
    }

    assert len(results) == 12

    """
    Testing: csv_url, name, property_url, required=True, suppress_output=False,
              title, value_url, virtual=False
    """
    assert results["some_dimension"] == ColumnDefinition(
        csv_url="qb-id-10004.csv",
        about_url=None,
        data_type=None,
        name="some_dimension",
        property_url="qb-id-10004.csv#dimension/some-dimension",
        required=True,
        suppress_output=False,
        title="Some Dimension",
        value_url="some-dimension.csv#{+some_dimension}",
        virtual=False,
    )

    """
    Testing: about_url, required=False
    """
    assert results["some_attribute"] == ColumnDefinition(
        csv_url="qb-id-10004.csv",
        about_url="qb-id-10004.csv#obs/{some_dimension}@some-measure",
        data_type=None,
        name="some_attribute",
        property_url="qb-id-10004.csv#attribute/some-attribute",
        required=False,
        suppress_output=False,
        title="Some Attribute",
        value_url="qb-id-10004.csv#attribute/some-attribute/{+some_attribute}",
        virtual=False,
    )

    """
    Testing: data_type
    """
    assert results["some_obs_val"] == ColumnDefinition(
        csv_url="qb-id-10004.csv",
        about_url="qb-id-10004.csv#obs/{some_dimension}@some-measure",
        data_type="http://www.w3.org/2001/XMLSchema#decimal",
        name="some_obs_val",
        property_url="qb-id-10004.csv#measure/some-measure",
        required=True,
        suppress_output=False,
        title="Some Obs Val",
        value_url=None,
        virtual=False,
    )

    """
    Testing: virtual=True, suppress_output=True
    """
    assert results["virt_suppressed_test"] == ColumnDefinition(
        csv_url="qb-id-10004.csv",
        about_url="http://example.com/about",
        data_type=None,
        name="virt_suppressed_test",
        property_url="http://example.com/property",
        required=False,
        suppress_output=True,
        title=None,
        value_url="http://example.com/value",
        virtual=True,
    )


def test_get_code_list_column_definitions_for_csv():
    """
    Tests that the code list column definitions can be successfully retrieved and
    are as expected given the input csv.
    """
    csvw_metadata_json_path = _test_case_base_dir / "alcohol-content.csv-metadata.json"
    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository
    code_list_repository = get_code_list_repository(csvw_metadata_json_path)
    csv_url = code_list_repository.get_primary_csv_url()

    results = {
        c.name: c for c in csvw_repository.get_column_definitions_for_csv(csv_url)
    }
    assert results["label"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type=None,
        name="label",
        property_url="rdfs:label",
        required=True,
        suppress_output=False,
        title="Label",
        value_url=None,
        virtual=False,
    )
    assert results["notation"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type=None,
        name="notation",
        property_url="skos:notation",
        required=True,
        suppress_output=False,
        title="Notation",
        value_url=None,
        virtual=False,
    )
    assert results["parent_notation"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type=None,
        name="parent_notation",
        property_url="skos:broader",
        required=False,
        suppress_output=False,
        title="Parent Notation",
        value_url="alcohol-content.csv#{+parent_notation}",
        virtual=False,
    )
    assert results["sort_priority"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type="http://www.w3.org/2001/XMLSchema#integer",
        name="sort_priority",
        property_url="http://www.w3.org/ns/ui#sortPriority",
        required=False,
        suppress_output=False,
        title="Sort Priority",
        value_url=None,
        virtual=False,
    )
    assert results["description"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type=None,
        name="description",
        property_url="rdfs:comment",
        required=False,
        suppress_output=False,
        title="Description",
        value_url=None,
        virtual=False,
    )
    assert results["virt_inScheme"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type=None,
        name="virt_inScheme",
        property_url="skos:inScheme",
        required=True,
        suppress_output=False,
        title=None,
        value_url="alcohol-content.csv#code-list",
        virtual=True,
    )
    assert results["virt_type"] == ColumnDefinition(
        csv_url="alcohol-content.csv",
        about_url=None,
        data_type=None,
        name="virt_type",
        property_url="rdf:type",
        required=True,
        suppress_output=False,
        title=None,
        value_url="skos:Concept",
        virtual=True,
    )


def test_multi_theme_and_keyword():
    """
    This test ensures that the 'select_catalog_metadata.sparql' will return the correct amount of
    themes, keywords and landing pages(unique values and no duplications)
    URL to the issue description: 'https://app.zenhub.com/workspaces/features-squad-61b72275ac896c0010a1b00b/issues/gh/gss-cogs/csvcubed/739'
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-theme-and-keywords"
        / "aged-16-to-64-years-level-3-or-above-qualifications.csv-metadata.json"
    )

    csvw_rdf_manager = get_csvw_rdf_manager(csvw_metadata_json_path)
    primary_catalog_metadata = (
        csvw_rdf_manager.csvw_repository.get_primary_catalog_metadata()
    )

    assert set(primary_catalog_metadata.themes) == {
        "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork",
        "https://www.ons.gov.uk/employmentandlabourmarket/peopleonholidays",
        "https://www.ons.gov.uk/employmentandlabourmarket/peopleoutofwork",
    }
    assert set(primary_catalog_metadata.keywords) == {
        "education",
        "employment",
        "united-kingdom",
        "levelling-up",
        "qualifications",
        "subnational",
        "mission-6",
    }
    assert set(primary_catalog_metadata.landing_pages) == {
        "https://www.gov.uk/government/statistics/alcohol-bulletin"
    }


def test_columns_return_order():
    """This test will check if the columns are returned in the correct order."""
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-multi-measure-single-unit-component"
        / "multi-measure-pivoted-dataset-units-and-attributes.csv-metadata.json"
    )

    csvw_repository = get_csvw_rdf_manager(csvw_metadata_json_path).csvw_repository
    column_definitions = csvw_repository.get_column_definitions_for_csv(
        "multi-measure-pivoted-dataset-units-and-attributes.csv"
    )

    expected_column_titles = [
        "Year",
        "Sector",
        "Imports",
        "Imports Status",
        "Exports",
        "Exports Status",
        "Exports Unit",
    ]
    actual_column_names = [
        column.title for column in column_definitions if not column.virtual
    ]

    assert expected_column_titles == actual_column_names
