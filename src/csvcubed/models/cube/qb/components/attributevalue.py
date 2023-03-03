"""
Attribute Values
----------------

Represent values for Attributes in an RDF Data Cube.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from csvcubed.models.uriidentifiable import UriIdentifiable
from csvcubed.models.validatedmodel import ValidationFunction
from csvcubed.utils import validations as v
from csvcubed.utils.validations import (
    validate_list,
    validate_optional,
    validate_str_type,
    validate_uri,
)

from .arbitraryrdf import ArbitraryRdf, RdfSerialisationHint, TripleFragmentBase
from .datastructuredefinition import SecondaryQbStructuralDefinition


@dataclass
class NewQbAttributeValue(
    SecondaryQbStructuralDefinition, UriIdentifiable, ArbitraryRdf
):
    label: str
    description: Optional[str] = field(default=None, repr=False)
    uri_safe_identifier_override: Optional[str] = field(default=None, repr=False)
    source_uri: Optional[str] = field(default=None, repr=False)
    parent_attribute_value_uri: Optional[str] = field(default=None, repr=False)
    arbitrary_rdf: List[TripleFragmentBase] = field(default_factory=list, repr=False)

    def _get_arbitrary_rdf(self) -> List[TripleFragmentBase]:
        return self.arbitrary_rdf

    def get_default_node_serialisation_hint(self) -> RdfSerialisationHint:
        return RdfSerialisationHint.AttributeValue

    def get_permitted_rdf_fragment_hints(self) -> Set[RdfSerialisationHint]:
        return {RdfSerialisationHint.AttributeValue}

    def get_identifier(self) -> str:
        return self.label

    def _get_validations(self) -> Dict[str, ValidationFunction]:

        return {
            "label": validate_str_type,
            "description": validate_optional(validate_str_type),
            **UriIdentifiable._get_validations(self),
            "source_uri": validate_optional(validate_uri),
            "parent_attribute_value_uri": validate_optional(validate_uri),
            "arbitrary_rdf": validate_list(v.validated_model(TripleFragmentBase)),
        }
