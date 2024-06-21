from pathlib import Path
from typing import List, Tuple

import numpy as np
import pytest
from pandas import DataFrame
from pandas.testing import assert_frame_equal
from treelib import Tree

from csvcubed.inspect.inspectdatasetmanager import (
    get_concepts_hierarchy_info,
    get_dataset_observations_info,
    get_dataset_val_counts_info,
    load_csv_to_dataframe,
)
from csvcubed.inspect.sparql_handler.code_list_repository import CodeListRepository
from csvcubed.inspect.sparql_handler.data_cube_repository import DataCubeRepository
from csvcubed.inspect.sparql_handler.sparqlquerymanager import (
    select_primary_key_col_names_by_csv_url,
)
from csvcubed.models.csvwtype import CSVWType
from csvcubed.models.cube.cube_shape import CubeShape
from csvcubed.models.cube.qb.validationerrors import BothMeasureTypesDefinedError
from csvcubed.models.inspect.inspectdataframeresults import (
    DatasetObservationsByMeasureUnitInfoResult,
    DatasetObservationsInfoResult,
)
from csvcubed.models.inspect.sparqlresults import (
    QubeComponentResult,
    QubeComponentsResult,
)
from csvcubed.utils.csvdataset import (
    get_single_measure_from_dsd,
    get_standard_shape_measure_col_name_from_dsd,
    get_standard_shape_unit_col_name_from_dsd,
    transform_dataset_to_canonical_shape,
)
from csvcubed.utils.skos.codelist import (
    CodelistPropertyUrl,
    get_codelist_col_title_by_property_url,
    get_codelist_col_title_from_col_name,
)
from tests.helpers.repository_cache import (
    get_code_list_repository,
    get_data_cube_repository,
)
from tests.unit.test_baseunit import get_test_cases_dir

_test_case_base_dir = get_test_cases_dir() / "cli" / "inspect"

_expected_dataframe = DataFrame(
    [
        {
            "Label": "All",
            "Notation": "all",
            "Parent Notation": "",
            "Sort Priority": 0,
            "Description": "",
        },
        {
            "Label": "Ready to Drink",
            "Notation": "ready-to-drink",
            "Parent Notation": "",
            "Sort Priority": 1,
            "Description": "",
        },
        {
            "Label": "Sparkling",
            "Notation": "sparkling",
            "Parent Notation": "",
            "Sort Priority": 2,
            "Description": "",
        },
        {
            "Label": "Still",
            "Notation": "still",
            "Parent Notation": "",
            "Sort Priority": 3,
            "Description": "",
        },
        {
            "Label": "UK",
            "Notation": "uk",
            "Parent Notation": "",
            "Sort Priority": 4,
            "Description": "",
        },
        {
            "Label": "UK Grain and Blend",
            "Notation": "uk-grain-and-blend",
            "Parent Notation": "",
            "Sort Priority": 5,
            "Description": "",
        },
        {
            "Label": "UK Potable",
            "Notation": "uk-potable",
            "Parent Notation": "",
            "Sort Priority": 6,
            "Description": "",
        },
        {
            "Label": "UK Registered",
            "Notation": "uk-registered",
            "Parent Notation": None,
            "Sort Priority": 7,
            "Description": "",
        },
        {
            "Label": "Uk Malt",
            "Notation": "uk-malt",
            "Parent Notation": "",
            "Sort Priority": 8,
            "Description": "",
        },
        {
            "Label": "UK Registered",
            "Notation": "uk-registered",
            "Parent Notation": "",
            "Sort Priority": 7,
            "Description": "",
        },
        {
            "Label": "Uk Malt",
            "Notation": "uk-malt",
            "Parent Notation": "",
            "Sort Priority": 8,
            "Description": "",
        },
    ]
).replace("", np.NAN)

expected_dataframe_pivoted_single_measure = DataFrame(
    [
        {"Some Dimension": "a", "Some Attribute": "attr-a", "Some Obs Val": 1},
        {"Some Dimension": "b", "Some Attribute": "attr-b", "Some Obs Val": 2},
        {"Some Dimension": "c", "Some Attribute": "attr-c", "Some Obs Val": 3},
    ]
).replace("", np.NAN)

