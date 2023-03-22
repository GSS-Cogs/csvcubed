# This script contain a set of function that can be used to validate specific class attributes/ member variables
import datetime as dt
from enum import Enum
from math import isinf, isnan
from pathlib import Path
from typing import Any, Callable, List, Optional, Type, TypeVar

from csvcubed.models.cube.qb.components.constants import ACCEPTED_DATATYPE_MAPPING
from csvcubed.models.validatedmodel import ValidatedModel, ValidationFunction
from csvcubed.models.validationerror import ValidateModelPropertiesError
from csvcubed.utils.uri import looks_like_uri

T = TypeVar("T")


def validate_list(
    validate_list_item: Callable[[T, str], List[ValidateModelPropertiesError]],
) -> Callable[[List[T], str], List[ValidateModelPropertiesError]]:
    """
    This function will validate if the argument provided is in fact a list and,
    in a loop will check each member of the list and returns any errors returned by the item validation function.
    """

    def _validate(
        list_items: List[T], property_path: List[str]
    ) -> List[ValidateModelPropertiesError]:
        if not isinstance(list_items, list):
            return [
                ValidateModelPropertiesError(
                    f"The value '{list_items}' should be a list. Check the following variable at the property path: '{property_path}'",
                    property_path,
                    list_items,
                )
            ]

        return [
            err
            for list_item in list_items
            for err in validate_list_item(list_item, property_path)
        ]

    return _validate


