"""
Models
------

config.json v1.* column mapping models.

If you change the shape of any model in this file, you **must** create a newly versioned JSON schema reflecting said changes.
"""

import logging
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, Optional, TypeVar, Tuple

import uritemplate

from jsonschema.exceptions import ValidationError

from csvcubedmodels.dataclassbase import DataClassBase

from csvcubed.utils.validators.schema import validate_dict_against_schema
from csvcubed.inputs import pandas_input_to_columnar_optional_str
from csvcubed.models.cube import CatalogMetadata, NewQbConcept
from csvcubed.models.cube.qb.components import (
    NewQbDimension,
    ExistingQbDimension,
    NewQbAttribute,
    NewQbAttributeValue,
    ExistingQbAttribute,
    NewQbUnit,
    ExistingQbUnit,
    QbMultiUnits,
    QbMultiMeasureDimension,
    QbMultiMeasureObservationValue,
    QbSingleMeasureObservationValue,
    ExistingQbMeasure,
    NewQbMeasure,
    QbObservationValue,
    CompositeQbCodeList,
    DuplicatedQbConcept,
    ExistingQbAttributeLiteral,
    ExistingQbCodeList,
    NewQbAttributeLiteral,
    NewQbCodeList,
    QbCodeList,
)
from csvcubed.inputs import PandasDataTypes
from csvcubed.utils.uri import (
    csvw_column_name_safe,
    looks_like_uri,
)
from csvcubed.models.codelistconfig.code_list_config import CodeListConfig
from csvcubed.utils.file import code_list_config_json_exists
from csvcubed.readers.cubeconfig.utils import load_resource

_logger = logging.getLogger(__name__)

T = TypeVar("T", bound=object)


@dataclass
class SchemaBaseClass(DataClassBase, ABC):
    ...


