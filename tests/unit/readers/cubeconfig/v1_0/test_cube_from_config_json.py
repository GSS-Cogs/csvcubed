import datetime
from pathlib import Path
import json
import pandas as pd
from tempfile import TemporaryDirectory
from typing import List

from csvcubed.models.cube.qb.components.attribute import ExistingQbAttribute
from csvcubed.models.cube.qb.components.codelist import (
    CompositeQbCodeList,
    ExistingQbCodeList,
)
from csvcubed.models.cube.qb.components.concept import DuplicatedQbConcept
from csvcubed.models.cube.qb.components.dimension import ExistingQbDimension
from csvcubed.models.cube.qb.components.measure import ExistingQbMeasure
from csvcubed.models.cube.qb.components.unit import ExistingQbUnit
from csvcubed.readers.catalogmetadata.v1.catalog_metadata_reader import (
    metadata_from_dict,
)

import pytest

from csvcubed.models.cube.cube import Cube
from csvcubed.models.cube.qb.catalog import CatalogMetadata
from csvcubed.models.cube.qb.components.attributevalue import (
    NewQbAttributeValue,
)
from csvcubed.models.cube.qb.components.observedvalue import (
    QbMultiMeasureObservationValue,
    QbSingleMeasureObservationValue,
)
from csvcubed.readers.cubeconfig.v1.mapcolumntocomponent import (
    map_column_to_qb_component,
)
from csvcubed.utils.uri import uri_safe
from csvcubed.cli.build import build as cli_build
from csvcubed.readers.cubeconfig.v1.configdeserialiser import _get_qb_column_from_json
from tests.unit.test_baseunit import get_test_cases_dir, assert_num_validation_errors
from csvcubed.definitions import APP_ROOT_DIR_PATH
from csvcubed.models.cube.qb import QbColumn
from csvcubed.models.cube.qb.components import (
    NewQbMeasure,
    NewQbUnit,
    NewQbDimension,
    NewQbCodeList,
    QbMultiMeasureDimension,
    QbMultiUnits,
    NewQbAttribute,
    NewQbConcept,
)

from .virtualconfigs import VirtualConfigurations as vc

TEST_CASE_DIR = get_test_cases_dir().absolute() / "readers" / "cube-config" / "v1.0"
SCHEMA_PATH_FILE = Path(
    APP_ROOT_DIR_PATH, "schema", "cube-config", "v1_0", "schema.json"
)


@pytest.mark.vcr
def test_build():
    with TemporaryDirectory() as temp_dir_path:
        temp_dir = Path(temp_dir_path)
        config = Path(TEST_CASE_DIR, "cube_data_config_ok.json")
        output = temp_dir / "out"
        csv = Path(TEST_CASE_DIR, "cube_data_config_ok.csv")
        cli_build(
            config_path=config,
            output_directory=output,
            csv_path=csv,
            fail_when_validation_error_occurs=True,
            validation_errors_file_out=Path(output, "validation_errors.json"),
        )


def _check_new_attribute_column(
    column: QbColumn, column_config: dict, column_data: list, title: str
) -> None:

    assert isinstance(column, QbColumn)
    assert isinstance(column.structural_definition, NewQbAttribute)
    assert hasattr(column, "type") is False
    assert column.csv_column_title == title
    assert column.uri_safe_identifier == uri_safe(title)
    assert column.uri_safe_identifier_override == column_config.get(
        "uri_safe_identifier_override"
    )

    sd = column.structural_definition
    assert sd.label == column_config.get("label", title)
    assert sd.description == column_config.get("description")
    assert sd.is_required == column_config.get("required", False)
    assert sd.parent_attribute_uri == column_config.get("from_existing")
    assert sd.source_uri == column_config.get("definition_uri")
    assert isinstance(sd.arbitrary_rdf, list)
    assert isinstance(sd.new_attribute_values, list)
    for av in sd.new_attribute_values:
        assert isinstance(av, NewQbAttributeValue)
        assert hasattr(av, "label")
        if isinstance(column_config["values"], bool):
            assert av.label in column_data
        else:
            assert av.label in [v["label"] for v in column_config["values"]]


