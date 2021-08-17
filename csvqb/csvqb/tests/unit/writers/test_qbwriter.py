import pytest
from copy import deepcopy
import pandas as pd
from rdflib import RDFS, Graph, URIRef, Literal
from sharedmodels.rdf import qb
from typing import List

from csvqb.models.cube import *
from csvqb.models.cube.csvqb.components.arbitraryrdf import (
    TripleFragment,
    RdfSerialisationHint,
)
from csvqb.utils.iterables import first
from csvqb.writers.qbwriter import QbWriter


def _get_standard_cube_for_columns(columns: List[CsvColumn]) -> Cube:
    data = pd.DataFrame(
        {
            "Country": ["Wales", "Scotland", "England", "Northern Ireland"],
            "Observed Value": [101.5, 56.2, 12.4, 77.8],
            "Marker": ["Provisional", "Provisional", "Provisional", "Provisional"],
        }
    )
    metadata: CatalogMetadata = CatalogMetadata("Cube Name")

    return Cube(deepcopy(metadata), data.copy(deep=True), columns)


def _assert_component_defined(
    dataset: qb.DataSet, name: str
) -> qb.ComponentSpecification:
    component = first(
        dataset.structure.components,
        lambda x: str(x.uri) == f"cube-name.csv#component/{name}",
    )
    assert component is not None
    return component


def _assert_component_property_defined(
    component: qb.ComponentSpecification, property_uri: str
) -> None:
    property = first(
        component.componentProperties, lambda x: str(x.uri) == property_uri
    )
    assert property is not None
    return property


empty_cube = Cube(CatalogMetadata("Cube Name"), pd.DataFrame, [])
empty_qbwriter = QbWriter(empty_cube)


def test_structure_defined():
    cube = _get_standard_cube_for_columns(
        [
            QbColumn(
                "Country",
                ExistingQbDimension("http://example.org/dimensions/country"),
            ),
            QbColumn(
                "Marker",
                ExistingQbAttribute("http://example.org/attributes/marker"),
            ),
            QbColumn(
                "Observed Value",
                QbSingleMeasureObservationValue(
                    ExistingQbMeasure("http://example.org/units/some-existing-measure"),
                    ExistingQbUnit("http://example.org/units/some-existing-unit"),
                ),
            ),
        ]
    )

    qbwriter = QbWriter(cube)
    dataset = qbwriter._generate_qb_dataset_dsd_definitions()

    assert dataset is not None

    assert dataset.structure is not None
    assert type(dataset.structure) == qb.DataStructureDefinition

    assert dataset.structure.componentProperties is not None

    _assert_component_defined(dataset, "country")
    _assert_component_defined(dataset, "marker")
    _assert_component_defined(dataset, "some-existing-unit")
    _assert_component_defined(dataset, "some-existing-measure")


def test_generating_concept_uri_template_from_global_concept_scheme_uri():
    """
    Given a globally defined skos:ConceptScheme's URI, generate the URI template for a column which maps the
    column's value to a concept defined inside the concept scheme.
    """
    column = SuppressedCsvColumn("Some Column")
    code_list = ExistingQbCodeList(
        "http://base-uri/concept-scheme/this-concept-scheme-name"
    )

    actual_concept_template_uri = (
        empty_qbwriter._get_default_value_uri_for_code_list_concepts(column, code_list)
    )
    assert (
        "http://base-uri/concept-scheme/this-concept-scheme-name/{+some_column}"
        == actual_concept_template_uri
    )


def test_generating_concept_uri_template_from_local_concept_scheme_uri():
    """
    Given a dataset-local skos:ConceptScheme's URI, generate the URI template for a column which maps the
    column's value to a concept defined inside the concept scheme.
    """
    column = SuppressedCsvColumn("Some Column")
    code_list = ExistingQbCodeList(
        "http://base-uri/dataset-name#scheme/that-concept-scheme-name"
    )

    actual_concept_template_uri = (
        empty_qbwriter._get_default_value_uri_for_code_list_concepts(column, code_list)
    )
    assert (
        "http://base-uri/dataset-name#concept/that-concept-scheme-name/{+some_column}"
        == actual_concept_template_uri
    )


