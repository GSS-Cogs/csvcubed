import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Type

from csvcubed import feature_flags
from csvcubed.definitions import QB_MEASURE_TYPE_DIMENSION_URI, SDMX_ATTRIBUTE_UNIT_URI
from csvcubed.models.cube.columns import CsvColumn
from csvcubed.models.cube.cube import QbColumnarDsdType, QbCube
from csvcubed.models.cube.qb.columns import QbColumn
from csvcubed.models.cube.qb.components.attribute import (
    ExistingQbAttribute,
    NewQbAttribute,
    QbAttribute,
)
from csvcubed.models.cube.qb.components.codelist import (
    ExistingQbCodeList,
    NewQbCodeList,
    QbCodeList,
)
from csvcubed.models.cube.qb.components.dimension import (
    ExistingQbDimension,
    NewQbDimension,
    QbDimension,
)
from csvcubed.models.cube.qb.components.measure import (
    ExistingQbMeasure,
    NewQbMeasure,
    QbMeasure,
)
from csvcubed.models.cube.qb.components.measuresdimension import QbMultiMeasureDimension
from csvcubed.models.cube.qb.components.observedvalue import QbObservationValue
from csvcubed.models.cube.qb.components.unit import ExistingQbUnit, NewQbUnit, QbUnit
from csvcubed.models.cube.qb.components.unitscolumn import QbMultiUnits
from csvcubed.utils.uri import csvw_column_name_safe, uri_safe
from csvcubed.writers.helpers.skoscodelistwriter.constants import SCHEMA_URI_IDENTIFIER
from csvcubed.writers.helpers.skoscodelistwriter.newresourceurigenerator import (
    NewResourceUriGenerator as SkosCodeListNewResourceUriGenerator,
)

from .newresourceurigenerator import NewResourceUriGenerator

_logger = logging.getLogger(__name__)