def _check_new_dimension_column(
    column: QbColumn, column_config: dict, column_data: list, title: str
) -> None:
    assert isinstance(column, QbColumn)
    assert isinstance(column.structural_definition, NewQbDimension)

    # Check code_list default constructions (from data)
    assert isinstance(column.structural_definition.code_list, NewQbCodeList)
    assert isinstance(column.structural_definition.code_list.metadata, CatalogMetadata)
    assert hasattr(column, "type") is False
    assert column.structural_definition.label == column_config.get("label", title)
    assert column.structural_definition.description == column_config.get("description")
    assert column.structural_definition.parent_dimension_uri == column_config.get(
        "from_existing"
    )
    assert column.structural_definition.source_uri == column_config.get(
        "definition_uri"
    )

    assert isinstance(column.structural_definition.code_list.concepts, list)
    assert isinstance(column.structural_definition.code_list.concepts[0], NewQbConcept)
    assert column.csv_column_uri_template == column_config.get("cell_uri_template")

    unique_column_data = list(sorted(set(column_data)))
    assert len(column.structural_definition.code_list.concepts) == len(
        unique_column_data
    )
    for concept in column.structural_definition.code_list.concepts:
        assert concept.label in unique_column_data
        assert concept.code in unique_column_data
        assert concept.description is None
        assert concept.parent_code is None
        assert concept.sort_order is None
        assert concept.uri_safe_identifier == uri_safe(concept.label)
        assert concept.uri_safe_identifier_override is None


@pytest.mark.vcr
def test_build_config_ok():
    """
    Valid Cube from Data using Convention (no config json)
    """

    with TemporaryDirectory() as temp_dir_path:
        temp_dir = Path(temp_dir_path)
        csv = Path(TEST_CASE_DIR, "cube_data_config_ok.csv")
        config = Path(TEST_CASE_DIR, "cube_data_config_ok.json")
        output = temp_dir / "out"
        csv = Path(TEST_CASE_DIR, "cube_data_config_ok.csv")
        cube, validation_errors = cli_build(
            csv_path=csv,
            config_path=config,
            output_directory=output,
            fail_when_validation_error_occurs=True,
            validation_errors_file_out=Path(output, "validation_errors.json"),
        )

    assert isinstance(cube, Cube)
    assert isinstance(validation_errors, List)
    assert isinstance(cube.columns, list)
    for column in cube.columns:
        assert isinstance(column, QbColumn)

    col_dim_0 = cube.columns[0]
    assert isinstance(col_dim_0.structural_definition, NewQbDimension)
    assert isinstance(col_dim_0.structural_definition.code_list, NewQbCodeList)
    assert isinstance(
        col_dim_0.structural_definition.code_list.metadata, CatalogMetadata
    )
    assert isinstance(col_dim_0.structural_definition.code_list.concepts, list)
    assert isinstance(
        col_dim_0.structural_definition.code_list.concepts[0], NewQbConcept
    )

    col_dim_1 = cube.columns[1]
    assert isinstance(col_dim_1.structural_definition, NewQbDimension)
    assert isinstance(
        col_dim_1.structural_definition.code_list.metadata, CatalogMetadata
    )
    assert isinstance(col_dim_1.structural_definition.code_list.concepts, list)
    assert isinstance(
        col_dim_1.structural_definition.code_list.concepts[0], NewQbConcept
    )

    col_dim_2 = cube.columns[2]
    assert isinstance(col_dim_2.structural_definition, NewQbDimension)
    assert isinstance(
        col_dim_2.structural_definition.code_list.metadata, CatalogMetadata
    )
    assert isinstance(col_dim_2.structural_definition.code_list.concepts, list)
    assert isinstance(
        col_dim_2.structural_definition.code_list.concepts[0], NewQbConcept
    )

    col_attr_1 = cube.columns[3]
    assert isinstance(col_attr_1.structural_definition, NewQbAttribute)
    assert isinstance(col_attr_1.structural_definition.new_attribute_values, list)
    assert isinstance(
        col_attr_1.structural_definition.new_attribute_values[0], NewQbAttributeValue
    )

    col_observation = cube.columns[4]
    assert isinstance(
        col_observation.structural_definition, QbMultiMeasureObservationValue
    )
    assert col_observation.structural_definition.unit is None
    assert col_observation.structural_definition.data_type == "decimal"

    col_measure = cube.columns[5]
    assert isinstance(col_measure.structural_definition, QbMultiMeasureDimension)
    assert isinstance(col_measure.structural_definition.measures, list)
    assert isinstance(col_measure.structural_definition.measures[0], NewQbMeasure)

    col_unit = cube.columns[6]
    assert isinstance(col_unit.structural_definition, QbMultiUnits)
    assert isinstance(col_unit.structural_definition.units, list)
    assert isinstance(col_unit.structural_definition.units[0], NewQbUnit)


