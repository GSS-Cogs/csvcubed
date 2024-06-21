import csv
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Set

import pandas as pd
import pytest
from rdflib import XSD, Graph, Literal, URIRef

from csvcubed.definitions import SDMX_ATTRIBUTE_UNIT_URI
from csvcubed.models.cube.columns import SuppressedCsvColumn
from csvcubed.models.cube.cube import Cube
from csvcubed.models.cube.qb.catalog import CatalogMetadata
from csvcubed.models.cube.qb.columns import QbColumn
from csvcubed.models.cube.qb.components.arbitraryrdf import (
    RdfSerialisationHint,
    TripleFragmentBase,
)
from csvcubed.models.cube.qb.components.attribute import (
    ExistingQbAttribute,
    NewQbAttribute,
    QbAttribute,
)
from csvcubed.models.cube.qb.components.concept import NewQbConcept
from csvcubed.models.cube.qb.components.dimension import (
    ExistingQbDimension,
    NewQbDimension,
)
from csvcubed.models.cube.qb.components.measure import NewQbMeasure, QbMeasure
from csvcubed.models.cube.qb.components.measuresdimension import QbMultiMeasureDimension
from csvcubed.models.cube.qb.components.observedvalue import QbObservationValue
from csvcubed.models.cube.qb.components.unit import NewQbUnit
from csvcubed.models.cube.qb.components.unitscolumn import QbMultiUnits
from csvcubed.models.cube.uristyle import URIStyle
from csvcubed.models.uriidentifiable import UriIdentifiable
from csvcubed.models.validatedmodel import ValidationFunction
from csvcubed.utils.iterables import first
from csvcubed.writers.qbwriter import QbWriter


@dataclass
class TestQbMeasure(QbMeasure, UriIdentifiable):
    uri_safe_identifier_override: Optional[str] = field(default=None, repr=False)

    def _get_arbitrary_rdf(self) -> List[TripleFragmentBase]:
        pass

    def get_permitted_rdf_fragment_hints(self) -> Set[RdfSerialisationHint]:
        pass

    def get_default_node_serialisation_hint(self) -> RdfSerialisationHint:
        pass

    def get_identifier(self) -> str:
        pass

    def _get_validations(self) -> Dict[str, ValidationFunction]:
        return {
            **UriIdentifiable._get_validations(self),
        }


empty_cube = Cube(CatalogMetadata("Cube Name"), pd.DataFrame, [])
empty_qbwriter = QbWriter(empty_cube)


def test_output_new_dimension_code_list_csvws_urls(tests_env_vars_setup_and_teardown):
    """
    Ensure that a new code list is referenced as a table in the CSV-W.
    """

    data = pd.DataFrame({"New Dimension": ["A", "B", "C"], "Value": [1, 2, 3]})
    cube = Cube(
        CatalogMetadata("Cube Name"),
        pd.DataFrame(),
        [
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data(
                    "Some Dimension", "New Dimension", data["New Dimension"]
                ),
            )
        ],
    )
    qb_writer = QbWriter(cube)
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        qb_writer._output_new_code_list_csvws(temp_dir)
        graph = Graph()
        graph.parse(
            temp_dir / "some-dimension.csv-metadata.json", publicID="file://relative/"
        )
        assert (
            URIRef("file://relative/some-dimension.csv#code-list"),
            URIRef("http://www.w3.org/ns/csvw#url"),
            Literal("some-dimension.csv", datatype=XSD.anyURI),
        ) in graph


def test_new_attribute_code_list_csvws_urls_codelist_true(
    tests_env_vars_setup_and_teardown,
):
    data = pd.DataFrame(
        {
            "New Dimension": ["A", "B", "C"],
            "New Attribute": ["D", "E", "F"],
            "Value": [1, 2, 3],
        }
    )
    cube = Cube(
        CatalogMetadata("Cube Name"),
        pd.DataFrame(),
        [
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data(
                    label="Some Dimension",
                    csv_column_title="New Dimension",
                    data=data["New Dimension"],
                ),
            ),
            QbColumn(
                "New Attribute",
                NewQbAttribute.from_data(
                    label="Some Attribute",
                    csv_column_title="New Attribute",
                    data=data["New Attribute"],
                ),
            ),
        ],
    )
    qb_writer = QbWriter(cube)
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        qb_writer._output_new_code_list_csvws(temp_dir)
        graph = Graph()
        graph.parse(
            temp_dir / "some-attribute.csv-metadata.json", publicID="file://relative/"
        )
        assert (
            URIRef("file://relative/some-attribute.csv#code-list"),
            URIRef("http://www.w3.org/ns/csvw#url"),
            Literal("some-attribute.csv", datatype=XSD.anyURI),
        ) in graph