@dataclass
class UriHelper:
    """
    Defines all of the URIs and URI templates used in an RDF Data Cube CSV-W.
    """

    cube: QbCube
    _new_resource_uri_generator: NewResourceUriGenerator = field(init=False)

    def __post_init__(self):
        _logger.debug("Initialising %s", UriHelper.__name__)
        self._new_resource_uri_generator = NewResourceUriGenerator(self.cube)

    def get_dataset_uri(self) -> str:
        return self._new_resource_uri_generator.get_dataset_uri()

    def get_distribution_uri(self) -> str:
        return self._new_resource_uri_generator.get_distribution_uri()

    def get_slice_key_across_measures_uri(self) -> str:
        return self._new_resource_uri_generator.get_slice_key_across_measures_uri()

    def get_structure_uri(self) -> str:
        return self._new_resource_uri_generator.get_structure_uri()

    def get_component_uri(self, component_identifier: str) -> str:
        return self._new_resource_uri_generator.get_component_uri(component_identifier)

    def get_class_uri(self, class_identifier: str) -> str:
        return self._new_resource_uri_generator.get_class_uri(class_identifier)

    def get_void_dataset_dependency_uri(self, identifier: str) -> str:
        return self._new_resource_uri_generator.get_void_dataset_dependency_uri(
            identifier
        )

    def get_build_activity_uri(self) -> str:
        return self._new_resource_uri_generator.get_build_activity_uri()

    def get_new_attribute_value_uri(
        self, attribute_identifier: str, attribute_value_identifier: str
    ) -> str:
        return self._new_resource_uri_generator.get_attribute_value_uri(
            attribute_identifier, attribute_value_identifier
        )

    def get_dimension_uri(self, dimension: QbDimension) -> str:
        if isinstance(dimension, NewQbDimension):
            dimension_uri = self._new_resource_uri_generator.get_dimension_uri(
                dimension.uri_safe_identifier
            )
            _logger.debug(
                "The dimension is a new dimension with uri '%s'",
                dimension_uri,
            )
            return dimension_uri
        elif isinstance(dimension, ExistingQbDimension):
            dimension_uri = dimension.dimension_uri
            _logger.debug(
                "The dimension is an existing dimension with uri '%s'",
                dimension_uri,
            )
            return dimension_uri
        else:
            raise TypeError(f"Unmatched {QbDimension.__name__} type {type(dimension)}")

    def get_measure_uri(self, measure: QbMeasure) -> str:
        if isinstance(measure, NewQbMeasure):
            measure_uri = self._new_resource_uri_generator.get_measure_uri(
                measure.uri_safe_identifier
            )
            _logger.debug(
                "The measure is a new dimension with uri '%s'",
                measure_uri,
            )
            return measure_uri
        elif isinstance(measure, ExistingQbMeasure):
            measure_uri = measure.measure_uri
            _logger.debug(
                "The measure is an existing dimension with uri '%s'",
                measure_uri,
            )
            return measure_uri
        else:
            raise TypeError(f"Unmatched {QbMeasure.__name__} type {type(measure)}")

    def get_unit_uri(self, unit: QbUnit) -> str:
        if isinstance(unit, ExistingQbUnit):
            return unit.unit_uri
        elif isinstance(unit, NewQbUnit):
            return self._new_resource_uri_generator.get_unit_uri(
                unit.uri_safe_identifier
            )
        else:
            raise TypeError(f"Unmatched unit type {type(unit)}")

    def get_attribute_uri(self, attribute: QbAttribute) -> str:
        if isinstance(attribute, NewQbAttribute):
            _logger.debug("The attribute %s is a new attribute", attribute.label)
            attribute_uri = self._new_resource_uri_generator.get_attribute_uri(
                attribute.uri_safe_identifier
            )
            _logger.debug(
                "The attribute %s is a new attribute with uri '%s'",
                attribute.label,
                attribute_uri,
            )
            return attribute_uri
        elif isinstance(attribute, ExistingQbAttribute):
            attribute_uri = attribute.attribute_uri
            _logger.debug(
                "The attribute is an existing attribute with uri '%s'",
                attribute_uri,
            )
            return attribute_uri
        else:
            raise TypeError(f"Unmatched {QbAttribute.__name__} type {type(attribute)}")

    def get_about_url(self) -> str:
        about_url_template = (
            self._get_pivoted_cube_slice_uri()
            if self.cube.is_pivoted_shape
            else self._get_observation_uri_for_standard_shape_data_set()
        )

        _logger.debug("aboutUrl template is %s", about_url_template)
        return about_url_template

    def get_about_url_for_csvw_col_in_pivoted_shape_cube(
        self, column: QbColumn
    ) -> Optional[str]:
        obs_val_cols = self.cube.get_columns_of_dsd_type(QbObservationValue)
        _logger.debug(
            "Getting aboutUrl for column with title '%s'", column.csv_column_title
        )

        obs_val_col: Optional[QbColumn[QbObservationValue]]
        # If the column represents a QbObservationValue, then simply assign the obs_val_column to this column.
        if isinstance(column.structural_definition, QbObservationValue):
            _logger.debug(
                "Column %s is a observation value column", column.csv_column_title
            )
            obs_val_col = column
        elif isinstance(column.structural_definition, QbAttribute):
            # If the column represents an attribute, set the valueUrl using the _get_observation_value_col_for_title
            # function
            _logger.debug("Column %s is an attribute column", column.csv_column_title)
            col_title = column.structural_definition.get_observed_value_col_title()
            obs_val_col = self._get_obs_val_col_described_by_csv_col(
                col_title, obs_val_cols
            )
        # If the column represents units, set the valueUrl using the _get_observation_value_col_for_title function
        elif isinstance(column.structural_definition, QbMultiUnits):
            _logger.debug("Column %s is a multi-units column", column.csv_column_title)
            col_title = column.structural_definition.observed_value_col_title
            obs_val_col = self._get_obs_val_col_described_by_csv_col(
                col_title, obs_val_cols
            )
        else:
            obs_val_col = None

        return (
            self.get_observation_uri_for_pivoted_shape_data_set(obs_val_col)
            if obs_val_col is not None
            else None
        )

    def get_default_property_value_uris_for_column(
        self, column: QbColumn
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns `propertyUrl` and `valueUrl` templates for the associated CSV-W column.

        Overrides such as the `cell_uri_template` are not applied in this function. This returns the default values for
        the column.
        """
        _logger.debug(
            "Getting default propertyUrl and valueUrl for column with title '%s'",
            column.csv_column_title,
        )

        if isinstance(column.structural_definition, QbDimension):
            _logger.debug("Column %s is a dimension column", column.csv_column_title)
            return self._get_default_property_value_uris_for_dimension(column)
        elif isinstance(column.structural_definition, QbAttribute):
            _logger.debug("Column %s is an attribute column", column.csv_column_title)
            return self._get_default_property_value_uris_for_attribute(column)
        elif isinstance(column.structural_definition, QbMultiUnits):
            _logger.debug("Column %s is a multi-units column", column.csv_column_title)
            return self._get_default_property_value_uris_for_multi_units(column)
        elif isinstance(column.structural_definition, QbMultiMeasureDimension):
            _logger.debug(
                "Column %s is a multi-measure dimension column", column.csv_column_title
            )
            return self._get_default_property_value_uris_for_multi_measure(column)
        elif isinstance(column.structural_definition, QbObservationValue):
            _logger.debug(
                "Column %s is an observation value column", column.csv_column_title
            )
            return self._get_default_property_value_uris_for_observation_value(
                column.structural_definition
            )
        else:
            raise TypeError(
                f"Unhandled component type {type(column.structural_definition)}"
            )

    def get_observation_uri_for_pivoted_shape_data_set(
        self, obs_val_column: QbColumn[QbObservationValue]
    ) -> str:
        """
        Provide the obervation uri for the pivoted shape data set
        """
        _logger.debug(
            "Getting observation uri for the observation value column with title '%s'",
            obs_val_column.csv_column_title,
        )

        dimension_columns_templates: List[str] = []
        for c in self.cube.columns:
            if isinstance(c, QbColumn):
                if isinstance(c.structural_definition, QbDimension):
                    col_template_uri = c.uri_safe_identifier
                    _logger.debug(
                        "Detected a dimension column in the cube, hence setting the column template uri '%s'",
                        col_template_uri,
                    )
                    dimension_columns_templates.append(
                        f"{{{csvw_column_name_safe(col_template_uri)}}}"
                    )

        obs_val_measure = obs_val_column.structural_definition.measure
        assert obs_val_measure is not None
        _logger.debug("Observation value column has a measure %s.", obs_val_measure)

        if isinstance(obs_val_measure, NewQbMeasure):
            measure_id = obs_val_measure.uri_safe_identifier
            _logger.debug("The measure is a new measure with id '%s'", measure_id)
        elif isinstance(obs_val_measure, ExistingQbMeasure):
            # Yes, this is absolutely nasty, but what else can we do?
            measure_id = uri_safe(obs_val_measure.measure_uri)
            _logger.debug("The measure is an existing measure with id '%s'", measure_id)
        else:
            raise TypeError(f"Unhandled QbMeasure type {type(obs_val_measure)}")

        return self._new_resource_uri_generator.get_observation_uri(
            dimension_columns_templates, measure_id
        )

    def _get_default_value_uri_for_code_list_concepts(
        self, column: CsvColumn, code_list: QbCodeList
    ) -> str:
        column_uri_fragment = self._get_column_uri_template_fragment(column)

        if isinstance(code_list, ExistingQbCodeList):
            legacy_external_match = self._legacy_external_code_list_pattern.match(
                code_list.concept_scheme_uri
            )
            legacy_local_match = self._legacy_dataset_local_code_list_pattern.match(
                code_list.concept_scheme_uri
            )
            csvcubed_match = self._csvcubed_code_list_pattern.match(
                code_list.concept_scheme_uri
            )
            if legacy_external_match:
                _logger.debug(
                    "Existing concept scheme URI %s matches legacy family/global style.",
                    code_list.concept_scheme_uri,
                )
                m: re.Match = legacy_external_match
                # ConceptScheme URI:
                # http://gss-data.org.uk/def/concept-scheme/{code-list-name}
                # Concept URI:
                # http://gss-data.org.uk/def/concept-scheme/{code-list-name}/{notation}
                return f"{m.group(1)}/concept-scheme/{m.group(2)}/{column_uri_fragment}"
            elif legacy_local_match:
                _logger.debug(
                    "Existing concept scheme URI %s matches legacy dataset-local style.",
                    code_list.concept_scheme_uri,
                )
                m: re.Match = legacy_local_match
                # ConceptScheme URI:
                # http://gss-data.org.uk/data/gss_data/{family-name}/{dataset-root-name}#scheme/{code-list-name}
                # Concept URI:
                # http://gss-data.org.uk/data/gss_data/{family-name}/{dataset-root-name}#concept/{code-list-name}/{notation}
                return f"{m.group(1)}#concept/{m.group(2)}/{column_uri_fragment}"
            elif csvcubed_match:
                _logger.debug(
                    "Existing concept scheme URI %s matches csvcubed style.",
                    code_list.concept_scheme_uri,
                )
                m: re.Match = csvcubed_match
                # ConceptScheme URI:
                # {code-list-uri}#code-list
                # Concept URI:
                # {code-list-uri}#{notation}
                return f"{m.group(1)}#{column_uri_fragment}"
            else:
                _logger.warning(
                    "Existing code list URI %s does not match expected any known convention.",
                    code_list.concept_scheme_uri,
                )
                # Unexpected code-list URI. Does not match expected conventions.
                return column_uri_fragment
        elif isinstance(code_list, NewQbCodeList):
            _logger.debug(
                "valueUrl defined by new dataset-local code list %s",
                code_list.metadata.title,
            )
            return SkosCodeListNewResourceUriGenerator(
                code_list, self.cube.uri_style
            ).get_concept_uri(column_uri_fragment)
        else:
            raise TypeError(f"Unhandled codelist type {type(code_list)}")

    @staticmethod
    def _get_column_uri_template_fragment(
        column: CsvColumn, escape_value: bool = False
    ) -> str:
        if escape_value:
            return "{" + csvw_column_name_safe(column.uri_safe_identifier) + "}"

        return "{+" + csvw_column_name_safe(column.uri_safe_identifier) + "}"

    def _get_observation_value_col_for_title(
        self, col_title: str
    ) -> QbColumn[QbObservationValue]:
        """
        Gets the matching observation value column for the given attributes/units column (if there is one).
        """
        _logger.debug(
            "Getting the matching observation value column for the column with title '%s'",
            col_title,
        )

        obs_value_columns = self.cube.get_columns_of_dsd_type(QbObservationValue)
        obs_columns_for_column = [
            obs_col
            for obs_col in obs_value_columns
            if col_title == obs_col.csv_column_title
        ]

        num_of_obs_val_cols = len(obs_columns_for_column)
        _logger.debug(
            "Found %d observation value column(s) for the column with title '%s'",
            num_of_obs_val_cols,
            col_title,
        )
        if num_of_obs_val_cols != 1:
            raise AssertionError(
                f'Could not find one observation value column. Found {num_of_obs_val_cols} for title: "{col_title}".'
            )
        return obs_columns_for_column[0]

    def _get_obs_val_col_described_by_csv_col(
        self,
        col_title: Optional[str],
        obs_val_cols: List[QbColumn[QbObservationValue]],
    ) -> Optional[QbColumn[QbObservationValue]]:
        """
        Return the obs val column which a particular CSV column describes.

        Looks up the obs val column by its `col_title`, but this is optional in data sets where there is only
        one obs val column.
        """

        _logger.debug(
            "Getting observation value column for column title '%s'", col_title
        )
        obs_val_col: Optional[QbColumn[QbObservationValue]] = None

        if len(obs_val_cols) == 1:
            # Only one obs val column so it's clear which one our column describes.
            _logger.debug("The cube has a single obs val column %s.", obs_val_cols[0])
            obs_val_col = obs_val_cols[0]
        else:
            _logger.debug("The cube has multiple obs val columns %s.", obs_val_cols)
            if col_title is not None:
                obs_val_col = self._get_observation_value_col_for_title(col_title)

        if obs_val_col is not None:
            _logger.debug(
                "Observation value column for column title '%s' is '%s'",
                col_title,
                obs_val_col.csv_column_title,
            )
        else:
            _logger.warning(
                "Could not find observation value column for title '%s'", col_title
            )

        return obs_val_col

    def _get_pivoted_cube_slice_uri(self) -> str:
        # TODO: Dimensions are currently appended in the order in which the appear in the cube.
        #       We may want to alter this in the future so that the ordering is from
        #       least entropic dimension -> most entropic.
        #       E.g. http://base-uri/observations/male/1996/all-males-1996

        dimension_columns_templates: List[str] = [
            f"{{{csvw_column_name_safe(c.uri_safe_identifier)}}}"
            for c in self.cube.get_columns_of_dsd_type(QbDimension)
        ]
        _logger.debug(
            "The cube has %d dimension column templates",
            len(dimension_columns_templates),
        )

        return self._new_resource_uri_generator.get_slice_across_measures_uri(
            dimension_columns_templates
        )

    _legacy_external_code_list_pattern = re.compile("^(.*)/concept-scheme/(.*)$")
    _legacy_dataset_local_code_list_pattern = re.compile("^(.*)#scheme/(.*)$")
    _csvcubed_code_list_pattern = re.compile(
        "^(.*)#" + re.escape(SCHEMA_URI_IDENTIFIER) + "$"
    )

    def _get_observation_uri_for_standard_shape_data_set(self) -> str:
        dimension_columns_templates: List[str] = []
        multi_measure_col_template: Optional[str] = None

        for c in self.cube.columns:
            if isinstance(c, QbColumn):
                if isinstance(c.structural_definition, QbDimension):
                    dimension_columns_templates.append(
                        f"{{{csvw_column_name_safe(c.uri_safe_identifier)}}}"
                    )
                elif isinstance(c.structural_definition, QbMultiMeasureDimension):
                    multi_measure_col_template = (
                        f"{{{csvw_column_name_safe(c.uri_safe_identifier)}}}"
                    )
        return self._new_resource_uri_generator.get_observation_uri(
            dimension_columns_templates, multi_measure_col_template
        )

    def _get_default_property_value_uris_for_dimension(
        self, column: QbColumn[QbDimension]
    ) -> Tuple[str, Optional[str]]:
        dimension = column.structural_definition
        dimension_uri = self.get_dimension_uri(dimension)
        if isinstance(dimension, ExistingQbDimension):
            return (
                dimension_uri,
                self._get_column_uri_template_fragment(column),
            )
        elif isinstance(dimension, NewQbDimension):
            value_uri = self._get_column_uri_template_fragment(column)
            if dimension.code_list is None:
                _logger.debug(
                    "Dimension %s does not have code list; valueUrl defaults directly to column's value.",
                    dimension.label,
                )
            else:
                _logger.debug(
                    "Dimension %s valueUrl determined by code list %s.",
                    dimension.label,
                    dimension.code_list,
                )
                value_uri = self._get_default_value_uri_for_code_list_concepts(
                    column, dimension.code_list
                )
            return dimension_uri, value_uri
        else:
            raise TypeError(f"Unhandled dimension type {type(dimension)}")

    def _get_default_property_value_uris_for_attribute(
        self, column: QbColumn[QbAttribute]
    ) -> Tuple[str, str]:
        attribute = column.structural_definition
        column_uri_fragment = self._get_column_uri_template_fragment(column)
        value_uri = self._get_column_uri_template_fragment(column)

        attribute_uri = self.get_attribute_uri(attribute)

        if isinstance(attribute, ExistingQbAttribute):
            _logger.debug(
                "Existing Attribute %s does not have new attribute values.",
                column.csv_column_title,
            )
            return attribute_uri, value_uri
        elif isinstance(attribute, NewQbAttribute):
            if attribute.code_list is None:
                _logger.debug(
                    "New Attribute %s does not have a code list; valueUrl defaults directly to column value",
                    column.csv_column_title,
                )
            else:
                if feature_flags.ATTRIBUTE_VALUE_CODELISTS:
                    _logger.debug(
                        "Attribute %s valueUrl determined by code list %s",
                        column.csv_column_title,
                        attribute.code_list,
                    )
                    value_uri = self._get_default_value_uri_for_code_list_concepts(
                        column, attribute.code_list
                    )
                else:
                    _logger.debug(
                        "New Attribute %s has new attribute values which define the valueUrl.",
                        column.csv_column_title,
                    )
                    value_uri = self.get_new_attribute_value_uri(
                        attribute.uri_safe_identifier, column_uri_fragment
                    )

            # N.B. We can't do mix-and-match New/Existing attribute values.

            return attribute_uri, value_uri
        else:
            raise TypeError(f"Unhandled attribute type {type(attribute)}")

    def _get_default_property_value_uris_for_multi_units(
        self, column: QbColumn[QbMultiUnits]
    ) -> Tuple[str, str]:
        unit_value_uri = self._get_unit_column_unit_template_uri(column)

        return (
            SDMX_ATTRIBUTE_UNIT_URI,
            unit_value_uri,
        )

    def _get_default_property_value_uris_for_multi_measure(
        self, column: QbColumn[QbMultiMeasureDimension]
    ) -> Tuple[str, str]:
        measure_value_uri = self._get_measure_dimension_column_measure_template_uri(
            column
        )

        return QB_MEASURE_TYPE_DIMENSION_URI, measure_value_uri

    def _get_default_property_value_uris_for_observation_value(
        self,
        observation_value: QbObservationValue,
    ):
        if observation_value.is_pivoted_shape_observation:
            assert observation_value.measure is not None
            _logger.debug(
                "Single-measure observation value propertyUrl defined by measure %s",
                observation_value.measure,
            )
            return self.get_measure_uri(observation_value.measure), None
        else:
            # In the standard shape
            multi_measure_dimension_col = self._get_single_column_of_type(
                QbMultiMeasureDimension
            )
            _logger.debug(
                "Multi-measure observation value propertyUrl defined by measure column %s",
                multi_measure_dimension_col.csv_column_title,
            )

            measure_uri_template = (
                self._get_measure_dimension_column_measure_template_uri(
                    multi_measure_dimension_col
                )
            )
            return measure_uri_template, None

    def _get_unit_column_unit_template_uri(self, column: QbColumn[QbMultiUnits]):
        column_template_fragment = self._get_column_uri_template_fragment(column)
        all_units_new = all(
            [isinstance(u, NewQbUnit) for u in column.structural_definition.units]
        )
        all_units_existing = all(
            [isinstance(u, ExistingQbUnit) for u in column.structural_definition.units]
        )
        unit_value_uri: str
        if all_units_new:
            _logger.debug(
                "All units are new; they define the %s column's valueUrl.",
                column.csv_column_title,
            )
            unit_value_uri = self._new_resource_uri_generator.get_unit_uri(
                column_template_fragment
            )
        elif all_units_existing:
            _logger.debug("All units are existing.")
            unit_value_uri = column_template_fragment
        else:
            # TODO: Come up with a solution for this.
            raise Exception(
                "Cannot handle a mix of new units and existing defined units."
            )
        return unit_value_uri

    def _get_measure_dimension_column_measure_template_uri(
        self, column: QbColumn[QbMultiMeasureDimension]
    ):
        all_measures_new = all(
            [isinstance(m, NewQbMeasure) for m in column.structural_definition.measures]
        )
        all_measures_existing = all(
            [
                isinstance(m, ExistingQbMeasure)
                for m in column.structural_definition.measures
            ]
        )

        column_template_fragment = self._get_column_uri_template_fragment(column)
        if all_measures_new:
            _logger.debug(
                "All measures are new; they define the %s column's valueUrl.",
                column.csv_column_title,
            )
            return self._new_resource_uri_generator.get_measure_uri(
                column_template_fragment
            )
        elif all_measures_existing:
            _logger.debug("All measures are existing.")
            if column.csv_column_uri_template is None:
                raise ValueError(
                    "A URI value template must be defined when a measures column reuses existing measures."
                )
            return column.csv_column_uri_template
        else:
            # TODO: Come up with a solution for this.
            raise Exception(
                "Cannot handle a mix of new measures and existing defined measures."
            )

    def _get_single_column_of_type(
        self, t: Type[QbColumnarDsdType]
    ) -> QbColumn[QbColumnarDsdType]:
        cols = self.cube.get_columns_of_dsd_type(t)
        if len(cols) != 1:
            raise ValueError(
                f"Found {len(cols)} columns with component type {t} in cube. Expected 1."
            )
        return cols[0]
