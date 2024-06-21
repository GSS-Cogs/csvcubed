"""
QbCube
------

Contains all of the URI definitions & configuration necessary to serialise a QbCube.
"""

from dataclasses import dataclass
from typing import List, Optional

from csvcubed.models.cube.cube import QbCube
from csvcubed.models.cube.uristyle import URIStyle


@dataclass
class NewResourceUriGenerator:
    """
    Defines all of the URIs for new resources defined in a QbCube CSV-W.
    """

    cube: QbCube

    def get_identifier_for_document(self) -> str:
        identifier = self.cube.metadata.uri_safe_identifier
        if self.cube.uri_style == URIStyle.Standard:
            return identifier + ".csv"
        elif self.cube.uri_style == URIStyle.WithoutFileExtensions:
            return identifier
        else:
            raise ValueError(f"Unhandled URI Style '{self.cube.uri_style}'.")

    def _uri_in_doc(self, identifier: str) -> str:
        """
        URIs declared in the `columns` section of the CSV-W are relative to the CSV's location.
        URIs declared in the JSON-LD metadata section of the CSV-W are relative to the metadata file's location.

        This function makes both point to the same base location - the CSV file's location. This ensures that we
        can talk about the same resources in the `columns` section and the JSON-LD metadata section.
        """
        return f"{self.get_identifier_for_document()}#{identifier}"

    def get_observation_uri(
        self, dimension_identifying_values: List[str], measure_identifier: Optional[str]
    ) -> str:
        identifying_parts = ",".join(dimension_identifying_values)
        if measure_identifier is not None:
            identifying_parts += f"@{measure_identifier}"

        return self._uri_in_doc(f"obs/{identifying_parts}")

    def get_slice_across_measures_uri(
        self, dimension_identifying_values: List[str]
    ) -> str:
        identifying_parts = ",".join(dimension_identifying_values)
        return self._uri_in_doc(f"slice/{identifying_parts}")

    def get_component_uri(self, component_identifier: str) -> str:
        return self._uri_in_doc(f"component/{component_identifier}")

    def get_measure_uri(self, measure_identifier: str) -> str:
        return self._uri_in_doc(f"measure/{measure_identifier}")

    def get_unit_uri(self, unit_identifier: str) -> str:
        return self._uri_in_doc(f"unit/{unit_identifier}")

    def get_attribute_uri(self, attribute_identifier: str) -> str:
        return self._uri_in_doc(f"attribute/{attribute_identifier}")

    def get_attribute_value_uri(
        self, attribute_identifier: str, value_identifier: str
    ) -> str:
        return self._uri_in_doc(f"attribute/{attribute_identifier}/{value_identifier}")

    def get_dimension_uri(self, dimension_identifier: str) -> str:
        return self._uri_in_doc(f"dimension/{dimension_identifier}")

    def get_slice_uri(self, slice_identifier: str) -> str:
        return self._uri_in_doc(f"slice/{slice_identifier}")

    def get_slice_key_across_measures_uri(self) -> str:
        return self.get_slice_uri("cross-measures")

    def get_class_uri(self, class_identifier: str) -> str:
        return self._uri_in_doc(f"class/{class_identifier}")

    def get_dataset_uri(self) -> str:
        return self._uri_in_doc("dataset")

    def get_distribution_uri(self) -> str:
        return self._uri_in_doc("qbDataSet")

    def get_void_dataset_dependency_uri(self, identifier: str) -> str:
        return self._uri_in_doc(f"dependency/{identifier}")

    def get_structure_uri(self) -> str:
        return self._uri_in_doc("structure")

    def get_build_activity_uri(self) -> str:
        return self._uri_in_doc("csvcubed-build-activity")