@dataclass
class NewDimension(SchemaBaseClass):
    # Schema property - but removed for json to dataclass mapping
    # type: # str = "dimension"

    label: Optional[str] = None
    description: Optional[str] = None
    definition_uri: Optional[str] = None
    code_list: Union[str, bool, dict, None] = True
    from_existing: Optional[str] = None
    cell_uri_template: Optional[str] = None

    def map_to_new_qb_dimension(
        self,
        csv_column_title: str,
        data: PandasDataTypes,
        cube_config_minor_version: Optional[int],
        config_path: Optional[Path] = None,
    ) -> Tuple[NewQbDimension, list[ValidationError]]:

        new_dimension = NewQbDimension.from_data(
            label=self.label or csv_column_title,
            data=data,
            description=self.description,
            parent_dimension_uri=self.from_existing,
            source_uri=self.definition_uri,
        )
        # The NewQbCodeList and Concepts are populated in the NewQbDimension.from_data() call
        # the _get_code_list method overrides the code_list if required.
        (
            new_dimension.code_list,
            code_list_schema_validation_errors,
        ) = self._get_code_list(
            new_dimension,
            csv_column_title,
            cube_config_minor_version,
            cube_config_path=config_path,
        )
        return (new_dimension, code_list_schema_validation_errors)

    def _get_code_list(
        self,
        new_dimension: NewQbDimension,
        csv_column_title: str,
        cube_config_minor_version: Optional[int],
        cube_config_path: Optional[Path],
    ) -> Tuple[Optional[QbCodeList], list[ValidationError]]:
        if isinstance(self.code_list, str):
            if looks_like_uri(self.code_list):
                return (ExistingQbCodeList(self.code_list), [])
            # The following elif is for cube config v1.1. This also requires the user to define the configuration in the build command, and therefore cube_config_path.
            elif (
                cube_config_minor_version
                and cube_config_minor_version >= 1
                and cube_config_path
                and code_list_config_json_exists(
                    Path(self.code_list), cube_config_path.parent
                )
            ):
                code_list_path = Path(self.code_list)
                code_list_config_path = (
                    code_list_path
                    if code_list_path.is_absolute()
                    else (cube_config_path.parent / code_list_path).resolve()
                )
                _logger.info(
                    f"Loading code list from local file path: {code_list_config_path}"
                )

                code_list_config, code_list_config_dict = CodeListConfig.from_json_file(
                    code_list_config_path
                )
                schema = load_resource(code_list_config.schema)

                code_list_schema_validation_errors = validate_dict_against_schema(
                    value=code_list_config_dict, schema=schema
                )

                return (
                    NewQbCodeList(
                        code_list_config.metadata, code_list_config.new_qb_concepts
                    ),
                    code_list_schema_validation_errors,
                )
            else:
                raise ValueError(
                    "Code List contains a string that cannot be recognised as a URI or a valid File Path"
                )

        elif isinstance(self.code_list, bool):
            if self.code_list is False:
                return (None, [])
            elif (
                new_dimension.parent_dimension_uri
                == "http://purl.org/linked-data/sdmx/2009/dimension#refPeriod"
                and self.cell_uri_template is not None
                and self.cell_uri_template.lower().startswith(
                    "http://reference.data.gov.uk/id/"
                )
            ):
                # This is a special case where we build up a code-list of the date/time values.
                return (
                    self._get_date_time_code_list_for_dimension(
                        new_dimension, self.cell_uri_template, csv_column_title
                    ),
                    [],
                )
            else:
                return (new_dimension.code_list, [])

        # The following elif is for cube config v1.1 and when the code list is defined inline.
        elif (
            cube_config_minor_version
            and cube_config_minor_version >= 1
            and isinstance(self.code_list, dict)
        ):
            code_list_config = CodeListConfig.from_dict(self.code_list)
            schema = load_resource(code_list_config.schema)

            code_list_schema_validation_errors = validate_dict_against_schema(
                value=code_list_config.as_dict(), schema=schema
            )

            return (
                NewQbCodeList(
                    code_list_config.metadata, code_list_config.new_qb_concepts
                ),
                code_list_schema_validation_errors,
            )
        else:
            raise ValueError(f"Unmatched code_list value {self.code_list}")

    @staticmethod
    def _get_date_time_code_list_for_dimension(
        new_dimension: NewQbDimension, cell_uri_template: str, csv_column_title: str
    ) -> CompositeQbCodeList:
        csvw_safe_column_title = csvw_column_name_safe(csv_column_title)
        assert isinstance(new_dimension.code_list, NewQbCodeList)

        return CompositeQbCodeList(
            CatalogMetadata(new_dimension.label),
            [
                DuplicatedQbConcept(
                    existing_concept_uri=uritemplate.expand(
                        cell_uri_template,
                        {csvw_safe_column_title: c.label},
                    ),
                    label=c.label,
                    code=c.code,
                )
                for c in new_dimension.code_list.concepts
                if isinstance(c, NewQbConcept)
            ],
        )


@dataclass
class ExistingDimension(SchemaBaseClass):
    from_existing: str
    cell_uri_template: Optional[str] = None

    def map_to_existing_qb_dimension(self) -> ExistingQbDimension:
        return ExistingQbDimension(dimension_uri=self.from_existing)


@dataclass
class AttributeValue(SchemaBaseClass):
    label: str
    description: Optional[str] = None
    from_existing: Optional[str] = None
    definition_uri: Optional[str] = None


@dataclass
class ExistingAttributeLiteral(SchemaBaseClass):
    from_existing: str
    data_type: str
    required: bool = False

    def map_to_existing_qb_attribute(self) -> ExistingQbAttributeLiteral:

        return ExistingQbAttributeLiteral(
            attribute_uri=self.from_existing,
            is_required=self.required,
            data_type=self.data_type,
        )


