import pytest
from pandas import Series

from csvcubed.readers.codelistconfig.codelist_schema_versions import (
    get_code_list_versioned_deserialiser,
)
from csvcubed.readers.cubeconfig.v1.columnschema import (
    EXISTING_UNIT_DEFAULT_SCALING_FACTOR,
    NewDimension,
    Unit,
    _get_unit_scaling_factor,
)


def test_new_unit():
    """
    Scaling factor of a new unit should be None.
    """
    unit = Unit("New Unit")
    scaling_factor = _get_unit_scaling_factor(unit)

    assert scaling_factor is None


def test_existing_unit_without_scaling_factor():
    """
    Scaling factor of an existing unit should be 1.0 when it is not defined.
    """
    unit = Unit(
        "Unit From Existing Unit", from_existing="http://qudt.org/vocab/unit/NUM"
    )
    scaling_factor = _get_unit_scaling_factor(unit)

    assert scaling_factor == EXISTING_UNIT_DEFAULT_SCALING_FACTOR


def test_existing_unit_with_scaling_factor():
    """
    Scaling factor of an existing unit should be the user-defined scaling factor when it is defined.
    """
    unit = Unit(
        "Unit From Existing Unit",
        from_existing="http://qudt.org/vocab/unit/NUM",
        scaling_factor=0.01,
    )
    scaling_factor = _get_unit_scaling_factor(unit)

    assert scaling_factor == 0.01


def test_code_list_config_v1_same_as():
    """
    Tests that a NewQBCodeList is successfully be generated when given an input config with codelist schema
    version 1.x and using the same_as field, with the correct version of the config deserialiser.
    """
    new_dimension = NewDimension(
        "Dimension",
        code_list={
            "$schema": "https://purl.org/csv-cubed/code-list-config/v1.1",
            "title": "Code list title",
            "concepts": [
                {
                    "label": "A",
                    "description": "A data record",
                    "notation": "a",
                    "same_as": "http://example.com/concepts/some-existing-concept",
                }
            ],
        },
    )
    code_list = new_dimension.code_list

    deserialiser = get_code_list_versioned_deserialiser(code_list)

    (
        code_list,
        json_schema_validation_errors,
        validation_errors,
    ) = deserialiser(code_list)

    concept = code_list.concepts[0]

    assert len(code_list.concepts) == 1
    assert len(json_schema_validation_errors) == 0
    assert len(validation_errors) == 0
    assert code_list.metadata.title == "Code list title"
    assert concept.label == "A"
    assert concept.code == "a"
    assert concept.description == "A data record"
    assert (
        concept.existing_concept_uri
        == "http://example.com/concepts/some-existing-concept"
    )


def test_code_list_config_v1_exact_match_error():
    """
    Tests that an error is raised as expected when trying to create a code list with
    codelist schema version 1.x but using the exact_match field (Wrong version for the config deserialiser).
    """
    new_dimension = NewDimension(
        "Dimension",
        code_list={
            "$schema": "https://purl.org/csv-cubed/code-list-config/v1.1",
            "title": "Code list title",
            "concepts": [
                {
                    "label": "A",
                    "description": "A data record",
                    "notation": "a",
                    "exact_match": "http://example.com/concepts/some-existing-concept",
                }
            ],
        },
    )

    code_list = new_dimension.code_list

    with pytest.raises(Exception) as err:
        deserialiser = get_code_list_versioned_deserialiser(code_list)

        (
            code_list,
            json_schema_validation_errors,
            validation_errors,
        ) = deserialiser(code_list)

    assert (
        "Could not match {'label': 'A', 'description': 'A data record', 'notation': 'a', 'exact_match': 'http://example.com/concepts/some-existing-concept'} with static type <class 'csvcubed.models.codelistconfig.code_list_configv1.CodeListConfigConceptV1'>"
        in str(err.value)
    )


def test_code_list_config_v2_exact_match():
    """
    Tests that a NewQBCodeList is successfully be generated when given an input config with codelist schema
    version 2.x and using the exact_match field, with the correct version of the config deserialiser.
    """
    new_dimension = NewDimension(
        "Dimension",
        code_list={
            "$schema": "https://purl.org/csv-cubed/code-list-config/v2.0",
            "title": "Code list title",
            "concepts": [
                {
                    "label": "A",
                    "description": "A data record",
                    "notation": "a",
                    "exact_match": "http://example.com/concepts/some-existing-concept",
                }
            ],
        },
    )

    code_list = new_dimension.code_list

    deserialiser = get_code_list_versioned_deserialiser(code_list)

    (
        code_list,
        json_schema_validation_errors,
        validation_errors,
    ) = deserialiser(code_list)

    concept = code_list.concepts[0]

    assert len(code_list.concepts) == 1
    assert len(json_schema_validation_errors) == 0
    assert len(validation_errors) == 0
    assert code_list.metadata.title == "Code list title"
    assert concept.label == "A"
    assert concept.code == "a"
    assert concept.description == "A data record"
    assert (
        concept.existing_concept_uri
        == "http://example.com/concepts/some-existing-concept"
    )


def test_code_list_config_v2_same_as_error():
    """
    Tests that an error is raised as expected when trying to create a code list with
    codelist schema version 2.x but using the same_as field (Wrong version for the config deserialiser).
    """
    new_dimension = NewDimension(
        "Dimension",
        code_list={
            "$schema": "https://purl.org/csv-cubed/code-list-config/v2.0",
            "title": "Code list title",
            "concepts": [
                {
                    "label": "A",
                    "description": "A data record",
                    "notation": "a",
                    "same_as": "http://example.com/concepts/some-existing-concept",
                }
            ],
        },
    )

    code_list = new_dimension.code_list

    with pytest.raises(Exception) as err:
        deserialiser = get_code_list_versioned_deserialiser(code_list)

        (
            code_list,
            json_schema_validation_errors,
            validation_errors,
        ) = deserialiser(code_list)

    assert (
        "Could not match {'label': 'A', 'description': 'A data record', 'notation': 'a', 'same_as': 'http://example.com/concepts/some-existing-concept'} with static type <class 'csvcubed.models.codelistconfig.code_list_configv2.CodeListConfigConceptV2'>"
        in str(err.value)
    )