def validate_str_type(
    value: str, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function will validate if the argument provided is in fact a string type and,
    returns any errors returned by the item validation function.
    """
    if not isinstance(value, str):
        return [
            ValidateModelPropertiesError(
                f"The value '{value}' should be a string. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]

    return []


def validate_uri(
    value: str, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function will validate if the argument provided is in fact a string type and,
    check is the string contains a uri. Either checks fail it returns any errors returned by the item validation function.
    """
    errors = validate_str_type(value, property_path)
    if any(errors):
        return errors

    if not looks_like_uri(value):
        return [
            ValidateModelPropertiesError(
                f"The value '{value}' should be a URI. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]

    return []


def validate_int_type(
    value: int, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function will validate if the argument provided is in fact a integer type and,
    returns any errors returned by the item validation function.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return [
            ValidateModelPropertiesError(
                f"The value '{value}' should be an integer. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]

    return []


def boolean(
    value: bool, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function will validate if the argument provided is in fact a boolean type and,
    returns and error if it isn't.
    """
    if not isinstance(value, bool):
        return [
            ValidateModelPropertiesError(
                f"This value '{value}' should be a boolean value. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]

    return []


def validate_optional(
    validate_item: Callable[[T, str], List[ValidateModelPropertiesError]]
) -> Callable[[Optional[T], str], List[ValidateModelPropertiesError]]:
    """
    This function will validate if the Optional argument provided is a None value it will return an empty list,
    else it returns any errors returned by the item validation function .
    """

    def _validate(
        maybe_item: Optional[T], property_path: List[str]
    ) -> List[ValidateModelPropertiesError]:
        if maybe_item is None:
            return []

        return validate_item(maybe_item, property_path)

    return _validate


def validate_float_type(
    value: float, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function will validate if the argument provided is in fact a float type and,
    returns any errors returned by the item validation function.
    """
    if not isinstance(value, float):
        return [
            ValidateModelPropertiesError(
                f"The value '{value}' should be a float. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]
    elif isnan(value):
        return [
            ValidateModelPropertiesError(
                f"The value '{value}' should be a float but is Not a Number (NaN). Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]
    elif isinf(value):
        return [
            ValidateModelPropertiesError(
                f"The value '{value}' should be a float but is +-infinity. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]

    return []


def validate_file(
    value: Path, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function validates whether the given argument is in fact of type Path, and if not,
    returns any validation errors raised by the validation function.
    """
    if isinstance(value, Path):
        if not value.exists():
            return [
                ValidateModelPropertiesError(
                    f"The file '{value}' does not exist. Check the following variable at the property path: '{property_path}'",
                    property_path,
                    value,
                )
            ]
        else:
            return []
    else:
        return [
            ValidateModelPropertiesError(
                f"The file '{value}' is not a valid file path. Check the following variable at the property path: '{property_path}'",
                property_path,
                value,
            )
        ]


def any_of(*conditions: ValidationFunction) -> ValidationFunction:
    """
    This function will validate if the argument provided is an instance of any of the types
    specified. (Useful for Unions.) Returns any errors returned by the validation function.
    """

    def validate(
        value: Any, property_path: List[str]
    ) -> List[ValidateModelPropertiesError]:
        all_errors = []
        for condition in conditions:
            errs = condition(value, property_path)
            if not any(errs):
                return []
            all_errors += errs

        return [
            ValidateModelPropertiesError(
                f"The value '{value}' does not satisfy any single condition for variable at the property path: '{property_path}'",
                property_path,
                value,
            ),
            *all_errors,
        ]

    return validate


def enum(enum_type: Type[Enum]) -> ValidationFunction:
    """
    This function will validate if the argument provided is in fact an enum type and,
    returns any errors returned by the validation function.
    """

    def validate(
        value: Any, property_path: List[str]
    ) -> List[ValidateModelPropertiesError]:
        for enum_value in enum_type:
            if value == enum_value:
                return []

        return [
            ValidateModelPropertiesError(
                f"Could not find matching enum value for '{value}' in {enum_type.__name__} at property path: {property_path}",
                property_path,
                value,
            )
        ]

    return validate


def data_type(
    data_type: str, property_path: List[str]
) -> List[ValidateModelPropertiesError]:
    """
    This function will validate if the argument provided is a member of the accepted data types,
    and returns any errors that are raised.
    """
    if data_type not in ACCEPTED_DATATYPE_MAPPING.keys():
        return [
            ValidateModelPropertiesError(
                f"'{data_type}' is not recognised as a valid data type. Check the following variable at the property path: '{property_path}'",
                property_path,
                data_type,
            )
        ]
    return []


def validated_model(validated_model_type: Type[ValidatedModel]):
    """
    Performs the standard validation of any object which inherits from ValidatedModel.

    This saves us from having to write a validation function for each class which
    implements/inherits from ValidatedModel.
    """

    if not issubclass(validated_model_type, ValidatedModel):
        # This error is really for developers when running tests.
        raise TypeError(
            f"Type '{validated_model_type}' is not an instance of {ValidatedModel.__name__}."
            f"This function is only designed to work with types which extend {ValidatedModel.__name__}."
        )

    def validate(
        value: ValidatedModel, property_path: List[str]
    ) -> List[ValidateModelPropertiesError]:
        if not isinstance(value, validated_model_type):
            # This error occurs when runtime validation occurs.
            return [
                ValidateModelPropertiesError(
                    f"Value '{value}' was not an instance of the expected type '{validated_model_type.__name__}'. Check the following variable at the property path: '{property_path}'",
                    property_path,
                    value,
                )
            ]

        return value.validate(property_path=property_path)

    return validate


def is_instance_of(expect_instance_type: Type[object]) -> ValidationFunction:
    """
    Validation function that can apply type validation to class properties in a generic manner,
    by specifying what instance/type of object to expect. This saves effort from having to create
    custom validation functions for specific types that do not inherit from ValidatedModel.
    """

    def _validate(
        value: Any, property_path: List[str]
    ) -> List[ValidateModelPropertiesError]:
        if not isinstance(value, expect_instance_type):
            return [
                ValidateModelPropertiesError(
                    f"Value '{value}' was not an instance of the expected type '{expect_instance_type.__name__}'. Check the following variable at the property path: '{property_path}'",
                    property_path,
                    value,
                ),
            ]
        return []

    return _validate