@dataclass
class ExistingAttributeResource(SchemaBaseClass):
    from_existing: str
    values: Union[bool, List[AttributeValue]] = True
    required: bool = False
    cell_uri_template: Optional[str] = None

    def map_to_existing_qb_attribute(
        self, data: PandasDataTypes
    ) -> ExistingQbAttribute:

        return ExistingQbAttribute(
            self.from_existing,
            new_attribute_values=_get_new_attribute_values(data, self.values),
            is_required=self.required,
        )


@dataclass
class NewAttributeLiteral(SchemaBaseClass):
    label: str
    data_type: str
    description: Optional[str] = None
    from_existing: Optional[str] = None
    definition_uri: Optional[str] = None
    required: bool = False

    def map_to_new_qb_attribute(self, column_title: str) -> NewQbAttributeLiteral:
        label = self.label or column_title

        return NewQbAttributeLiteral(
            label=label,
            description=self.description,
            data_type=self.data_type,
            parent_attribute_uri=self.from_existing,
            source_uri=self.definition_uri,
            is_required=self.required,
        )


@dataclass
class NewAttributeResource(SchemaBaseClass):
    label: Optional[str] = None
    description: Optional[str] = None
    from_existing: Optional[str] = None
    definition_uri: Optional[str] = None
    required: bool = False
    values: Union[bool, List[AttributeValue]] = True
    cell_uri_template: Optional[str] = None

    def map_to_new_qb_attribute(
        self, column_title: str, data: PandasDataTypes
    ) -> NewQbAttribute:
        label = self.label or column_title

        return NewQbAttribute(
            label=label,
            description=self.description,
            new_attribute_values=_get_new_attribute_values(data, self.values),
            parent_attribute_uri=self.from_existing,
            source_uri=self.definition_uri,
            is_required=self.required,
        )


@dataclass
class Unit(SchemaBaseClass):
    label: str
    description: Optional[str] = None
    from_existing: Optional[str] = None
    definition_uri: Optional[str] = None
    scaling_factor: Optional[float] = None
    si_scaling_factor: Optional[float] = None
    quantity_kind: Optional[str] = None


@dataclass
class ExistingUnits(SchemaBaseClass):
    cell_uri_template: str

    def map_to_existing_qb_multi_units(
        self, data: PandasDataTypes, column_title: str
    ) -> QbMultiUnits:
        return QbMultiUnits.existing_units_from_data(
            data, csvw_column_name_safe(column_title), self.cell_uri_template
        )


@dataclass
class NewUnits(SchemaBaseClass):
    values: Union[bool, List[Unit]] = True

    def map_to_new_qb_multi_units(self, data: PandasDataTypes) -> QbMultiUnits:
        if isinstance(self.values, bool) and self.values is True:
            return QbMultiUnits.new_units_from_data(data)

        elif isinstance(self.values, list):

            units = []
            for unit in self.values:
                if not isinstance(unit, Unit):
                    raise ValueError(f"Unexpected unit value: {unit}")

                units.append(_map_unit(unit))

            return QbMultiUnits(units)

        raise ValueError(f"Unhandled units 'values': {self}")


@dataclass
class Measure(SchemaBaseClass):
    label: str
    description: Optional[str] = None
    from_existing: Optional[str] = None
    definition_uri: Optional[str] = None

    def map_to_measure(self) -> NewQbMeasure:
        return NewQbMeasure(
            label=self.label,
            description=self.description,
            parent_measure_uri=self.from_existing,
            source_uri=self.definition_uri,
        )


@dataclass
class NewMeasures(SchemaBaseClass):
    values: Union[bool, List[Measure]] = True

    def map_to_new_multi_measure_dimension(
        self, data: PandasDataTypes
    ) -> QbMultiMeasureDimension:
        # When values is a single bool True then create new Measures from the csv column data
        if self.values is True:
            return QbMultiMeasureDimension.new_measures_from_data(data)

        elif isinstance(self.values, list):
            new_measures = []
            for new_measure in self.values:
                if not isinstance(new_measure, Measure):
                    raise ValueError(f"Unexpected measure: {new_measure}")
                new_measures.append(new_measure.map_to_measure())

            return QbMultiMeasureDimension(new_measures)

        else:
            raise ValueError(f"Unexpected measure 'values': {self.values}")