def test_generating_concept_uri_template_from_unexpected_concept_scheme_uri():
    """
    Given a skos:ConceptScheme's URI *that does not follow the global or dataset-local conventions* used in our
    tooling, return the column's value as our best guess at the concept's URI.
    """
    column = SuppressedCsvColumn("Some Column")
    code_list = ExistingQbCodeList(
        "http://base-uri/dataset-name#codes/that-concept-scheme-name"
    )

    actual_concept_template_uri = (
        empty_qbwriter._get_default_value_uri_for_code_list_concepts(column, code_list)
    )
    assert "{+some_column}" == actual_concept_template_uri


def test_default_property_value_uris_existing_dimension_column():
    """
    When an existing dimension is used, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        ExistingQbDimension("http://base-uri/dimensions/existing-dimension"),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "http://base-uri/dimensions/existing-dimension" == default_property_uri
    assert "{+some_column}" == default_value_uri


def test_default_property_value_uris_new_dimension_column_without_code_list():
    """
    When a new dimension is defined without a code list, we can provide the `propertyUrl`,
    but we cannot guess the `valueUrl`.
    """
    column = QbColumn("Some Column", NewQbDimension("Some New Dimension"))
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "cube-name.csv#dimension/some-new-dimension" == default_property_uri
    assert "{+some_column}" == default_value_uri


def test_default_property_value_uris_new_dimension_column_with_code_list():
    """
    When an new dimension is defined with a code list, we can provide the `propertyUrl` and the `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        NewQbDimension(
            "Some New Dimension",
            code_list=ExistingQbCodeList("http://base-uri/concept-scheme/this-scheme"),
        ),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "cube-name.csv#dimension/some-new-dimension" == default_property_uri
    assert (
        "http://base-uri/concept-scheme/this-scheme/{+some_column}" == default_value_uri
    )


def test_default_property_value_uris_existing_attribute_existing_values():
    """
    When an existing attribute is used, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        ExistingQbAttribute("http://base-uri/attributes/existing-attribute"),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "http://base-uri/attributes/existing-attribute" == default_property_uri
    assert "{+some_column}" == default_value_uri


def test_default_property_value_uris_existing_attribute_new_values():
    """
    When an existing attribute is used, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        ExistingQbAttribute(
            "http://base-uri/attributes/existing-attribute",
            new_attribute_values=[NewQbAttributeValue("Some Attribute Value")],
        ),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "http://base-uri/attributes/existing-attribute" == default_property_uri
    assert "cube-name.csv#attribute/some-column/{+some_column}" == default_value_uri


def test_default_property_value_uris_new_attribute_existing_values():
    """
    When a new attribute is defined, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
    """
    column = QbColumn("Some Column", NewQbAttribute("This New Attribute"))
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "cube-name.csv#attribute/this-new-attribute" == default_property_uri
    assert "{+some_column}" == default_value_uri


def test_default_property_value_uris_new_attribute_new_values():
    """
    When a new attribute is defined, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        NewQbAttribute(
            "This New Attribute",
            new_attribute_values=[NewQbAttributeValue("Something")],
        ),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "cube-name.csv#attribute/this-new-attribute" == default_property_uri
    assert (
        "cube-name.csv#attribute/this-new-attribute/{+some_column}" == default_value_uri
    )


def test_default_property_value_uris_multi_units_all_new():
    """
    When a QbMultiUnits component is defined using only new/locally defined units, we can provide the
    `propertyUrl` and the `valueUrl`.
    """
    column = QbColumn("Some Column", QbMultiUnits([NewQbUnit("Some New Unit")]))
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert (
        "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        == default_property_uri
    )
    assert "cube-name.csv#unit/{+some_column}" == default_value_uri


def test_default_property_value_uris_multi_units_all_existing():
    """
    When a QbMultiUnits component is defined using just existing units, we can provide the `propertyUrl` and
    `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        QbMultiUnits([ExistingQbUnit("http://base-uri/units/existing-unit")]),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert (
        "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        == default_property_uri
    )
    assert "{+some_column}" == default_value_uri


