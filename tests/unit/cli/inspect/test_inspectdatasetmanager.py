from csvcubed.cli.inspect.metadatainputvalidator import CSVWType
from csvcubed.utils.skos.codelist import (
    CodelistPropertyUrl,
    get_codelist_col_title_by_property_url,
)
import pytest
import numpy as np
from pandas import DataFrame
from pandas.util.testing import assert_frame_equal
from typing import List, Tuple

from pathlib import Path
from rdflib import Graph
from treelib import Node, Tree

from csvcubed.cli.inspect.inspectsparqlmanager import (
    select_codelist_cols_by_dataset_url,
    select_codelist_dataset_url,
    select_csvw_catalog_metadata,
    select_csvw_dsd_dataset_label_and_dsd_def_uri,
    select_csvw_dsd_qube_components,
    select_qb_dataset_url,
)
from csvcubed.models.inspectsparqlresults import (
    DSDLabelURIResult,
    QubeComponentResult,
    QubeComponentsResult,
)
from csvcubed.cli.inspect.inspectdatasetmanager import (
    get_concepts_hierarchy_info,
    get_dataset_observations_info,
    get_dataset_val_counts_info,
    get_measure_col_name_from_dsd,
    get_single_measure_from_dsd,
    get_unit_col_name_from_dsd,
    load_csv_to_dataframe,
)
from csvcubed.cli.inspect.metadataprocessor import MetadataProcessor
from csvcubed.models.inspectdataframeresults import (
    DatasetObservationsByMeasureUnitInfoResult,
    DatasetObservationsInfoResult,
)
from csvcubed.utils.csvdataset import (
    transform_dataset_to_canonical_shape,
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

_expected_by_measure_and_unit_val_counts_df_single_unit_single_measure = DataFrame(
    [
        {
            "Measure": "energy-consumption",
            "Unit": "millions-of-tonnes-of-oil-equivalent",
            0: 286,
        }
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_single_unit_multi_measure = DataFrame(
    [
        {
            "Measure": "emissions-ar4-gwps",
            "Unit": "MtCO2e",
            0: 49765,
        },
        {
            "Measure": "emissions-ar5-gwps",
            "Unit": "MtCO2e",
            0: 49765,
        },
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_multi_unit_single_measure = DataFrame(
    [
        {
            "Measure": "gas emissions(gwp-ar4)",
            "Unit": "millions of tonnes of carbon dioxide (mt co2)",
            0: 41508,
        }
    ]
).replace("", np.NAN)

_expected_by_measure_and_unit_val_counts_df_multi_unit_multi_measure = DataFrame(
    [
        {"Measure": "alcohol-duty-receipts", "Unit": "gbp-million", 0: 314},
        {"Measure": "beer-duty-receipts", "Unit": "gbp-million", 0: 314},
        {"Measure": "cider-duty-receipts", "Unit": "gbp-million", 0: 314},
        {"Measure": "clearances", "Unit": "hectolitres", 0: 4710},
        {"Measure": "clearances", "Unit": "hectolitres-of-alcohol", 0: 942},
        {"Measure": "clearances", "Unit": "thousand-hectolitres", 0: 1256},
        {"Measure": "clearances-of-alcohol", "Unit": "hectolitres", 0: 942},
        {
            "Measure": "clearances-of-alcohol",
            "Unit": "thousand-hectolitres",
            0: 314,
        },
        {
            "Measure": "production-volume",
            "Unit": "thousand-hectolitres",
            0: 314,
        },
        {
            "Measure": "production-volume-alcohol",
            "Unit": "hectolitres",
            0: 314,
        },
        {
            "Measure": "production-volume-alcohol",
            "Unit": "thousand-hectolitres",
            0: 314,
        },
        {"Measure": "spirits-duty-receipts", "Unit": "gbp-million", 0: 314},
        {"Measure": "wine-duty-receipts", "Unit": "gbp-million", 0: 314},
    ]
).replace("", np.NAN)


def _get_arguments_qb_dataset(
    csvw_metadata_rdf_graph: Graph, csvw_metadata_json_path: Path
) -> Tuple[DataFrame, List[QubeComponentResult], str, str]:
    """
    Produces the dataset, qube components and dsd uri arguments for qb:dataset.
    """
    dataset_uri = select_csvw_catalog_metadata(csvw_metadata_rdf_graph).dataset_uri
    dataset_url = select_qb_dataset_url(
        csvw_metadata_rdf_graph, dataset_uri
    ).dataset_url

    dataset: DataFrame = load_csv_to_dataframe(
        csvw_metadata_json_path, Path(dataset_url)
    )

    dsd_uri = select_csvw_dsd_dataset_label_and_dsd_def_uri(
        csvw_metadata_rdf_graph
    ).dsd_uri

    qube_components = select_csvw_dsd_qube_components(
        csvw_metadata_rdf_graph, dsd_uri, csvw_metadata_json_path
    ).qube_components

    return (dataset, qube_components, dsd_uri, dataset_url)


def _get_arguments_skos_codelist(
    csvw_metadata_rdf_graph: Graph, csvw_metadata_json_path: Path
) -> Tuple[DataFrame, str]:
    """
    Produces the dataset, qube components and dsd uri arguments for skos:codelist.
    """
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    dataset: DataFrame = load_csv_to_dataframe(
        csvw_metadata_json_path, Path(dataset_url)
    )
    return (dataset, dataset_url)


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
        dataset, CSVWType.QbDataSet
    )

    assert result.num_of_observations == 11
    assert result.num_of_duplicates == 2
    assert_frame_equal(result.dataset_head, _expected_dataframe.head(n=10))
    assert_frame_equal(result.dataset_tail, _expected_dataframe.tail(n=10))


def test_get_measure_col_name_from_dsd_measure_col_present():
    """
    Should return the measure column name when measure col is present.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-bulletin.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    result: DSDLabelURIResult = select_csvw_dsd_dataset_label_and_dsd_def_uri(
        csvw_metadata_rdf_graph
    )
    result_qube_components: QubeComponentsResult = select_csvw_dsd_qube_components(
        csvw_metadata_rdf_graph, result.dsd_uri, csvw_metadata_json_path
    )

    measure_col = get_measure_col_name_from_dsd(result_qube_components.qube_components)

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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    result: DSDLabelURIResult = select_csvw_dsd_dataset_label_and_dsd_def_uri(
        csvw_metadata_rdf_graph
    )
    result_qube_components: QubeComponentsResult = select_csvw_dsd_qube_components(
        csvw_metadata_rdf_graph, result.dsd_uri, csvw_metadata_json_path
    )

    measure_col = get_measure_col_name_from_dsd(result_qube_components.qube_components)

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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    result: DSDLabelURIResult = select_csvw_dsd_dataset_label_and_dsd_def_uri(
        csvw_metadata_rdf_graph
    )
    result_qube_components: QubeComponentsResult = select_csvw_dsd_qube_components(
        csvw_metadata_rdf_graph, result.dsd_uri, csvw_metadata_json_path
    )

    unit_col = get_unit_col_name_from_dsd(result_qube_components.qube_components)

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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    result: DSDLabelURIResult = select_csvw_dsd_dataset_label_and_dsd_def_uri(
        csvw_metadata_rdf_graph
    )
    result_qube_components: QubeComponentsResult = select_csvw_dsd_qube_components(
        csvw_metadata_rdf_graph, result.dsd_uri, csvw_metadata_json_path
    )

    unit_col = get_unit_col_name_from_dsd(result_qube_components.qube_components)

    assert unit_col is None


def test_get_single_measure_label_from_dsd():
    """
    Should return the correct measure label.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_single-measure"
        / "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2019.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    result: DSDLabelURIResult = select_csvw_dsd_dataset_label_and_dsd_def_uri(
        csvw_metadata_rdf_graph
    )
    result_qube_components: QubeComponentsResult = select_csvw_dsd_qube_components(
        csvw_metadata_rdf_graph, result.dsd_uri, csvw_metadata_json_path
    )

    measure_col = get_measure_col_name_from_dsd(result_qube_components.qube_components)
    assert measure_col is None

    result_measure = get_single_measure_from_dsd(
        result_qube_components.qube_components, csvw_metadata_json_path
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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    (dataset, qube_components, dsd_uri, _) = _get_arguments_qb_dataset(
        csvw_metadata_rdf_graph, csvw_metadata_json_path
    )
    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        dataset,
        qube_components,
        dsd_uri,
        csvw_metadata_rdf_graph,
        csvw_metadata_json_path,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    _expected_by_measure_and_unit_val_counts_df_multi_unit_multi_measure.rename(
        columns={
            "Measure": measure_col,
            "Unit": unit_col,
        },
        inplace=True,
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
        / "final-uk-greenhouse-gas-emissions-national-statistics-1990-to-2019.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    (dataset, qube_components, dsd_uri, _) = _get_arguments_qb_dataset(
        csvw_metadata_rdf_graph, csvw_metadata_json_path
    )
    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        dataset,
        qube_components,
        dsd_uri,
        csvw_metadata_rdf_graph,
        csvw_metadata_json_path,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    _expected_by_measure_and_unit_val_counts_df_multi_unit_single_measure.rename(
        columns={
            "Measure": measure_col,
            "Unit": unit_col,
        },
        inplace=True,
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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    (dataset, qube_components, dsd_uri, _) = _get_arguments_qb_dataset(
        csvw_metadata_rdf_graph, csvw_metadata_json_path
    )
    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        dataset,
        qube_components,
        dsd_uri,
        csvw_metadata_rdf_graph,
        csvw_metadata_json_path,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    _expected_by_measure_and_unit_val_counts_df_single_unit_multi_measure.rename(
        columns={
            "Measure": measure_col,
            "Unit": unit_col,
        },
        inplace=True,
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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    (dataset, qube_components, dsd_uri, _) = _get_arguments_qb_dataset(
        csvw_metadata_rdf_graph, csvw_metadata_json_path
    )
    (
        canonical_shape_dataset,
        measure_col,
        unit_col,
    ) = transform_dataset_to_canonical_shape(
        dataset,
        qube_components,
        dsd_uri,
        csvw_metadata_rdf_graph,
        csvw_metadata_json_path,
    )

    result: DatasetObservationsByMeasureUnitInfoResult = get_dataset_val_counts_info(
        canonical_shape_dataset, measure_col, unit_col
    )

    _expected_by_measure_and_unit_val_counts_df_single_unit_single_measure.rename(
        columns={
            "Measure": measure_col,
            "Unit": unit_col,
        },
        inplace=True,
    )

    assert result is not None
    assert_frame_equal(
        result.by_measure_and_unit_val_counts_df,
        _expected_by_measure_and_unit_val_counts_df_single_unit_single_measure,
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
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    (dataset, dataset_url) = _get_arguments_skos_codelist(
        csvw_metadata_rdf_graph, csvw_metadata_json_path
    )

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosBroader
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFLabel
    )
    notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosNotation
    )

    result = get_concepts_hierarchy_info(
        dataset, parent_notation_col_name, label_col_name, notation_col_name
    )

    assert isinstance(result.tree, Tree)
    assert result.tree.depth() == 1
    assert len(result.tree.all_nodes_itr()) == 7


def test_get_concepts_hierarchy_info_hierarchy_with_depth_more_than_one():
    """
    Should produce the expected tree structure for the given codelist.
    """
    csvw_metadata_json_path = _test_case_base_dir / "itis-industry.csv-metadata.json"
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()

    (dataset, dataset_url) = _get_arguments_skos_codelist(
        csvw_metadata_rdf_graph, csvw_metadata_json_path
    )

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosBroader
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFLabel
    )
    notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosNotation
    )

    result = get_concepts_hierarchy_info(
        dataset, parent_notation_col_name, label_col_name, notation_col_name
    )

    assert isinstance(result.tree, Tree)
    assert result.tree.depth() == 2
    assert len(result.tree.all_nodes_itr()) == 10