@pytest.mark.vcr
def test_dimension_new_no_type():
    """
    Checks a New dimension is created when omitting 'type'
    """
    column_data = ["a", "b", "c", "a"]
    dimension_config = vc.LABEL_ONLY
    data = pd.Series(column_data, name="Dimension Heading")

    (column, _) = map_column_to_qb_component(
        "New Dimension", dimension_config, data, cube_config_minor_version=0
    )
    _check_new_dimension_column(column, dimension_config, column_data, "New Dimension")


@pytest.mark.vcr
def test_dimension_new_config_common():
    """
    Using a common/typical config, populates all options and confirms the New Dimension &
    CodeList classes are created and all properties are mapped through correctly
    """
    column_data = ["a", "b", "c", "a"]
    dimension_config = vc.DIMENSION_CONFIG_POPULATED
    data = pd.Series(column_data, name="Dimension Heading")

    (column, _) = map_column_to_qb_component(
        "New Dimension", dimension_config, data, cube_config_minor_version=0
    )
    _check_new_dimension_column(column, dimension_config, column_data, "New Dimension")


@pytest.mark.vcr
def test_dimension_new_minimal_config():
    """
    Confirm we can create a new dimension with the minimal explicit dimension configuration.
    """
    column_data = ["a", "b", "c", "a"]
    dimension_config = vc.DIMENSION_WITH_LABEL
    data = pd.Series(column_data, name="Dimension Heading")

    (column, _) = map_column_to_qb_component(
        "New Dimension", dimension_config, data, cube_config_minor_version=0
    )
    _check_new_dimension_column(column, dimension_config, column_data, "New Dimension")