def test_default_property_value_uris_multi_units_local_and_existing():
    """
    When a QbMultiUnits component is defined using a mixture of existing units and new units, we can't provide
    an appropriate and consistent `valueUrl`.

    An exception is raised when this is attempted.
    """
    column = QbColumn(
        "Some Column",
        QbMultiUnits(
            [
                NewQbUnit("Some New Unit"),
                ExistingQbUnit("http://base-uri/units/existing-unit"),
            ]
        ),
    )
    with pytest.raises(Exception) as exception:

        def fetch_exception():
            empty_qbwriter._get_default_property_value_uris_for_column(column)

        fetch_exception()


def test_default_property_value_uris_multi_measure_all_new():
    """
    When a QbMultiMeasureDimension component is defined using only new/locally defined measures,
    we can provide the `propertyUrl` and the `valueUrl`.
    """
    column = QbColumn(
        "Some Column", QbMultiMeasureDimension([NewQbMeasure("Some New Measure")])
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "http://purl.org/linked-data/cube#measureType" == default_property_uri
    assert "cube-name.csv#measure/{+some_column}" == default_value_uri


def test_default_property_value_uris_multi_measure_all_existing():
    """
    When a QbMultiUnits component is defined using just existing units, we can provide the `propertyUrl` and
    `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        QbMultiMeasureDimension(
            [ExistingQbMeasure("http://base-uri/measures/existing-measure")]
        ),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert "http://purl.org/linked-data/cube#measureType" == default_property_uri
    assert "{+some_column}" == default_value_uri


def test_default_property_value_uris_multi_measure_local_and_existing():
    """
    When a QbMultiUnits component is defined using a mixture of existing units and new units, we can't provide
    an appropriate and consistent `valueUrl`.

    An exception is raised when this is attempted.
    """
    column = QbColumn(
        "Some Column",
        QbMultiMeasureDimension(
            [
                NewQbMeasure("Some New Measure"),
                ExistingQbMeasure("http://base-uri/measures/existing-measure"),
            ]
        ),
    )

    with pytest.raises(Exception) as exception:

        def fetch_exception():
            empty_qbwriter._get_default_property_value_uris_for_column(column)

        fetch_exception()


def test_default_property_value_uris_single_measure_obs_val():
    """
    There should be no `propertyUrl` or `valueUrl` for a `QbSingleMeasureObservationValue`.
    """
    column = QbColumn(
        "Some Column",
        QbSingleMeasureObservationValue(
            NewQbUnit("New Unit"), NewQbMeasure("New Qb Measure")
        ),
    )
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert default_property_uri is None
    assert default_value_uri is None


def test_default_property_value_uris_multi_measure_obs_val():
    """
    There should be no `propertyUrl` or `valueUrl` for a `QbMultiMeasureObservationValue`.
    """
    column = QbColumn("Some Column", QbMultiMeasureObservationValue())
    (
        default_property_uri,
        default_value_uri,
    ) = empty_qbwriter._get_default_property_value_uris_for_column(column)
    assert default_property_uri is None
    assert default_value_uri is None


def test_csv_col_definition_default_property_value_urls():
    """
    When configuring a CSV-W column definition, if the user has not specified an `output_uri_template`
    against the `QbColumn` then the `propertyUrl` and `valueUrl`s should both be populated by the default
    values inferred from the component.
    """
    column = QbColumn("Some Column", QbMultiUnits([NewQbUnit("Some Unit")]))
    csv_col = empty_qbwriter._generate_csvqb_column(column)
    assert (
        "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        == csv_col["propertyUrl"]
    )
    assert "cube-name.csv#unit/{+some_column}" == csv_col["valueUrl"]


def test_csv_col_definition_output_uri_template_override():
    """
    When configuring a CSV-W column definition, if the user has specified an `output_uri_template` against the
    `QbColumn` then this should end up as the resulting CSV-W column's `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        ExistingQbDimension("http://base-uri/dimensions/some-dimension"),
        output_uri_template="http://base-uri/some-alternative-output-uri/{+some_column}",
    )
    csv_col = empty_qbwriter._generate_csvqb_column(column)
    assert "http://base-uri/dimensions/some-dimension" == csv_col["propertyUrl"]
    assert (
        "http://base-uri/some-alternative-output-uri/{+some_column}"
        == csv_col["valueUrl"]
    )


