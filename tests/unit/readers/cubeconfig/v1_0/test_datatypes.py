from dataclasses import dataclass
import pandas as pd

from csvcubed.readers.cubeconfig.v1 import datatypes

from .virtualconfigs import VirtualConfigurations as vc
from tests.unit.test_baseunit import get_test_cases_dir
from pathlib import Path
import json

TEST_CASE_DIR = get_test_cases_dir().absolute() / "readers" / "cube-config" / "v1.0"


def _assert_dict(got: dict, expected: dict):
    """
    Helper for a light touch comparisson between a created dictionary
    and an expected dictionary.
    """

    assert len(got) == len(expected), (
        "Unexpected number of items:\n"
        f'Got: {", ".join(got.keys())}\n'
        f'Expected: {",".join(expected.keys())}'
    )
    for k, v in got.items():
        assert (
            k in expected
        ), f'Unexpected key found: "{k}". The expected keys were: {",".join(expected.keys())}'
        expected_v = expected[k]
        assert (
            expected_v == v
        ), f'For field "{k}", expexcted datatype: {expected_v}, got value {v}'


def test_configured_dimension_dtypes():
    """
    Test that where given a a configured dimension, that dimension is
    mapped to the dimemnsion type of string.
    """

    for config in [
        vc.DIMENSION_CONFIG_POPULATED,
        vc.DIMENSION_EXISTING,
        vc.DIMENSION_EXISTING_CODELIST,
        vc.DIMENSION_WITH_LABEL,
        vc.LABEL_ONLY,
    ]:

        # Assert expected dtype
        dtype = datatypes.pandas_datatypes_from_columns_config({"Dimension": config})
        _assert_dict(dtype, {"Dimension": "string"})


def test_attribute_literal_dtypes():
    """
    Test that where given a literal attribute, the provided datatype is
    mapped to our corresponding pandas datatype.
    """

    # It shouldnt matter which variation of an attribute literal but we'll
    # test with both to be thorough
    for config in [vc.ATTRIBUTE_NEW_LITERAL, vc.ATTRIBUTE_EXISTING_LITERAL]:

        for csvw_type, pandas_type in datatypes.ACCEPTED_DATATYPE_MAPPING.items():

            # Reassign datatype for test
            config["data_type"] = csvw_type

            # Assert expected dtype
            dtype = datatypes.pandas_datatypes_from_columns_config(
                {"Attribute": config}
            )
            _assert_dict(dtype, {"Attribute": pandas_type})


def test_assignable_pandas_datatypes_are_valid():
    """
    Confirm that all pandas dtypes we are mapping to are valid and
    can be assigned to a series while loading a dataframe.
    """

    pandas_dtypes = set(datatypes.ACCEPTED_DATATYPE_MAPPING.values())

    for pdt in pandas_dtypes:
        df = pd.DataFrame({"column": [1, 2, 3, 4, 5]}, dtype=pdt)
        assert df["column"].dtype == pdt


def test_datatypes_by_expicit_definition():
    """
    Confirm expected datatypes when using a fully configured dataset.
    """

    csv_path = Path(TEST_CASE_DIR / "cube_datatypes.csv")
    config_path = Path(TEST_CASE_DIR / "cube_datatypes.json")

    with open(config_path) as f:
        config = json.load(f)

    dtype = datatypes.get_pandas_datatypes(csv_path, config=config)

    _assert_dict(
        dtype,
        {
            "Dim-0": "string",
            "Dim-1": "string",
            "Dim-2": "string",
            "Attr-anyURI": "string",
            "Attr-boolean": "bool",
            "Attr-decimal": "float64",
            "Attr-integer": "int64",
            "Attr-long": "long",
            "Attr-int": "int64",
            "Attr-short": "short",
            "Attr-nonNegativeInteger": "uint64",
            "Attr-positiveInteger": "uint64",
            "Attr-unsignedLong": "uint64",
            "Attr-unsignedInt": "uint64",
            "Attr-unsignedShort": "uint64",
            "Attr-nonPositiveInteger": "int64",
            "Attr-negativeInteger": "int64",
            "Attr-double": "double",
            "Attr-float": "float64",
            "Attr-string": "string",
            "Attr-language": "string",
            "Attr-date": "string",
            "Attr-dateTime": "string",
            "Attr-dateTimeStamp": "string",
            "Attr-time": "string",
            "Value": "int64",
            "Measure": "string",
            "Units": "string",
        },
    )


def test_datatypes_by_convention():
    """
    Confirm expected datatypes when using a configured by convention dataset.
    """

    csv_path = Path(TEST_CASE_DIR / "cube_datatypes.csv")

    dtype = datatypes.get_pandas_datatypes(csv_path)

    _assert_dict(
        dtype,
        {
            "Dim-0": "string",
            "Dim-1": "string",
            "Dim-2": "string",
            "Attr-anyURI": "string",
            "Attr-boolean": "string",
            "Attr-decimal": "string",
            "Attr-integer": "string",
            "Attr-long": "string",
            "Attr-int": "string",
            "Attr-short": "string",
            "Attr-nonNegativeInteger": "string",
            "Attr-positiveInteger": "string",
            "Attr-unsignedLong": "string",
            "Attr-unsignedInt": "string",
            "Attr-unsignedShort": "string",
            "Attr-nonPositiveInteger": "string",
            "Attr-negativeInteger": "string",
            "Attr-double": "string",
            "Attr-float": "string",
            "Attr-string": "string",
            "Attr-language": "string",
            "Attr-date": "string",
            "Attr-dateTime": "string",
            "Attr-dateTimeStamp": "string",
            "Attr-time": "string",
            "Value": "float64",
            "Measure": "string",
            "Units": "string",
        },
    )