@pytest.mark.vcr
def test_dimension_existing():
    """
    Confirm we can create a new attribute resurce from configuration.
    """
    column_data = ["a", "b", "c", "a"]
    dimension_config = vc.DIMENSION_EXISTING
    data = pd.Series(column_data, name="Dimension Heading")

    (column, _) = map_column_to_qb_component(
        "New Dimension", dimension_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False

    # And the Column is of the expected type
    assert isinstance(column.structural_definition, ExistingQbDimension)
    assert not hasattr(column.structural_definition, "code_list")
    assert (
        column.structural_definition.dimension_uri == dimension_config["from_existing"]
    )
    assert column.structural_definition.range_uri is None
    assert isinstance(column.structural_definition.arbitrary_rdf, list)
    assert column.structural_definition.arbitrary_rdf == []


@pytest.mark.vcr
def test_attribute_new_resource():
    """
    Confirm we can create a new attribute resurce from configuration.
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.ATTRIBUTE_NEW_RESOURCE
    data = pd.Series(column_data, name="Attribute Heading")

    (column, _) = map_column_to_qb_component(
        "New Attribute", column_config, data, cube_config_minor_version=0
    )
    _check_new_attribute_column(column, column_config, column_data, "New Attribute")


@pytest.mark.vcr
def test_attribute_new_literal():
    """
    Confirm we can create a new attribute literal from configuration.
    """
    column_data = ["1", "2", "3", "4"]
    column_config = vc.ATTRIBUTE_NEW_LITERAL
    data = pd.Series(column_data, name="Attribute Heading")

    (column, _) = map_column_to_qb_component(
        "New Attribute", column_config, data, cube_config_minor_version=0
    )
    _check_new_attribute_column(column, column_config, column_data, "New Attribute")


@pytest.mark.vcr
def test_attribute_new_resource_with_values():
    """
    Checks New attribute resource where values are provided inline.
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.ATTRIBUTE_NEW_RESOURCE_WITH_VALUES
    data = pd.Series(column_data, name="Attribute Heading")

    (column, _) = map_column_to_qb_component(
        "New Attribute", column_config, data, cube_config_minor_version=0
    )
    _check_new_attribute_column(column, column_config, column_data, "New Attribute")


@pytest.mark.vcr
def test_attribute_existing_resource():
    """
    Populates options for an Existing Attribute resource, checking all properties are mapped
    through correctly
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.ATTRIBUTE_EXISTING_RESOURCE
    data = pd.Series(column_data, name="Attribute Heading")

    (column, _) = map_column_to_qb_component(
        "Existing Resource Attribute", column_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False

    # And the Column is of the expected type
    assert isinstance(column.structural_definition, ExistingQbAttribute)
    assert not hasattr(column.structural_definition, "code_list")
    assert column.structural_definition.attribute_uri == column_config["from_existing"]
    assert isinstance(column.structural_definition.arbitrary_rdf, list)
    assert column.structural_definition.arbitrary_rdf == []


@pytest.mark.vcr
def test_attribute_existing_literal():
    """
    Populates options for an Existing Attribute checks all properties are mapped through correctly
    """
    column_config = vc.ATTRIBUTE_EXISTING_LITERAL
    (column, _) = map_column_to_qb_component(
        "Existing Literal Attribute", column_config, "", cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False

    # And the Column is of the expected type
    assert isinstance(column.structural_definition, ExistingQbAttribute)
    assert not hasattr(column.structural_definition, "code_list")
    assert column.structural_definition.attribute_uri == column_config["from_existing"]
    assert isinstance(column.structural_definition.arbitrary_rdf, list)
    assert column.structural_definition.arbitrary_rdf == []


@pytest.mark.vcr
def test_attribute_existing_resource_has_values():
    """
    Checks that new (non nul) values are created from data for an existing attribute
    """
    column_data = ["a", "b", None, "a"]
    column_config = vc.ATTRIBUTE_EXISTING_RESOURCE
    data = pd.Series(column_data, name="Attribute Heading")

    (column, _) = map_column_to_qb_component(
        "Existing Attribute", column_config, data, cube_config_minor_version=0
    )

    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False

    sd = column.structural_definition
    assert isinstance(sd, ExistingQbAttribute)
    assert not hasattr(sd, "code_list")
    # assert sd.definition_uri == column_config.get('from_existing')
    assert sd.attribute_uri == column_config.get("from_existing", "")
    assert sd.is_required == column_config.get("required")
    assert isinstance(sd.arbitrary_rdf, list)
    assert sd.arbitrary_rdf == []
    if column_config.get("required") is True:
        data_vals = set(column_data)
    else:
        data_vals = set([v for v in column_data if v])
    assert len(sd.new_attribute_values) == len(list(data_vals))
    for value in sd.new_attribute_values:
        assert hasattr(value, "label")
        assert value.label in data_vals


@pytest.mark.vcr
def test_measure_new():
    """
    Populates options for an New Measures checks all properties are mapped through correctly
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.MEASURE_NEW
    data = pd.Series(column_data, name="New Measure")

    (column, _) = map_column_to_qb_component(
        "New Measure", column_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    # And the Column is of the expected type
    assert hasattr(column, "type") is False
    assert column.csv_column_title == "New Measure"
    assert column.uri_safe_identifier == uri_safe("New Measure")
    assert column.uri_safe_identifier_override == None

    sd = column.structural_definition
    assert isinstance(sd, QbMultiMeasureDimension)
    assert isinstance(sd.measures, list)
    assert len(sd.measures) == len(set(data))
    for measure in sd.measures:
        assert isinstance(measure, NewQbMeasure)
        assert measure.label in column_data


@pytest.mark.vcr
def test_measure_existing():
    """
    Populates options for existing Measures checks all properties are mapped through correctly
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.MEASURE_EXISTING
    data = pd.Series(column_data, name="Existing Measure Series")

    (column, _) = map_column_to_qb_component(
        "Existing Measure", column_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False
    assert column.uri_safe_identifier == uri_safe("Existing Measure")
    assert column.uri_safe_identifier_override is None

    sd = column.structural_definition
    assert isinstance(sd, QbMultiMeasureDimension)
    assert isinstance(sd.measures, list)
    assert len(sd.measures) == len(set(data))
    for measure in sd.measures:
        assert isinstance(measure, ExistingQbMeasure)
        assert measure.measure_uri.startswith(
            column_config["cell_uri_template"][
                : column_config["cell_uri_template"].find("{")
            ]
        )
        assert (
            measure.measure_uri[column_config["cell_uri_template"].find("{") :]
            in column_data
        )


@pytest.mark.vcr
def test_unit_new():
    """
    Populates options for an New Units checks all properties are mapped through correctly
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.UNIT_NEW
    data = pd.Series(column_data, name="New Units")

    (column, _) = map_column_to_qb_component(
        "New Units", column_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    # And the Column is of the expected type
    assert hasattr(column, "type") is False
    assert column.csv_column_title == "New Units"
    assert column.uri_safe_identifier == uri_safe("New Units")
    assert column.uri_safe_identifier_override == None

    sd = column.structural_definition
    assert isinstance(sd, QbMultiUnits)
    assert isinstance(sd.units, list)
    assert len(sd.units) == len(set(data))
    for unit in sd.units:
        assert isinstance(unit, NewQbUnit)
        assert unit.label in column_data


@pytest.mark.vcr
def test_units_existing():
    """
    Populates options for an Existing Units checks all properties are mapped through correctly
    """
    column_data = ["a", "b", "c", "a"]
    column_config = vc.UNIT_EXISTING
    data = pd.Series(column_data, name="Existing Unit Series")

    (column, _) = map_column_to_qb_component(
        "Existing Unit", column_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False
    assert column.uri_safe_identifier == uri_safe("Existing Unit")
    assert column.uri_safe_identifier_override is None

    sd = column.structural_definition
    assert isinstance(sd, QbMultiUnits)
    assert isinstance(sd.units, list)
    assert len(sd.units) == len(set(data))
    for unit in sd.units:
        assert isinstance(unit, ExistingQbUnit)
        assert unit.unit_uri.startswith(
            column_config["cell_uri_template"][
                : column_config["cell_uri_template"].find("{")
            ]
        )
        assert (
            unit.unit_uri[column_config["cell_uri_template"].find("{") :] in column_data
        )


@pytest.mark.vcr
def test_observation_ok():
    column_data = ["a", "b", "c", "a"]
    column_config = {
        "type": "observations",
        "data_type": "decimal",
        # 'unit': None,
        # 'measure': None
    }
    # "properties": {
    #     "type": {
    #         "description": "Column type.",
    #         "type": "string",
    #         "default": "observation"
    #     },
    #     "data_type": {
    #         "$ref": "#/definitions/v1.0/dataTypes"
    #     },
    #     "unit": {
    #         "description": "The units being measured in this observation",
    #         "$ref": "#/definitions/v1.0/valueTypes/unitType"
    #     },
    #     "measure": {
    #         "description": "The measure used for this observation",
    #         "$ref": "#/definitions/v1.0/valueTypes/measureType"
    #     }
    data = pd.Series(column_data, name="Observation Series")

    (column, _) = map_column_to_qb_component(
        "Observations", column_config, data, cube_config_minor_version=0
    )

    # Confirm a Column is returned
    assert isinstance(column, QbColumn)
    assert hasattr(column, "type") is False
    assert column.uri_safe_identifier == uri_safe("observations")
    assert column.uri_safe_identifier_override is None

    sd = column.structural_definition
    assert isinstance(sd, QbMultiMeasureObservationValue)
    assert sd.unit is None
    assert sd.data_type == "decimal"


def test_new_dimension_existing_code_list():
    """
    Ensure we can correctly define a new dimension using an existing code-list
    """
    column_data = ["a", "b", "c", "a"]
    dimension_config = vc.DIMENSION_EXISTING_CODELIST
    data = pd.Series(column_data, name="Dimension Heading")

    (column, _) = map_column_to_qb_component(
        "New Dimension", dimension_config, data, cube_config_minor_version=0
    )

    assert isinstance(column.structural_definition, NewQbDimension)
    dimension = column.structural_definition
    assert dimension.label == "The New Dimension"
    assert isinstance(dimension.code_list, ExistingQbCodeList)
    assert (
        dimension.code_list.concept_scheme_uri == "http://example.com/code-list#scheme"
    )
    assert (
        column.csv_column_uri_template
        == "http://example.com/code-list#{+new_dimension}"
    )


@pytest.mark.vcr
def test_column_template_expansion():
    """
    Test that when using a column template, we see the default parameters expanded as expected.
    """
    data = pd.DataFrame({"The Column": ["a", "b", "c", "a"]})

    (column, _) = _get_qb_column_from_json(
        {
            "from_template": "year",
        },
        "The Column",
        data,
        1,
    )

    assert isinstance(column.structural_definition, NewQbDimension)
    dimension = column.structural_definition
    assert dimension.label == "Year"


def test_load_catalog_metadata():
    with open(TEST_CASE_DIR / "cube_data_config_ok.json") as f:
        config = json.load(f)

    catalog_metadata = metadata_from_dict(config)

    validation_errors = catalog_metadata.pydantic_validation()
    assert_num_validation_errors(validation_errors, 0)

    assert (
        catalog_metadata.title == "Tests/test-cases/config/schema-cube-data-config-ok"
    )
    assert catalog_metadata.identifier == "schema-cube-data-config-ok"
    assert (
        catalog_metadata.creator_uri
        == "https://www.gov.uk/government/organisations/office-for-national-statistics"
    )
    assert catalog_metadata.publisher_uri == "http://statistics.data.gov.uk"
    assert catalog_metadata.description == "Schema for testing"
    assert catalog_metadata.summary == "a summary"
    assert (
        catalog_metadata.license_uri
        == "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    )
    assert catalog_metadata.public_contact_point_uri == "mailto:csvcubed@example.com"

    # Test date deserialisation
    assert catalog_metadata.dataset_issued == datetime.date(2022, 3, 4)

    # Test date-time deserialisation
    assert catalog_metadata.dataset_modified == datetime.datetime(
        2022, 3, 4, 15, 0, 0, tzinfo=datetime.timezone.utc
    )

    assert set(catalog_metadata.keywords) == {"A keyword", "Another keyword"}
    assert set(catalog_metadata.theme_uris) == {
        "https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments"
    }


def test_date_time_column_extraction():
    """
    Ensure that date time columns generate code lists which refer back to the original reference.data.gov.uk identifiers.
    """
    data = pd.DataFrame({"The Column": ["2010", "2011", "2012"]})

    (column, _) = _get_qb_column_from_json(
        {
            "type": "dimension",
            "from_existing": "http://purl.org/linked-data/sdmx/2009/dimension#refPeriod",
            "label": "Year",
            "cell_uri_template": "http://reference.data.gov.uk/id/year/{+the_column}",
        },
        "The Column",
        data,
        1,
    )

    assert isinstance(
        column.structural_definition, NewQbDimension
    ), column.structural_definition
    new_dimension = column.structural_definition
    assert isinstance(new_dimension.code_list, CompositeQbCodeList)
    composite_code_list = new_dimension.code_list
    assert set(composite_code_list.concepts) == {
        DuplicatedQbConcept(
            "http://reference.data.gov.uk/id/year/2010", label="2010", code="2010"
        ),
        DuplicatedQbConcept(
            "http://reference.data.gov.uk/id/year/2011", label="2011", code="2011"
        ),
        DuplicatedQbConcept(
            "http://reference.data.gov.uk/id/year/2012", label="2012", code="2012"
        ),
    }

    # csv_column_uri_template must be reset to None so that the URI automatically points to the
    # newly created QbCompositeCodeList
    assert column.csv_column_uri_template is None


def test_observation_value_data_type_extraction():
    """
    Ensure that the data_type can be correctly extracted from an observation's JSON config.
    """
    data = pd.DataFrame({"The Column": [1, 2, 3]})

    (column, _) = _get_qb_column_from_json(
        {
            "type": "observations",
            "data_type": "integer",
            "unit": "http://example.com/some-unit",
            "measure": "http://example.com/some-measure",
        },
        "The Column",
        data,
        1,
    )

    assert isinstance(
        column.structural_definition, QbSingleMeasureObservationValue
    ), column.structural_definition
    obs_val = column.structural_definition
    assert obs_val.data_type == "integer"


def test_bool_column_is_supressed_from_json_config():
    """
    Test to ensure that columns are supressed when given a boolean value.
    """
    data = pd.DataFrame({"The Column": [1, 2, 3]})

    (column, _) = _get_qb_column_from_json(
        {False},
        "The Column",
        data,
        1,
    )

    assert isinstance(column, QbColumn)


if __name__ == "__main__":
    pytest.main()