def test_csv_col_definition():
    """
    Test basic configuration of a CSV-W column definition.
    """
    column = QbColumn(
        "Some Column",
        ExistingQbDimension("http://base-uri/dimensions/some-dimension"),
    )
    csv_col = empty_qbwriter._generate_csvqb_column(column)
    assert "suppressOutput" not in csv_col
    assert "Some Column" == csv_col["titles"]
    assert "some_column" == csv_col["name"]
    assert "http://base-uri/dimensions/some-dimension" == csv_col["propertyUrl"]
    assert "{+some_column}" == csv_col["valueUrl"]


def test_csv_col_definition_suppressed():
    """
    Test basic configuration of a *suppressed* CSV-W column definition.
    """
    column = SuppressedCsvColumn("Some Column")
    csv_col = empty_qbwriter._generate_csvqb_column(column)
    assert csv_col["suppressOutput"]
    assert "Some Column" == csv_col["titles"]
    assert "some_column" == csv_col["name"]
    assert "propertyUrl" not in csv_col
    assert "valueUrl" not in csv_col


def test_virtual_columns_generated_for_single_obs_val():
    """
    Ensure that the virtual columns generated for a `QbSingleMeasureObservationValue`'s unit and measure are
    correct.
    """
    obs_val = QbSingleMeasureObservationValue(
        NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
    )
    virtual_columns = empty_qbwriter._generate_virtual_columns_for_obs_val(obs_val)

    virt_unit = first(virtual_columns, lambda x: x["name"] == "virt_unit")
    assert virt_unit is not None
    assert virt_unit["virtual"]
    assert (
        "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        == virt_unit["propertyUrl"]
    )
    assert "cube-name.csv#unit/some-unit" == virt_unit["valueUrl"]

    virt_measure = first(virtual_columns, lambda x: x["name"] == "virt_measure")
    assert virt_measure is not None
    assert virt_measure["virtual"]
    assert "http://purl.org/linked-data/cube#measureType" == virt_measure["propertyUrl"]
    assert "cube-name.csv#measure/some-measure" == virt_measure["valueUrl"]


def test_virtual_columns_generated_for_multi_meas_obs_val():
    """
    Ensure that the virtual column generated for a `QbMultiMeasureObservationValue`'s unit and measure are
    correct.
    """
    obs_val = QbMultiMeasureObservationValue(unit=NewQbUnit("Some Unit"))
    virtual_columns = empty_qbwriter._generate_virtual_columns_for_obs_val(obs_val)

    virt_unit = first(virtual_columns, lambda x: x["name"] == "virt_unit")
    assert virt_unit is not None
    assert virt_unit["virtual"]
    assert (
        "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure"
        == virt_unit["propertyUrl"]
    )
    assert "cube-name.csv#unit/some-unit" == virt_unit["valueUrl"]


def test_about_url_generation():
    """
    Ensuring that when an aboutUrl is defined for a non-multimeasure cube, the resulting URL
    is built in the order in which dimensions appear in the cube.
    """
    data = pd.DataFrame(
        {
            "Existing Dimension": ["A", "B", "C"],
            "Local Dimension": ["D", "E", "F"],
            "Value": [2, 2, 2],
        }
    )

    metadata = CatalogMetadata("Some Dataset")
    columns = [
        QbColumn(
            "Existing Dimension",
            ExistingQbDimension("https://example.org/dimensions/existing_dimension"),
        ),
        QbColumn(
            "Local Dimension",
            NewQbDimension.from_data("Name of New Dimension", data["Local Dimension"]),
        ),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                ExistingQbMeasure("http://example.com/measures/existing_measure"),
                NewQbUnit("New Unit"),
            ),
        ),
    ]

    cube = Cube(metadata, data, columns)

    actual_about_url = QbWriter(cube)._get_about_url()
    expected_about_url = "some-dataset.csv#obs/{+existing_dimension}/{+local_dimension}"
    assert actual_about_url == expected_about_url


