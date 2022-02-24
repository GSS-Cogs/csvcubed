"""
Inspect SPARQL Queries
----------------------

Collection of SPARQL queries used in the inspect cli.
"""

from enum import Enum
from pathlib import Path
from typing import List
from csvcubed.utils.file import get_root_dir_level

from rdflib import Graph, URIRef
from rdflib.query import ResultRow

from csvcubed.utils.sparql import ask, select


class SPARQLQueryFileName(Enum):
    """
    The file name of sparql query.
    """

    ASK_IS_CODELIST = "ask_is_codelist"

    ASK_IS_QB_DATASET = "ask_is_qb_dataset"

    SELECT_CATALOG_METADATA = "select_catalog_metadata"

    SELECT_DSD_DATASETLABEL_AND_URI = "select_dsd_datasetlabel_and_uri"

    SELECT_DSD_QUBE_COMPONENTS = "select_dsd_qube_components"

    SELECT_COLS_W_SUPPRESS_OUTPUT = "select_cols_w_suppress_output"

    SELECT_CODE_LISTS_AND_COLS = "select_code_lists_and_cols"


def _get_query_string_from_file(queryType: SPARQLQueryFileName) -> str:
    """
    Read the sparql query string from sparql file for the given query type.

    Member of :file:`./inspectsparqlmanager.py`

    :return: `bool` - String containing the sparql query.
    """
    try:
        file_path = (
            get_root_dir_level("pyproject.toml", Path(__file__))
            / "csvcubed"
            / "cli"
            / "inspect"
            / "inspect_sparql_queries"
            / (queryType.value + ".sparql")
        )
        with open(
            file_path,
            "r",
        ) as f:
            return f.read()
    except Exception as ex:
        raise Exception("An error occured while reading sparql query") from ex


def ask_is_csvw_code_list(rdf_graph: Graph) -> bool:
    """
    Queries whether the given rdf is a code list (i.e. skos:ConceptScheme).

    Member of :file:`./inspectsparqlmanager.py`

    :return: `bool` - Boolean specifying whether the rdf is code list (true) or not (false).
    """
    return ask(
        _get_query_string_from_file(SPARQLQueryFileName.ASK_IS_CODELIST),
        rdf_graph,
    )


def ask_is_csvw_qb_dataset(rdf_graph: Graph) -> bool:
    """
    Queries whether the given rdf is a qb dataset (i.e. qb:Dataset).

    Member of :file:`./inspectsparqlmanager.py`

    :return: `bool` - Boolean specifying whether the rdf is code list (true) or not (false).
    """
    return ask(
        _get_query_string_from_file(SPARQLQueryFileName.ASK_IS_QB_DATASET),
        rdf_graph,
    )


def select_csvw_catalog_metadata(rdf_graph: Graph) -> ResultRow:
    """
    Queries catalog metadata such as title, label, issued date/time, modified data/time, etc.

    Member of :file:`./inspectsparqlmanager.py`

    :return: `List[ResultRow]` - List containing the results. The expected length of this list for this query is 1.
    """
    results: List[ResultRow] = select(
        _get_query_string_from_file(SPARQLQueryFileName.SELECT_CATALOG_METADATA),
        rdf_graph,
    )

    if len(results) != 1:
        raise Exception(f"Expected 1 dcat:Dataset record, found {len(results)}")

    return results[0]


def select_csvw_dsd_dataset_label_and_dsd_def_uri(rdf_graph: Graph) -> ResultRow:
    """
    Queries data structure definition dataset label and uri.

    Member of :file:`./inspectsparqlmanager.py`

    :return: `List[ResultRow]` - List containing the results. The expected length of this list for this query is 1.
    """
    results: List[ResultRow] = select(
        _get_query_string_from_file(
            SPARQLQueryFileName.SELECT_DSD_DATASETLABEL_AND_URI
        ),
        rdf_graph,
    )

    if len(results) != 1:
        raise Exception(f"Expected 1 dcat:Dataset record, found {len(results)}")

    return results[0]


def select_csvw_dsd_qube_components(rdf_graph: Graph, dsd_uri: str) -> List[ResultRow]:
    """
    Queries the list of qube components.

    Member of :file:`./inspectsparqlmanager.py`

    :return: `List[ResultRow]` - List containing the results.
    """
    return select(
        _get_query_string_from_file(SPARQLQueryFileName.SELECT_DSD_QUBE_COMPONENTS),
        rdf_graph,
        init_bindings={"dsd_uri": URIRef(dsd_uri)},
    )


def select_cols_w_supress_output(rdf_graph: Graph) -> List[ResultRow]:
    """
    Queries the columns with suppress output is true.

    Member of :file:`./inspectsparqlmanager.py`

    :return: `List[ResultRow]` - List containing the results.
    """
    return select(
        _get_query_string_from_file(SPARQLQueryFileName.SELECT_COLS_W_SUPPRESS_OUTPUT),
        rdf_graph,
    )


def select_dsd_code_list_and_cols(rdf_graph: Graph, dsd_uri: str) -> List[ResultRow]:
    """
    Queries code lists and columns in the data cube.

    Member of :file:`./inspectsparqlmanager.py`

    :return: `List[ResultRow]` - List containing the results.
    """
    return select(
        _get_query_string_from_file(SPARQLQueryFileName.SELECT_CODE_LISTS_AND_COLS),
        rdf_graph,
        init_bindings={"dsd_uri": URIRef(dsd_uri)},
    )