@dataclass
class ExistingMeasures(SchemaBaseClass):
    cell_uri_template: str

    def map_to_existing_multi_measure_dimension(
        self, column_title: str, data: PandasDataTypes
    ) -> QbMultiMeasureDimension:
        csvw_column_name = csvw_column_name_safe(column_title)
        return QbMultiMeasureDimension.existing_measures_from_data(
            data, csvw_column_name, self.cell_uri_template
        )


@dataclass
class ObservationValue(SchemaBaseClass):
    data_type: str = "decimal"
    unit: Union[None, str, Unit] = None
    measure: Union[None, str, Measure] = None

    def map_to_qb_observation(self) -> QbObservationValue:
        unit = None
        if isinstance(self.unit, str):
            unit = ExistingQbUnit(unit_uri=self.unit)

        elif isinstance(self.unit, Unit):
            unit = _map_unit(self.unit)

        elif self.unit is not None:
            raise ValueError(f"Unexpected unit: {self.unit}")

        if self.measure is None:
            # Multi-measure cube
            return QbMultiMeasureObservationValue(data_type=self.data_type, unit=unit)
        else:
            # Single measure qb
            measure = None
            if isinstance(self.measure, str):
                measure = ExistingQbMeasure(self.measure)

            elif isinstance(self.measure, Measure):
                measure = _map_measure(self.measure)

            else:
                raise ValueError(f"Unhandled measure type: {self.measure}")

            return QbSingleMeasureObservationValue(
                measure=measure, unit=unit, data_type=self.data_type or "decimal"
            )


def _map_unit(resource: Unit) -> NewQbUnit:
    return NewQbUnit(
        label=resource.label,
        description=resource.description,
        source_uri=resource.from_existing,
        base_unit=(
            None
            if resource.from_existing is None
            else ExistingQbUnit(resource.from_existing)
        ),
        base_unit_scaling_factor=resource.scaling_factor,
        qudt_quantity_kind_uri=resource.quantity_kind,
        si_base_unit_conversion_multiplier=resource.si_scaling_factor,
    )


def _map_measure(resource: Measure) -> NewQbMeasure:
    return NewQbMeasure(
        label=resource.label,
        description=resource.description,
        source_uri=resource.definition_uri,
        parent_measure_uri=resource.from_existing,
    )


def _map_attribute_values(
    new_attribute_values_from_schema: List[AttributeValue],
) -> List[NewQbAttributeValue]:
    new_attribute_values = []
    for attr_val in new_attribute_values_from_schema:
        if not isinstance(attr_val, AttributeValue):
            raise ValueError(f"Found unexpected attribute value {attr_val}")

        new_attribute_values.append(
            NewQbAttributeValue(
                label=attr_val.label,
                description=attr_val.description,
                source_uri=attr_val.definition_uri,
                # uri_safe_identifier_override=attr_val.path,
            )
        )
    return new_attribute_values


def _get_new_attribute_values(
    data: PandasDataTypes,
    new_attribute_values: Union[bool, List[AttributeValue]],
) -> List[NewQbAttributeValue]:
    if isinstance(new_attribute_values, bool):
        if new_attribute_values:
            columnar_data: List[str] = [
                v for v in pandas_input_to_columnar_optional_str(data) if v is not None
            ]
            return [NewQbAttributeValue(v) for v in sorted(set(columnar_data))]

        return []
    elif isinstance(new_attribute_values, list):
        return _map_attribute_values(new_attribute_values)

    raise ValueError(
        f"Unexpected value for 'newAttributeValues': {new_attribute_values}"
    )