def test_about_url_generation_with_multiple_measures():
    """
    Ensuring that when an aboutUrl is defined for a multi-measure cube, the resulting URL
    is built in the order in which dimensions appear in the cube except for the multi-measure
    dimensions which are appended to the end of the URL.
    """
    data = pd.DataFrame(
        {
            "Measure": ["People", "Children", "Adults"],
            "Existing Dimension": ["A", "B", "C"],
            "Value": [2, 2, 2],
            "Local Dimension": ["D", "E", "F"],
            "Units": ["Percent", "People", "People"],
        }
    )

    metadata = CatalogMetadata("Some Dataset")
    columns = [
        QbColumn(
            "Measure", QbMultiMeasureDimension.new_measures_from_data(data["Measure"])
        ),
        QbColumn(
            "Existing Dimension",
            ExistingQbDimension("https://example.org/dimensions/existing_dimension"),
        ),
        QbColumn(
            "Local Dimension",
            NewQbDimension.from_data("Name of New Dimension", data["Local Dimension"]),
        ),
        QbColumn("Value", QbMultiMeasureObservationValue("number")),
        QbColumn("Units", QbMultiUnits.new_units_from_data(data["Units"])),
    ]

    cube = Cube(metadata, data, columns)

    actual_about_url = QbWriter(cube)._get_about_url()
    expected_about_url = (
        "some-dataset.csv#obs/{+existing_dimension}/{+local_dimension}/{+measure}"
    )
    assert actual_about_url == expected_about_url