expected_dataframe_pivoted_multi_measure = DataFrame(
    [
        {
            "Some Dimension": "a",
            "Some Attribute": "attr-a",
            "Some Obs Val": 1,
            "Some Other Obs Val": 2,
            "Some Unit": "percent",
        },
        {
            "Some Dimension": "b",
            "Some Attribute": "attr-b",
            "Some Obs Val": 2,
            "Some Other Obs Val": 4,
            "Some Unit": "percent",
        },
        {
            "Some Dimension": "c",
            "Some Attribute": "attr-c",
            "Some Obs Val": 3,
            "Some Other Obs Val": 6,
            "Some Unit": "percent",
        },
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_single_unit_single_measure = DataFrame(
    [
        {
            "Measure": "energy-consumption",
            "Unit": "millions-of-tonnes-of-oil-equivalent",
            "Count": 286,
        }
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_single_unit_multi_measure = DataFrame(
    [
        {
            "Measure": "emissions-ar4-gwps",
            "Unit": "MtCO2e",
            "Count": 49765,
        },
        {
            "Measure": "emissions-ar5-gwps",
            "Unit": "MtCO2e",
            "Count": 49765,
        },
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_multi_unit_single_measure = DataFrame(
    [
        {
            "Measure": "tax-receipts",
            "Unit": "gbp",
            "Count": 6,
        },
        {
            "Measure": "tax-receipts",
            "Unit": "gbp-million",
            "Count": 6,
        },
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_multi_unit_multi_measure = DataFrame(
    [
        {"Measure": "alcohol-duty-receipts", "Unit": "gbp-million", "Count": 314},
        {"Measure": "beer-duty-receipts", "Unit": "gbp-million", "Count": 314},
        {"Measure": "cider-duty-receipts", "Unit": "gbp-million", "Count": 314},
        {"Measure": "clearances", "Unit": "hectolitres", "Count": 4710},
        {"Measure": "clearances", "Unit": "hectolitres-of-alcohol", "Count": 942},
        {"Measure": "clearances", "Unit": "thousand-hectolitres", "Count": 1256},
        {"Measure": "clearances-of-alcohol", "Unit": "hectolitres", "Count": 942},
        {
            "Measure": "clearances-of-alcohol",
            "Unit": "thousand-hectolitres",
            "Count": 314,
        },
        {
            "Measure": "production-volume",
            "Unit": "thousand-hectolitres",
            "Count": 314,
        },
        {
            "Measure": "production-volume-alcohol",
            "Unit": "hectolitres",
            "Count": 314,
        },
        {
            "Measure": "production-volume-alcohol",
            "Unit": "thousand-hectolitres",
            "Count": 314,
        },
        {"Measure": "spirits-duty-receipts", "Unit": "gbp-million", "Count": 314},
        {"Measure": "wine-duty-receipts", "Unit": "gbp-million", "Count": 314},
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_pivoted_single_measure = DataFrame(
    [
        {
            "Measure": "Some Measure",
            "Unit": "Some Unit",
            "Count": 3,
        }
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_pivoted_multi_measure = DataFrame(
    [
        {
            "Measure": "Some Measure",
            "Unit": "Some Unit",
            "Count": 3,
        },
        {
            "Measure": "Some Other Measure",
            "Unit": "Percent",
            "Count": 3,
        },
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_with_column_titled_value = DataFrame(
    [
        {
            "Measure": "gas emissions(gwp-ar4)",
            "Unit": "millions of tonnes of carbon dioxide (mt co2)",
            "Count": 19,
        }
    ]
).replace("", np.NAN)


def get_arguments_qb_dataset(
    data_cube_repository: DataCubeRepository,
) -> Tuple[DataFrame, List[QubeComponentResult], str]:
    """
    Produces the dataset, qube components and dsd uri arguments for qb:dataset.
    """
    csvw_repository = data_cube_repository.csvw_repository

    result_dataset_uri = (
        data_cube_repository.csvw_repository.get_primary_catalog_metadata().distribution_uri
    )
    identifiers = data_cube_repository.get_cube_identifiers_for_dataset(
        result_dataset_uri
    )

    result: QubeComponentsResult = data_cube_repository.get_dsd_qube_components_for_csv(
        identifiers.csv_url
    )

    dataset: DataFrame = load_csv_to_dataframe(
        csvw_repository.csvw_json_path, Path(identifiers.csv_url)
    )

    return (dataset, result.qube_components, identifiers.csv_url)


def _get_arguments_skos_codelist(
    code_list_repository: CodeListRepository,
) -> Tuple[DataFrame, str]:
    """
    Produces the ConceptScheme for skos:codelist.
    """
    primary_catalogue_metadata = (
        code_list_repository.csvw_repository.get_primary_catalog_metadata()
    )
    csv_url = code_list_repository.get_table_identifiers_for_concept_scheme(
        primary_catalogue_metadata.dataset_uri
    ).csv_url

    dataset: DataFrame = load_csv_to_dataframe(
        code_list_repository.csvw_repository.csvw_json_path, Path(csv_url)
    )
    return (dataset, csv_url)


def test_load_csv_to_dataframe_success():
    """
    Should load the csv to dataframe successfully.
    """
    csvw_metadata_json_path = _test_case_base_dir / "datacube.csv-metadata.json"
    dataset = load_csv_to_dataframe(csvw_metadata_json_path, "csv_file.csv")

    assert dataset is not None
    assert len(dataset.index) == 11
    assert_frame_equal(dataset, _expected_dataframe)


def test_load_csv_to_dataframe_error():
    """
    Should error when loading csv to dataframe.
    """
    csvw_metadata_json_path = _test_case_base_dir / "datacube.csv-metadata.json"

    with pytest.raises(Exception):
        load_csv_to_dataframe(csvw_metadata_json_path, "missing_csv_file.csv")


def test_get_dataset_observations_info():
    """
    Should produce the expected `DatasetObservationsInfoResult`.
    """
    csvw_metadata_json_path = _test_case_base_dir / "datacube.csv-metadata.json"
    dataset = load_csv_to_dataframe(csvw_metadata_json_path, "csv_file.csv")

    result: DatasetObservationsInfoResult = get_dataset_observations_info(
        dataset, CSVWType.QbDataSet, CubeShape.Pivoted
    )

    assert result.num_of_observations == 11
    assert result.num_of_duplicates == 2
    assert_frame_equal(result.dataset_head, _expected_dataframe.head(n=10))
    assert_frame_equal(result.dataset_tail, _expected_dataframe.tail(n=10))


def test_get_dataset_observations_info_for_pivoted_single_measure_shape_dataset():
    """
    Ensures the expected 'DatasetObservationsInfoResult' object is returned from a pivoted single measure shape input.
    """
    _test_case_dir = (
        get_test_cases_dir() / "cli" / "inspect" / "pivoted-single-measure-dataset"
    )
    csvw_metadata_json_path = _test_case_dir / "qb-id-10004.csv-metadata.json"
    dataset = load_csv_to_dataframe(csvw_metadata_json_path, "qb-id-10004.csv")

    result: DatasetObservationsInfoResult = get_dataset_observations_info(
        dataset, CSVWType.QbDataSet, CubeShape.Pivoted
    )

    assert result.num_of_observations == 3
    assert result.num_of_duplicates == 0
    assert_frame_equal(
        result.dataset_head, expected_dataframe_pivoted_single_measure.head(n=3)
    )
    assert_frame_equal(
        result.dataset_tail, expected_dataframe_pivoted_single_measure.tail(n=3)
    )


def test_get_dataset_observations_info_for_pivoted_multi_measure_shape_dataset():
    """
    Ensures the expected 'DatasetObservationsInfoResult' object is returned from a pivoted single measure shape input.
    """
    _test_case_dir = (
        get_test_cases_dir() / "cli" / "inspect" / "pivoted-multi-measure-dataset"
    )
    csvw_metadata_json_path = _test_case_dir / "qb-id-10003.csv-metadata.json"
    dataset = load_csv_to_dataframe(csvw_metadata_json_path, "qb-id-10003.csv")

    result: DatasetObservationsInfoResult = get_dataset_observations_info(
        dataset, CSVWType.QbDataSet, CubeShape.Pivoted
    )

    assert result.num_of_observations == 3
    assert result.num_of_duplicates == 0
    assert_frame_equal(
        result.dataset_head, expected_dataframe_pivoted_multi_measure.head(n=3)
    )
    assert_frame_equal(
        result.dataset_tail, expected_dataframe_pivoted_multi_measure.tail(n=3)
    )


def test_get_measure_col_name_from_dsd_measure_col_present():
    """
    Should return the measure column name when measure col is present.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-bulletin.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    result_data_set_uri = (
        data_cube_repository.csvw_repository.get_primary_catalog_metadata().distribution_uri
    )
    identifiers = data_cube_repository.get_cube_identifiers_for_dataset(
        result_data_set_uri
    )

    result: QubeComponentsResult = data_cube_repository.get_dsd_qube_components_for_csv(
        identifiers.csv_url
    )

    measure_col = get_standard_shape_measure_col_name_from_dsd(result.qube_components)

    assert measure_col == "Measure Type"


def test_get_measure_col_name_from_dsd_measure_col_not_present():
    """
    Should return the None when measure column is not present.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_single-measure"
        / "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2019.csv-metadata.json"
    )

    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)
    primary_catalog_metadata = (
        data_cube_repository.csvw_repository.get_primary_catalog_metadata()
    )

    identifiers = data_cube_repository.get_cube_identifiers_for_dataset(
        primary_catalog_metadata.dataset_uri
    )

    result: QubeComponentsResult = data_cube_repository.get_dsd_qube_components_for_csv(
        identifiers.csv_url
    )

    measure_col = get_standard_shape_measure_col_name_from_dsd(result.qube_components)

    assert measure_col is None


def test_get_unit_col_name_from_dsd_unit_col_present():
    """
    Should return the correct unit column name when the unit column is present.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-bulletin.csv-metadata.json"
    )

    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)
    primary_catalog_metadata = (
        data_cube_repository.csvw_repository.get_primary_catalog_metadata()
    )

    identifiers = data_cube_repository.get_cube_identifiers_for_dataset(
        primary_catalog_metadata.distribution_uri
    )

    result: QubeComponentsResult = data_cube_repository.get_dsd_qube_components_for_csv(
        identifiers.csv_url
    )

    unit_col = get_standard_shape_unit_col_name_from_dsd(result.qube_components)

    assert unit_col == "Unit"


def test_get_unit_col_name_from_dsd_unit_col_not_present():
    """
    Should return None when unit column is not present.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_single-measure"
        / "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2019.csv-metadata.json"
    )

    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)
    primary_catalog_metadata = (
        data_cube_repository.csvw_repository.get_primary_catalog_metadata()
    )

    identifiers = data_cube_repository.get_cube_identifiers_for_dataset(
        primary_catalog_metadata.dataset_uri
    )

    result: QubeComponentsResult = data_cube_repository.get_dsd_qube_components_for_csv(
        identifiers.csv_url
    )

    unit_col = get_standard_shape_unit_col_name_from_dsd(result.qube_components)

    assert unit_col is None


@pytest.mark.vcr
def test_get_single_measure_label_from_dsd():
    """
    Should return the correct measure label.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_single-measure"
        / "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2019.csv-metadata.json"
    )

    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)
    primary_catalog_metadata = (
        data_cube_repository.csvw_repository.get_primary_catalog_metadata()
    )

    identifiers = data_cube_repository.get_cube_identifiers_for_dataset(
        primary_catalog_metadata.dataset_uri
    )

    result: QubeComponentsResult = data_cube_repository.get_dsd_qube_components_for_csv(
        identifiers.csv_url
    )

    measure_col = get_standard_shape_measure_col_name_from_dsd(result.qube_components)
    assert measure_col is None

    result_measure = get_single_measure_from_dsd(
        result.qube_components, csvw_metadata_json_path
    )
    assert (
        result_measure.measure_uri
        == "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2019.csv#measure/gas-emissions-gwp-ar4"
    )
    assert result_measure.measure_label == "gas emissions(gwp-ar4)"


def test_get_val_counts_info_multi_unit_multi_measure_dataset():
    """
    Should produce expected `DatasetObservationsByMeasureUnitInfoResult` for multi-unit multi-measure dataset.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-bulletin.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    (dataset, qube_components, csv_url) = get_arguments_qb_dataset(data_cube_repository)

    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        data_cube_repository,
        dataset,
        csv_url,
        qube_components,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_multi_unit_multi_measure,
    )


def test_get_val_counts_info_multi_unit_single_measure_dataset():
    """
    Should produce expected `DatasetObservationsByMeasureUnitInfoResult` for multi-unit single-measure dataset.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_single-measure"
        / "new"
        / "multi-unit-single-measure-dataset.csv-metadata.json"
    )

    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    (dataset, qube_components, csv_url) = get_arguments_qb_dataset(data_cube_repository)

    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        data_cube_repository,
        dataset,
        csv_url,
        qube_components,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_multi_unit_single_measure,
    )


def test_get_val_counts_info_single_unit_multi_measure_dataset():
    """
    Should produce expected `DatasetObservationsByMeasureUnitInfoResult` for single-unit multi-measure dataset.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "single-unit_multi-measure"
        / "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2020.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    (dataset, qube_components, csv_url) = get_arguments_qb_dataset(data_cube_repository)

    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        data_cube_repository,
        dataset,
        csv_url,
        qube_components,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_single_unit_multi_measure,
    )


def test_get_val_counts_info_single_unit_single_measure_dataset():
    """
    Should produce expected `DatasetObservationsByMeasureUnitInfoResult` for single-unit single-measure dataset.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "single-unit_single-measure"
        / "energy-trends-uk-total-energy.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    (dataset, qube_components, csv_url) = get_arguments_qb_dataset(data_cube_repository)

    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        data_cube_repository,
        dataset,
        csv_url,
        qube_components,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_single_unit_single_measure,
    )


def test_get_val_counts_info_pivoted_single_measure_dataset():
    """
    Should produce expected `DatasetObservationsByMeasureUnitInfoResult` for pivoted single measure dataset.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-single-measure-dataset"
        / "qb-id-10004.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    (dataset, qube_components, csv_url) = get_arguments_qb_dataset(data_cube_repository)

    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        data_cube_repository,
        dataset,
        csv_url,
        qube_components,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_pivoted_single_measure,
    )


def test_get_val_counts_info_pivoted_multi_measure_dataset():
    """
    Should produce expected `DatasetObservationsByMeasureUnitInfoResult` for pivoted multi measure dataset.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "pivoted-multi-measure-dataset"
        / "qb-id-10003.csv-metadata.json"
    )
    data_cube_repository = get_data_cube_repository(csvw_metadata_json_path)

    (dataset, qube_components, csv_url) = get_arguments_qb_dataset(data_cube_repository)

    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        data_cube_repository,
        dataset,
        csv_url,
        qube_components,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_pivoted_multi_measure,
    )


def test_get_concepts_hierarchy_info_hierarchy_with_depth_of_one():
    """
    Should produce the expected tree structure for the given codelist.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    code_list_repository = get_code_list_repository(csvw_metadata_json_path)

    (dataset, csv_url) = _get_arguments_skos_codelist(code_list_repository)

    result_code_list_cols = (
        code_list_repository.csvw_repository.get_column_definitions_for_csv(csv_url)
    )
    result_primary_key_col_names_by_csv_url = select_primary_key_col_names_by_csv_url(
        code_list_repository.csvw_repository.rdf_graph, csv_url
    )

    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols, CodelistPropertyUrl.SkosBroader
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols, CodelistPropertyUrl.RDFLabel
    )
    unique_identifier = get_codelist_col_title_from_col_name(
        result_code_list_cols,
        result_primary_key_col_names_by_csv_url[0].value,
    )

    result = get_concepts_hierarchy_info(
        dataset, parent_notation_col_name, label_col_name, unique_identifier
    )

    assert isinstance(result.tree, Tree)
    assert result.tree.depth() == 1
    assert len(result.tree.all_nodes_itr()) == 7


def test_get_concepts_hierarchy_info_hierarchy_with_depth_more_than_one():
    """
    Should produce the expected tree structure for the given codelist.
    """
    csvw_metadata_json_path = _test_case_base_dir / "itis-industry.csv-metadata.json"
    code_list_repository = get_code_list_repository(csvw_metadata_json_path)

    (dataset, csv_url) = _get_arguments_skos_codelist(code_list_repository)

    result_code_list_cols = (
        code_list_repository.csvw_repository.get_column_definitions_for_csv(csv_url)
    )
    result_primary_key_col_names_by_csv_url = select_primary_key_col_names_by_csv_url(
        code_list_repository.csvw_repository.rdf_graph, csv_url
    )

    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols, CodelistPropertyUrl.SkosBroader
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols, CodelistPropertyUrl.RDFLabel
    )
    unique_identifier = get_codelist_col_title_from_col_name(
        result_code_list_cols,
        result_primary_key_col_names_by_csv_url[0].value,
    )

    result = get_concepts_hierarchy_info(
        dataset, parent_notation_col_name, label_col_name, unique_identifier
    )

    assert isinstance(result.tree, Tree)
    assert result.tree.depth() == 2
    assert len(result.tree.all_nodes_itr()) == 10
