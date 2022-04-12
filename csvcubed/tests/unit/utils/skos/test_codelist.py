from pathlib import Path

from pandas import DataFrame
from treelib import Tree

from csvcubed.cli.inspect.inspectdatasetmanager import load_csv_to_dataframe
from csvcubed.cli.inspect.inspectsparqlmanager import (
    select_codelist_cols_by_dataset_url,
    select_codelist_dataset_url,
)
from csvcubed.cli.inspect.metadataprocessor import MetadataProcessor
from csvcubed.utils.skos.codelist import (
    CodelistPropertyUrl,
    build_concepts_hierarchy_tree,
    get_codelist_col_title_by_property_url,
)
from tests.unit.test_baseunit import get_test_cases_dir

_test_case_base_dir = get_test_cases_dir() / "cli" / "inspect"


def test_get_codelist_col_title_by_property_url_label():
    """
    Should return the correct column title for the property URI of type rdfs:label.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFLabel
    )

    assert label_col_name == "Label"


def test_get_codelist_col_title_by_property_url_notation():
    """
    Should return the correct column title for the property URI of type skos:notation.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosNotation
    )

    assert notation_col_name == "Notation"


def test_get_codelist_col_title_by_property_url_parent_notation():
    """
    Should return the correct column title for the property URI of type skos:broader.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosBroader
    )

    assert parent_notation_col_name == "Parent Notation"


def test_get_codelist_col_title_by_property_url_sort_priority():
    """
    Should return the correct column title for the property URI of type rdfs:label.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    sort_priority_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SortPriority
    )

    assert sort_priority_col_name == "Sort Priority"


def test_get_codelist_col_title_by_property_url_rdfs_comment():
    """
    Should return the correct column title for the property URI of type rdfs:label.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    comment_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFsComment
    )

    assert comment_col_name == "Description"


def test_get_codelist_col_title_by_property_url_rdfs_type():
    """
    Should return the correct column title for the property URI of type rdfs:label.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url

    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )
    type_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFType
    )

    assert type_col_name is None


def test_build_concepts_hierarchy_tree_of_depth_one():
    """
    Should return the expected Tree for the concepts with hierarchical depth of one.
    """
    csvw_metadata_json_path = (
        _test_case_base_dir
        / "multi-unit_multi-measure"
        / "alcohol-content.csv-metadata.json"
    )
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url
    dataset: DataFrame = load_csv_to_dataframe(
        csvw_metadata_json_path, Path(dataset_url)
    )
    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )

    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosBroader
    )
    notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosNotation
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFLabel
    )
    concepts_tree = build_concepts_hierarchy_tree(
        dataset, parent_notation_col_name, label_col_name, notation_col_name
    )

    assert isinstance(concepts_tree, Tree)
    assert concepts_tree.depth() == 1
    assert len(concepts_tree.all_nodes_itr()) == 7


def test_build_concepts_hierarchy_tree_of_depth_more_than_one():
    """
    Should return the expected Tree for the concepts with hierarchical depth of more than one.
    """
    csvw_metadata_json_path = _test_case_base_dir / "itis-industry.csv-metadata.json"
    metadata_processor = MetadataProcessor(csvw_metadata_json_path)
    csvw_metadata_rdf_graph = metadata_processor.load_json_ld_to_rdflib_graph()
    dataset_url = select_codelist_dataset_url(csvw_metadata_rdf_graph).dataset_url
    dataset: DataFrame = load_csv_to_dataframe(
        csvw_metadata_json_path, Path(dataset_url)
    )
    result_code_list_cols = select_codelist_cols_by_dataset_url(
        csvw_metadata_rdf_graph, dataset_url
    )

    parent_notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosBroader
    )
    notation_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.SkosNotation
    )
    label_col_name = get_codelist_col_title_by_property_url(
        result_code_list_cols.columns, CodelistPropertyUrl.RDFLabel
    )
    concepts_tree = build_concepts_hierarchy_tree(
        dataset, parent_notation_col_name, label_col_name, notation_col_name
    )

    assert isinstance(concepts_tree, Tree)
    assert concepts_tree.depth() == 2
    assert len(concepts_tree.all_nodes_itr()) == 10