def test_output_new_code_list_csws_urls_with_uri_style_without_file_extensions():
    """
    Ensure that a new code list is correctly referenced as a table in the CSV-W even when
    the URIStyle is set to output URIs without file extensions.
    """
    data = pd.DataFrame({"New Dimension": ["A", "B", "C"], "Value": [1, 2, 3]})
    cube = Cube(
        CatalogMetadata("Cube Name"),
        pd.DataFrame(),
        [
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data(
                    "Some Dimension", "New Dimension", data["New Dimension"]
                ),
            )
        ],
        uri_style=URIStyle.WithoutFileExtensions,
    )
    qb_writer = QbWriter(cube)
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        qb_writer._output_new_code_list_csvws(temp_dir)
        graph = Graph()
        graph.parse(
            temp_dir / "some-dimension.csv-metadata.json", publicID="file://relative/"
        )
        assert (
            URIRef("file://relative/some-dimension#code-list"),
            URIRef("http://www.w3.org/ns/csvw#url"),
            Literal("some-dimension.csv", datatype=XSD.anyURI),
        ) in graph


def test_csv_col_definition_default_property_value_urls():
    """
    When configuring a CSV-W column definition, if the user has not specified an `csv_column_uri_template`
    against the `QbColumn` then the `propertyUrl` and `valueUrl`s should both be populated by the default
    values inferred from the component.
    """
    column = QbColumn("Some Column", QbMultiUnits([NewQbUnit("Some Unit")]))
    csv_col = empty_qbwriter._generate_csvw_column_definition(column)
    assert SDMX_ATTRIBUTE_UNIT_URI == csv_col["propertyUrl"]
    assert "cube-name.csv#unit/{+some_column}" == csv_col["valueUrl"]


def test_csv_col_definition_csv_column_uri_template_override():
    """
    When configuring a CSV-W column definition, if the user has specified an `csv_column_uri_template` against the
    `QbColumn` then this should end up as the resulting CSV-W column's `valueUrl`.
    """
    column = QbColumn(
        "Some Column",
        ExistingQbDimension("http://base-uri/dimensions/some-dimension"),
        csv_column_uri_template="http://base-uri/some-alternative-output-uri/{+some_column}",
    )
    csv_col = empty_qbwriter._generate_csvw_column_definition(column)
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
    csv_col = empty_qbwriter._generate_csvw_column_definition(column)
    assert "suppressOutput" not in csv_col
    assert csv_col["titles"] == "Some Column"
    assert csv_col["name"] == "some_column"
    assert csv_col["propertyUrl"] == "http://base-uri/dimensions/some-dimension"
    assert csv_col["valueUrl"] == "{+some_column}"
    assert csv_col["required"]


def test_csv_col_required():
    """Test that the :attr:`required` key is set correctly for various different component types."""
    required_columns = [
        QbColumn(
            "Some Dimension",
            ExistingQbDimension("http://base-uri/dimensions/some-dimension"),
        ),
        QbColumn(
            "Some Required Attribute",
            NewQbAttribute("Some Attribute", is_required=True),
        ),
        QbColumn("Some Multi Units", QbMultiUnits([])),
        QbColumn("Some Measure Dimension", QbMultiMeasureDimension([])),
        QbColumn(
            "Some Obs Val",
            QbObservationValue(NewQbMeasure("Some Measure")),
        ),
    ]

    optional_columns = [
        QbColumn(
            "Some Optional Attribute",
            NewQbAttribute("Some Attribute", is_required=False),
        )
    ]

    for col in required_columns:
        csv_col = empty_qbwriter._generate_csvw_column_definition(col)
        required = csv_col["required"]
        assert isinstance(required, bool)
        assert required == True

    for col in optional_columns:
        csv_col = empty_qbwriter._generate_csvw_column_definition(col)
        required = csv_col["required"]
        assert isinstance(required, bool)
        assert not required


