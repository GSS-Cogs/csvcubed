import unittest
from copy import deepcopy
from typing import List
import pandas as pd
from sharedmodels.rdf import qb

from csvqb.models.cube import *
from csvqb.tests.unit.unittestbase import UnitTestBase
from csvqb.utils.iterables import first
from csvqb.writers import qbwriter


def _get_standard_cube_for_columns(columns: List[CsvColumn]) -> Cube:
    data = pd.DataFrame({
        "Country": ["Wales", "Scotland", "England", "Northern Ireland"],
        "Observed Value": [101.5, 56.2, 12.4, 77.8],
        "Marker": ["Provisional", "Provisional", "Provisional", "Provisional"]
    })
    metadata: CubeMetadata = CubeMetadata("Some qube")

    return Cube(deepcopy(metadata), data.copy(deep=True), columns)


def _assert_component_defined(dataset: qb.DataSet, name: str) -> qb.ComponentSpecification:
    component = first(dataset.structure.components, lambda x: str(x.uri) == f"#component/{name}")
    assert(component is not None)
    return component


def _assert_component_property_defined(component: qb.ComponentSpecification, property_uri: str) -> None:
    property = first(component.componentProperties, lambda x: str(x.uri) == property_uri)
    assert(property is not None)
    return property


class QbWriterTests(UnitTestBase):
    def test_structure_defined(self):
        cube = _get_standard_cube_for_columns([
            QbColumn("Country", ExistingQbDimension("http://example.org/dimensions/country")),
            QbColumn("Marker", ExistingQbAttribute("http://example.org/attributes/marker")),
            QbColumn("Observed Value", QbSingleMeasureObservationValue(
                ExistingQbMeasure("http://example.org/units/some-existing-measure"),
                ExistingQbUnit("http://example.org/units/some-existing-unit")))
        ])

        dataset = qbwriter._generate_qb_dataset_dsd_definitions(cube)

        self.assertIsNotNone(dataset)

        self.assertIsNotNone(dataset.structure)
        self.assertIsInstance(dataset.structure, qb.DataStructureDefinition)

        self.assertIsNotNone(dataset.structure.componentProperties)

        _assert_component_defined(dataset, "country")
        _assert_component_defined(dataset, "marker")
        _assert_component_defined(dataset, "some-existing-unit")
        _assert_component_defined(dataset, "some-existing-measure")

    def test_generating_concept_uri_template_from_global_concept_scheme_uri(self):
        """
            Given a globally defined skos:ConceptScheme's URI, generate the URI template for a column which maps the
            column's value to a concept defined inside the concept scheme.
        """
        column = SuppressedCsvColumn("Some Column")
        code_list = ExistingQbCodeList("http://base-uri/concept-scheme/this-concept-scheme-name")

        actual_concept_template_uri = qbwriter._get_default_value_uri_for_code_list_concepts(column, code_list)
        self.assertEqual("http://base-uri/concept-scheme/this-concept-scheme-name/{+some_column}",
                         actual_concept_template_uri)

    def test_generating_concept_uri_template_from_local_concept_scheme_uri(self):
        """
            Given a dataset-local skos:ConceptScheme's URI, generate the URI template for a column which maps the
            column's value to a concept defined inside the concept scheme.
        """
        column = SuppressedCsvColumn("Some Column")
        code_list = ExistingQbCodeList("http://base-uri/dataset-name#scheme/that-concept-scheme-name")

        actual_concept_template_uri = qbwriter._get_default_value_uri_for_code_list_concepts(column, code_list)
        self.assertEqual("http://base-uri/dataset-name#concept/that-concept-scheme-name/{+some_column}",
                         actual_concept_template_uri)

    def test_generating_concept_uri_template_from_unexpected_concept_scheme_uri(self):
        """
            Given a skos:ConceptScheme's URI *that does not follow the global or dataset-local conventions* used in our
            tooling, return the column's value as our best guess at the concept's URI.
        """
        column = SuppressedCsvColumn("Some Column")
        code_list = ExistingQbCodeList("http://base-uri/dataset-name#codes/that-concept-scheme-name")

        actual_concept_template_uri = qbwriter._get_default_value_uri_for_code_list_concepts(column, code_list)
        self.assertEqual("{+some_column}", actual_concept_template_uri)

    def test_default_property_value_uris_existing_dimension_column(self):
        """
            When an existing dimension is used, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
        """
        column = QbColumn("Some Column", ExistingQbDimension("http://base-uri/dimensions/existing-dimension"))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("http://base-uri/dimensions/existing-dimension", default_property_uri)
        self.assertEqual("{+some_column}", default_value_uri)

    def test_default_property_value_uris_new_dimension_column_without_code_list(self):
        """
            When a new dimension is defined without a code list, we can provide the `propertyUrl`,
            but we cannot guess the `valueUrl`.
        """
        column = QbColumn("Some Column", NewQbDimension("Some New Dimension"))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("#dimension/some-new-dimension", default_property_uri)
        self.assertEqual("{+some_column}", default_value_uri)

    def test_default_property_value_uris_new_dimension_column_with_code_list(self):
        """
            When an new dimension is defined with a code list, we can provide the `propertyUrl` and the `valueUrl`.
        """
        column = QbColumn("Some Column",
                          NewQbDimension("Some New Dimension",
                                         code_list=ExistingQbCodeList("http://base-uri/concept-scheme/this-scheme")))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("#dimension/some-new-dimension", default_property_uri)
        self.assertEqual("http://base-uri/concept-scheme/this-scheme/{+some_column}", default_value_uri)

    def test_default_property_value_uris_existing_attribute_column(self):
        """
            When an existing attribute is used, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
        """
        column = QbColumn("Some Column", ExistingQbAttribute("http://base-uri/attributes/existing-attribute"))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("http://base-uri/attributes/existing-attribute", default_property_uri)
        self.assertEqual("{+some_column}", default_value_uri)

    def test_default_property_value_uris_existing_attribute_column(self):
        """
            When a new attribute is defined, we can provide the `propertyUrl`, but we cannot guess the `valueUrl`.
        """
        column = QbColumn("Some Column", NewQbAttribute("This New Attribute"))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("#attribute/this-new-attribute", default_property_uri)
        self.assertEqual("{+some_column}", default_value_uri)

    def test_default_property_value_uris_multi_units_all_new(self):
        """
            When a QbMultiUnits component is defined using only new/locally defined units, we can provide the
            `propertyUrl` and the `valueUrl`.
        """
        column = QbColumn("Some Column", QbMultiUnits([NewQbUnit("Some New Unit")]))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure", default_property_uri)
        self.assertEqual("#unit/{+some_column}", default_value_uri)

    def test_default_property_value_uris_multi_units_all_existing(self):
        """
            When a QbMultiUnits component is defined using just existing units, we can provide the `propertyUrl` and
            `valueUrl`.
        """
        column = QbColumn("Some Column", QbMultiUnits([ExistingQbUnit("http://base-uri/units/existing-unit")]))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure", default_property_uri)
        self.assertEqual("{+some_column}", default_value_uri)

    def test_default_property_value_uris_multi_units_local_and_existing(self):
        """
            When a QbMultiUnits component is defined using a mixture of existing units and new units, we can't provide
            an appropriate and consistent `valueUrl`.

            An exception is raised when this is attempted.
        """
        column = QbColumn("Some Column", QbMultiUnits([NewQbUnit("Some New Unit"),
                                                       ExistingQbUnit("http://base-uri/units/existing-unit")]))
        self.assertRaises(Exception, lambda _: qbwriter._get_default_property_value_uris_for_column(column))

    def test_default_property_value_uris_multi_measure_all_new(self):
        """
            When a QbMultiMeasureDimension component is defined using only new/locally defined measures,
            we can provide the `propertyUrl` and the `valueUrl`.
        """
        column = QbColumn("Some Column", QbMultiMeasureDimension([NewQbMeasure("Some New Measure")]))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("http://purl.org/linked-data/cube#measureType", default_property_uri)
        self.assertEqual("#measure/{+some_column}", default_value_uri)

    def test_default_property_value_uris_multi_measure_all_existing(self):
        """
            When a QbMultiUnits component is defined using just existing units, we can provide the `propertyUrl` and
            `valueUrl`.
        """
        column = QbColumn("Some Column",
                          QbMultiMeasureDimension([ExistingQbMeasure("http://base-uri/measures/existing-measure")]))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertEqual("http://purl.org/linked-data/cube#measureType", default_property_uri)
        self.assertEqual("{+some_column}", default_value_uri)

    def test_default_property_value_uris_multi_measure_local_and_existing(self):
        """
            When a QbMultiUnits component is defined using a mixture of existing units and new units, we can't provide
            an appropriate and consistent `valueUrl`.

            An exception is raised when this is attempted.
        """
        column = QbColumn("Some Column",
                          QbMultiMeasureDimension([NewQbMeasure("Some New Measure"),
                                                   ExistingQbMeasure("http://base-uri/measures/existing-measure")]))
        self.assertRaises(Exception, lambda _: qbwriter._get_default_property_value_uris_for_column(column))

    def test_default_property_value_uris_single_measure_obs_val(self):
        """
            There should be no `propertyUrl` or `valueUrl` for a `QbSingleMeasureObservationValue`.
        """
        column = QbColumn("Some Column", QbSingleMeasureObservationValue(NewQbUnit("New Unit"),
                                                                         NewQbMeasure("New Qb Measure")))
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertIsNone(default_property_uri)
        self.assertIsNone(default_value_uri)

    def test_default_property_value_uris_multi_measure_obs_val(self):
        """
            There should be no `propertyUrl` or `valueUrl` for a `QbMultiMeasureObservationValue`.
        """
        column = QbColumn("Some Column", QbMultiMeasureObservationValue())
        default_property_uri, default_value_uri = qbwriter._get_default_property_value_uris_for_column(column)
        self.assertIsNone(default_property_uri)
        self.assertIsNone(default_value_uri)

    def test_csv_col_definition_default_property_value_urls(self):
        """
            When configuring a CSV-W column definition, if the user has not specified an `output_uri_template`
            against the `QbColumn` then the `propertyUrl` and `valueUrl`s should both be populated by the default
            values inferred from the component.
        """
        column = QbColumn("Some Column", QbMultiUnits([NewQbUnit("Some Unit")]))
        csv_col = qbwriter._generate_csvqb_column(column)
        self.assertEqual("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure", csv_col["propertyUrl"])
        self.assertEqual("#unit/{+some_column}", csv_col["valueUrl"])

    def test_csv_col_definition_output_uri_template_override(self):
        """
            When configuring a CSV-W column definition, if the user has specified an `output_uri_template` against the
            `QbColumn` then this should end up as the resulting CSV-W column's `valueUrl`.
        """
        column = QbColumn("Some Column", ExistingQbDimension("http://base-uri/dimensions/some-dimension"),
                          output_uri_template="http://base-uri/some-alternative-output-uri/{+some_column}")
        csv_col = qbwriter._generate_csvqb_column(column)
        self.assertEqual("http://base-uri/dimensions/some-dimension", csv_col["propertyUrl"])
        self.assertEqual("http://base-uri/some-alternative-output-uri/{+some_column}", csv_col["valueUrl"])

    def test_csv_col_definition(self):
        """
            Test basic configuration of a CSV-W column definition.
        """
        column = QbColumn("Some Column", ExistingQbDimension("http://base-uri/dimensions/some-dimension"))
        csv_col = qbwriter._generate_csvqb_column(column)
        self.assertFalse("suppressOutput" in csv_col)
        self.assertEqual("Some Column", csv_col["titles"])
        self.assertEqual("some_column", csv_col["name"])
        self.assertEqual("http://base-uri/dimensions/some-dimension", csv_col["propertyUrl"])
        self.assertEqual("{+some_column}", csv_col["valueUrl"])

    def test_csv_col_definition_suppressed(self):
        """
            Test basic configuration of a *suppressed* CSV-W column definition.
        """
        column = SuppressedCsvColumn("Some Column")
        csv_col = qbwriter._generate_csvqb_column(column)
        self.assertTrue(csv_col["suppressOutput"])
        self.assertEqual("Some Column", csv_col["titles"])
        self.assertEqual("some_column", csv_col["name"])
        self.assertFalse("propertyUrl" in csv_col)
        self.assertFalse("valueUrl" in csv_col)

    def test_virtual_columns_generated_for_single_obs_val(self):
        """
            Ensure that the virtual columns generated for a `QbSingleMeasureObservationValue`'s unit and measure are
            correct.
        """
        obs_val = QbSingleMeasureObservationValue(NewQbMeasure("Some Measure"), NewQbUnit("Some Unit"))
        virtual_columns = qbwriter._generate_virtual_columns_for_obs_val(obs_val)

        virt_unit = first(virtual_columns, lambda x: x["name"] == "virt_unit")
        self.assertIsNotNone(virt_unit)
        self.assertTrue(virt_unit["virtual"])
        self.assertEqual("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure", virt_unit["propertyUrl"])
        self.assertEqual("#unit/some-unit", virt_unit["valueUrl"])

        virt_measure = first(virtual_columns, lambda x: x["name"] == "virt_measure")
        self.assertIsNotNone(virt_measure)
        self.assertTrue(virt_measure["virtual"])
        self.assertEqual("http://purl.org/linked-data/cube#measureType", virt_measure["propertyUrl"])
        self.assertEqual("#measure/some-measure", virt_measure["valueUrl"])

    def test_virtual_columns_generated_for_multi_meas_obs_val(self):
        """
            Ensure that the virtual column generated for a `QbMultiMeasureObservationValue`'s unit and measure are
            correct.
        """
        obs_val = QbMultiMeasureObservationValue(unit=NewQbUnit("Some Unit"))
        virtual_columns = qbwriter._generate_virtual_columns_for_obs_val(obs_val)

        virt_unit = first(virtual_columns, lambda x: x["name"] == "virt_unit")
        self.assertIsNotNone(virt_unit)
        self.assertTrue(virt_unit["virtual"])
        self.assertEqual("http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure", virt_unit["propertyUrl"])
        self.assertEqual("#unit/some-unit", virt_unit["valueUrl"])

    def test_about_url_generation(self):
        """
            Ensuring that when an aboutUrl is defined for a non-multimeasure cube, the resulting URL
            is built in the order in which dimensions appear in the cube.
        """
        data = pd.DataFrame({
            "Existing Dimension": ["A", "B", "C"],
            "Local Dimension": ["D", "E", "F"],
            "Value": [2, 2, 2]
        })

        metadata = CubeMetadata("Some Dataset")
        columns = [
            QbColumn("Existing Dimension",
                     ExistingQbDimension("https://example.org/dimensions/existing_dimension")),
            QbColumn("Local Dimension", 
                     NewQbDimension.from_data("Name of New Dimension", 
                     data["Local Dimension"])),
            QbColumn("Value", 
                     QbSingleMeasureObservationValue(ExistingQbMeasure("http://example.com/measures/existing_measure"), 
                     NewQbUnit("New Unit")))
            
        ]

        cube = Cube(metadata, data, columns)

        actual_about_url = qbwriter._get_about_url(cube)
        expected_about_url = "#obs/{+existing_dimension}/{+local_dimension}"
        assert actual_about_url == expected_about_url

    def test_about_url_generation_with_multiple_measures(self):
        """
            Ensuring that when an aboutUrl is defined for a multimeasure cube, the resulting URL
            is built in the order in which dimensions appear in the cube except for the multi-measure
            dimensions which are appended to the end of the URL.
        """
        data = pd.DataFrame({
            "Measure": ["People", "Children", "Adults"],
            "Existing Dimension": ["A", "B", "C"],
            "Value": [2, 2, 2],
            "Local Dimension": ["D", "E", "F"],
            "Units": ["Percent", "People", "People"]
        })

        metadata = CubeMetadata("Some Dataset")
        columns = [
            QbColumn("Measure", QbMultiMeasureDimension.new_measures_from_data(data["Measure"])),
            QbColumn("Existing Dimension", ExistingQbDimension("https://example.org/dimensions/existing_dimension")),
            QbColumn("Local Dimension", NewQbDimension.from_data("Name of New Dimension", data["Local Dimension"])),
            QbColumn("Value", QbMultiMeasureObservationValue("number")),
            QbColumn("Units", QbMultiUnits.new_units_from_data(data["Units"]))
    
        ]

        cube = Cube(metadata, data, columns)

        actual_about_url = qbwriter._get_about_url(cube)
        expected_about_url = "#obs/{+existing_dimension}/{+local_dimension}/{+measure}"
        assert actual_about_url == expected_about_url


if __name__ == '__main__':
    unittest.main()