def test_arbitrary_rdf_serialisation_existing_attribute():
    """
    Test that when arbitrary RDF is specified against an Existing Attribute, it is serialised correctly.
    """
    data = pd.DataFrame(
        {
            "Existing Dimension": ["A", "B", "C"],
            "Value": [1, 2, 3],
            "Existing Attribute": ["Provisional", "Final", "Provisional"],
        }
    )

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "Existing Dimension",
                ExistingQbDimension(
                    "https://example.org/dimensions/existing_dimension"
                ),
            ),
            QbColumn(
                "Value",
                QbSingleMeasureObservationValue(
                    NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
                ),
            ),
            QbColumn(
                "Existing Attribute",
                ExistingQbAttribute(
                    "http://some-existing-attribute-uri",
                    arbitrary_rdf=[
                        TripleFragment(RDFS.label, "Existing Attribute Component")
                    ],
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    dataset = qb_writer._generate_qb_dataset_dsd_definitions()
    graph = dataset.to_graph(Graph())

    assert (
        URIRef("some-dataset.csv#component/existing-attribute"),
        RDFS.label,
        Literal("Existing Attribute Component"),
    ) in graph


def test_arbitrary_rdf_serialisation_new_attribute():
    """
    Test that when arbitrary RDF is specified against a New Attribute, it is serialised correctly.
    """
    data = pd.DataFrame(
        {
            "Existing Dimension": ["A", "B", "C"],
            "Value": [1, 2, 3],
            "New Attribute": ["Provisional", "Final", "Provisional"],
        }
    )

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "Existing Dimension",
                ExistingQbDimension(
                    "https://example.org/dimensions/existing_dimension"
                ),
            ),
            QbColumn(
                "Value",
                QbSingleMeasureObservationValue(
                    NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
                ),
            ),
            QbColumn(
                "Existing Attribute",
                NewQbAttribute.from_data(
                    "New Attribute",
                    data["New Attribute"],
                    arbitrary_rdf=[
                        TripleFragment(RDFS.label, "New Attribute Property"),
                        TripleFragment(
                            RDFS.label,
                            "New Attribute Component",
                            RdfSerialisationHint.Component,
                        ),
                    ],
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    dataset = qb_writer._generate_qb_dataset_dsd_definitions()
    graph = dataset.to_graph(Graph())

    assert (
        URIRef("some-dataset.csv#attribute/new-attribute"),
        RDFS.label,
        Literal("New Attribute Property"),
    ) in graph

    assert (
        URIRef("some-dataset.csv#component/new-attribute"),
        RDFS.label,
        Literal("New Attribute Component"),
    ) in graph


def test_arbitrary_rdf_serialisation_existing_dimension():
    """
    Test that when arbitrary RDF is specified against an Existing Dimension, it is serialised correctly.
    """
    data = pd.DataFrame(
        {
            "Existing Dimension": ["A", "B", "C"],
            "Value": [1, 2, 3],
            "Existing Attribute": ["Provisional", "Final", "Provisional"],
        }
    )

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "Existing Dimension",
                ExistingQbDimension(
                    "https://example.org/dimensions/existing_dimension",
                    arbitrary_rdf=[
                        TripleFragment(RDFS.label, "Existing Dimension Component")
                    ],
                ),
            ),
            QbColumn(
                "Value",
                QbSingleMeasureObservationValue(
                    NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    dataset = qb_writer._generate_qb_dataset_dsd_definitions()
    graph = dataset.to_graph(Graph())

    assert (
        URIRef("some-dataset.csv#component/existing-dimension"),
        RDFS.label,
        Literal("Existing Dimension Component"),
    ) in graph


def test_arbitrary_rdf_serialisation_new_dimension():
    """
    Test that when arbitrary RDF is specified against a new dimension, it is serialised correctly.
    """
    data = pd.DataFrame({"New Dimension": ["A", "B", "C"], "Value": [1, 2, 3]})

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data(
                    "Some Dimension",
                    data["New Dimension"],
                    arbitrary_rdf=[
                        TripleFragment(RDFS.label, "New Dimension Property"),
                        TripleFragment(
                            RDFS.label,
                            "New Dimension Component",
                            RdfSerialisationHint.Component,
                        ),
                    ],
                ),
            ),
            QbColumn(
                "Value",
                QbSingleMeasureObservationValue(
                    NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    dataset = qb_writer._generate_qb_dataset_dsd_definitions()
    graph = dataset.to_graph(Graph())

    assert (
        URIRef("some-dataset.csv#dimension/some-dimension"),
        RDFS.label,
        Literal("New Dimension Property"),
    ) in graph

    assert (
        URIRef("some-dataset.csv#component/some-dimension"),
        RDFS.label,
        Literal("New Dimension Component"),
    ) in graph


def test_arbitrary_rdf_serialisation_existing_dimension():
    """
    Test that when arbitrary RDF is specified against an Existing Dimension, it is serialised correctly.
    """
    data = pd.DataFrame(
        {
            "Existing Dimension": ["A", "B", "C"],
            "Value": [1, 2, 3],
            "Existing Attribute": ["Provisional", "Final", "Provisional"],
        }
    )

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "Existing Dimension",
                NewQbDimension.from_data(
                    "Existing Dimension", data["Existing Dimension"]
                ),
            ),
            QbColumn(
                "Value",
                QbSingleMeasureObservationValue(
                    ExistingQbMeasure(
                        "http://some/uri/existing-measure-uri",
                        arbitrary_rdf=[
                            TripleFragment(RDFS.label, "Existing Measure Component")
                        ],
                    ),
                    NewQbUnit("Some Unit"),
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    dataset = qb_writer._generate_qb_dataset_dsd_definitions()
    graph = dataset.to_graph(Graph())

    assert (
        URIRef("some-dataset.csv#component/existing-measure-uri"),
        RDFS.label,
        Literal("Existing Measure Component"),
    ) in graph


def test_arbitrary_rdf_serialisation_new_measure():
    """
    Test that when arbitrary RDF is specified against a new measure, it is serialised correctly.
    """
    data = pd.DataFrame({"New Dimension": ["A", "B", "C"], "Value": [1, 2, 3]})

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data("Some Dimension", data["New Dimension"]),
            ),
            QbColumn(
                "Value",
                QbSingleMeasureObservationValue(
                    NewQbMeasure(
                        "Some Measure",
                        arbitrary_rdf=[
                            TripleFragment(RDFS.label, "New Measure Property"),
                            TripleFragment(
                                RDFS.label,
                                "New Measure Component",
                                RdfSerialisationHint.Component,
                            ),
                        ],
                    ),
                    NewQbUnit("Some Unit"),
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    dataset = qb_writer._generate_qb_dataset_dsd_definitions()
    graph = dataset.to_graph(Graph())

    assert (
        URIRef("some-dataset.csv#measure/some-measure"),
        RDFS.label,
        Literal("New Measure Property"),
    ) in graph

    assert (
        URIRef("some-dataset.csv#component/some-measure"),
        RDFS.label,
        Literal("New Measure Component"),
    ) in graph


# TODO: Add attribute and unit RDF serialisation tests here in Issue #79.

if __name__ == "__main__":
    pytest.main()