def test_csv_col_required_for_pivoted_multi_measure():
    """Test that the :attr:`required` key is set correctly for various different component types for a pivoted multi-measure input."""
    data = pd.DataFrame(
        {
            "New Dimension": ["A", "B"],
            "Units": ["A B", "A.B"],
            "Value": [2, 2],
        }
    )
    cube = Cube(
        metadata=CatalogMetadata("Some Qube"),
        data=data,
        columns=[
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data(
                    "New Dimension", "New Dimension", data["New Dimension"]
                ),
            ),
            QbColumn(
                "Units",
                QbMultiUnits.new_units_from_data(data["Units"]),
            ),
            QbColumn(
                "Some Required Attribute",
                NewQbAttribute("Some Attribute", is_required=True),
            ),
            QbColumn(
                "Some Optional Attribute",
                NewQbAttribute("Some Attribute", is_required=False),
            ),
            QbColumn(
                "Some Obs Value",
                QbObservationValue(NewQbMeasure("Some Measure")),
            ),
            QbColumn(
                "Some Other Obs Value",
                QbObservationValue(NewQbMeasure("Some Other Measure")),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    obs_val_cols = cube.get_columns_of_dsd_type(QbObservationValue)
    for col in cube.columns:
        csv_col = qb_writer._generate_csvw_column_definition(col)
        required = csv_col["required"]
        assert isinstance(required, bool)
        if isinstance(col.structural_definition, QbAttribute):
            # Determine if the cube is pivoted multi-measure
            if cube.is_pivoted_shape and len(obs_val_cols) > 1:
                # If the cube is in pivoted multi-measure shape, the attribute columns cannot be set to required.
                assert required == False
        else:
            assert required == True


def test_csv_col_required_observed_value_with_obs_status_attribute():
    """Test that the observation value column is **not** marked as `required` in the CSV-W where an `sdmxa:obsStatus`
    attribute column is defined in the same cube."""
    observed_values_column = QbColumn(
        "Values",
        QbObservationValue(
            NewQbMeasure("Some Measure"),
            NewQbUnit("Some Unit"),
        ),
    )

    qube = Cube(
        metadata=CatalogMetadata("Some Qube"),
        data=None,
        columns=[
            QbColumn("Some Dimension", NewQbDimension(label="Some Dimension")),
            observed_values_column,
            QbColumn(
                "Marker",
                ExistingQbAttribute(
                    "http://purl.org/linked-data/sdmx/2009/attribute#obsStatus"
                ),
                csv_column_uri_template="https://example.org/some_attribute/{+Some_attribute}",
            ),
        ],
    )
    writer = QbWriter(qube)
    observed_values_column_is_required = writer._generate_csvw_column_definition(
        observed_values_column
    )["required"]
    assert isinstance(observed_values_column_is_required, bool)
    assert not observed_values_column_is_required


def test_csv_col_definition_suppressed():
    """
    Test basic configuration of a *suppressed* CSV-W column definition.
    """
    column = SuppressedCsvColumn("Some Column")
    csv_col = empty_qbwriter._generate_csvw_column_definition(column)
    assert csv_col["suppressOutput"]
    assert "Some Column" == csv_col["titles"]
    assert "some_column" == csv_col["name"]
    assert "propertyUrl" not in csv_col
    assert "valueUrl" not in csv_col


def test_virtual_columns_generated_for_single_obs_val():
    """
    Ensure that the virtual columns generated for a `QbObservationValue`'s unit and measure are correct.
    """
    cube = Cube(
        CatalogMetadata("Cube"),
        columns=[
            QbColumn("Some Dimension", NewQbDimension("Some Dimension")),
            QbColumn(
                "Some Obs Val",
                QbObservationValue(
                    NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
                ),
            ),
        ],
    )
    writer = QbWriter(cube)

    virtual_columns = (
        writer._generate_virtual_columns_for_obs_vals_in_pivoted_shape_cube()
    )

    virt_col = first(virtual_columns, lambda x: x["name"] == "virt_slice")
    assert virt_col is not None
    assert virt_col["virtual"] == True
    assert virt_col["propertyUrl"] == "rdf:type"
    assert virt_col["valueUrl"] == "qb:Slice"

    virt_col = first(virtual_columns, lambda x: x["name"] == "virt_obs_some_obs_val")
    assert virt_col is not None
    assert virt_col["virtual"] == True
    assert virt_col["propertyUrl"] == "qb:observation"
    assert virt_col["valueUrl"] == "cube.csv#obs/{some_dimension}@some-measure"

    virt_col = first(
        virtual_columns, lambda x: x["name"] == "virt_obs_some_obs_val_meas"
    )
    assert virt_col is not None
    assert virt_col["virtual"] == True
    assert virt_col["aboutUrl"] == "cube.csv#obs/{some_dimension}@some-measure"
    assert virt_col["propertyUrl"] == "qb:measureType"
    assert virt_col["valueUrl"] == "cube.csv#measure/some-measure"

    virt_col = first(
        virtual_columns, lambda x: x["name"] == "virt_dim_some_obs_val_some_dimension"
    )
    assert virt_col is not None
    assert virt_col["virtual"] == True
    assert virt_col["aboutUrl"] == "cube.csv#obs/{some_dimension}@some-measure"
    assert virt_col["propertyUrl"] == "cube.csv#dimension/some-dimension"
    assert virt_col["valueUrl"] == "{+some_dimension}"

    virt_col = first(
        virtual_columns, lambda x: x["name"] == "virt_obs_some_obs_val_type"
    )
    assert virt_col is not None
    assert virt_col["virtual"] == True
    assert virt_col["aboutUrl"] == "cube.csv#obs/{some_dimension}@some-measure"
    assert virt_col["propertyUrl"] == "rdf:type"
    assert virt_col["valueUrl"] == "qb:Observation"

    virt_col = first(
        virtual_columns, lambda x: x["name"] == "virt_dataSet_some_obs_val"
    )
    assert virt_col is not None
    assert virt_col["virtual"] == True
    assert virt_col["aboutUrl"] == "cube.csv#obs/{some_dimension}@some-measure"
    assert virt_col["propertyUrl"] == "qb:dataSet"
    assert virt_col["valueUrl"] == "cube.csv#qbDataSet"


def test_virtual_columns_generated_for_multi_meas_obs_val():
    """
    Ensure that the virtual column generated for a `QbObservationValue`'s unit and measure are
    correct.
    """
    obs_val = QbObservationValue(unit=NewQbUnit("Some Unit"))
    virtual_columns = (
        empty_qbwriter._generate_virtual_columns_for_obs_val_in_standard_shape_cube(
            obs_val
        )
    )

    virt_unit = first(virtual_columns, lambda x: x["name"] == "virt_unit")
    assert virt_unit is not None
    assert virt_unit["virtual"]
    assert SDMX_ATTRIBUTE_UNIT_URI == virt_unit["propertyUrl"]
    assert "cube-name.csv#unit/some-unit" == virt_unit["valueUrl"]


def test_output_integer_obs_val_with_missing_values():
    """
    Due to the way that pandas represents missing values (as NaN), instead of interpreting an integer data column as
     integers, it represents the column as decimal values when some values are missing. Therefore we need to explicitly
     coerce these values back to integers.

     This test ensures that we can write CSVs to disk which contain integer values even when one of the obs_vals is
     missing.
    """

    data = pd.DataFrame({"New Dimension": ["A", "B", "C"], "Value": [1, None, 3]})

    cube = Cube(
        CatalogMetadata("Some Dataset"),
        data,
        [
            QbColumn(
                "New Dimension",
                NewQbDimension.from_data(
                    "Some Dimension", "New Dimension", data["New Dimension"]
                ),
            ),
            QbColumn(
                "Value",
                QbObservationValue(
                    NewQbMeasure("Some Measure"),
                    NewQbUnit("Some Unit"),
                    data_type="int",
                ),
            ),
        ],
    )

    qb_writer = QbWriter(cube)
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        qb_writer.write(temp_dir)
        with open(temp_dir / "some-dataset.csv") as csv_file:
            rows = list(csv.reader(csv_file, delimiter=",", quotechar='"'))
            for row in rows[1:]:
                value: str = row[1]
                if len(value) > 0:
                    # If any of the values are not integers (e.g. "1.0") the next line will throw an exception.
                    int_val = int(value)
                    assert isinstance(int_val, int)
                # else: len == 0 implies it's a missing value, which is expected in one location.


if __name__ == "__main__":
    pytest.main()
