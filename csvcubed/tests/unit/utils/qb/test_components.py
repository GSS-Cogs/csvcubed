from pathlib import Path
from csvcubed.utils.sparql import path_to_file_uri_for_rdflib
import pytest

from csvcubed.utils.qb.components import (
    ComponentPropertyType,
    get_component_property_as_relative_path,
    get_component_property_type,
)


def test_printable_component_property_url():
    """
    Should return component property as it is, if it is a url.
    """
    input_file_path = Path("folder/sub-folder/file.csv")
    component_property = "http://purl.org/linked-data/sdmx/2009/attribute#obsStatus"
    printable_component_property = get_component_property_as_relative_path(
        input_file_path, component_property
    )
    assert (
        printable_component_property
        == "http://purl.org/linked-data/sdmx/2009/attribute#obsStatus"
    )


def test_printable_component_property_sub_file_path():
    """
    Should return component property as relative path, if it is `file://`.
    """
    input_file_path = Path("folder", "sub-folder", "file.csv")
    other_file_path = Path("folder", "sub-folder", "sub-sub-folder", "other-file.csv")
    component_property = (
        f"{path_to_file_uri_for_rdflib(other_file_path)}#property-type/type"
    )
    printable_component_property = get_component_property_as_relative_path(
        input_file_path, component_property
    )
    assert (
        printable_component_property
        == f"{Path('sub-sub-folder', 'other-file.csv')}#property-type/type"
    )


def test_printable_component_property_root_file_path():
    """
    Should return component property as relative path, if it is `file://`.
    """
    input_file_path = Path("folder", "sub-folder", "file.csv")
    other_file_path = Path("other-folder", "sub-folder", "sub-sub-folder", "other-file.csv")
    component_property = f"{path_to_file_uri_for_rdflib(other_file_path)}#property-type/type"
    printable_component_property = get_component_property_as_relative_path(
        input_file_path, component_property
    )
    assert (
        printable_component_property
        == f"{Path('..', '..', 'other-folder', 'sub-folder', 'sub-sub-folder', 'other-file.csv')}#property-type/type"
    )


def test_printable_component_property_type_dimension():
    """
    Should return "Dimension" when the input is http://purl.org/linked-data/cube#DimensionProperty
    """
    property_type = get_component_property_type(
        "http://purl.org/linked-data/cube#DimensionProperty"
    )
    assert property_type == ComponentPropertyType.Dimension.value


def test_printable_component_property_type_attribute():
    """
    Should return "Attribute" when the input is http://purl.org/linked-data/cube#AttributeProperty
    """
    property_type = get_component_property_type(
        "http://purl.org/linked-data/cube#AttributeProperty"
    )
    assert property_type == ComponentPropertyType.Attribute.value


def test_printable_component_property_type_measure():
    """
    Should return "Measure" when the input is http://purl.org/linked-data/cube#MeasureProperty
    """
    property_type = get_component_property_type(
        "http://purl.org/linked-data/cube#MeasureProperty"
    )
    assert property_type == ComponentPropertyType.Measure.value


def test_printable_component_property_type_unsupported_exception():
    """
    Should raise an exception when the property is not supported (i.e. property is not of type Dimension, Attribute or Measure).
    """
    with pytest.raises(Exception):
        get_component_property_type(
            "http://purl.org/linked-data/cube#UnsupportedProperty"
        )
