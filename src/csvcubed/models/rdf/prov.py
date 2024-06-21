"""
PROV Ontology Models
--------------------

This module holds some models in the prov-o ontology.
"""

from typing import Annotated

from csvcubedmodels.rdf import (
    ExistingResource,
    NewResource,
    PropertyStatus,
    Resource,
    Triple,
    map_resource_to_uri,
    map_str_to_en_literal,
)
from csvcubedmodels.rdf.namespaces import PROV
from rdflib import DCTERMS


class Activity(NewResource):
    """
    This class represents the PROV-O ontology's activity class.
    prov:used is a property used to describe a prov:activty.
    """

    used: Annotated[
        ExistingResource,
        Triple(PROV.used, PropertyStatus.optional, map_resource_to_uri),
    ]

    def __init__(self, uri: str):
        NewResource.__init__(self, uri)
        self.rdf_types.add(PROV.Activity)


class Entity(NewResource):
    """
    This class represents the PROV-O ontology's entity class.
    prov:wasGeneratedBy is a property used to describe a prov:entity.

    """

    was_generated_by: Annotated[
        Resource[Activity],
        Triple(PROV.wasGeneratedBy, PropertyStatus.optional, map_resource_to_uri),
    ]
    title: Annotated[
        str, Triple(DCTERMS.title, PropertyStatus.recommended, map_str_to_en_literal)
    ]
    has_primary_source: Annotated[
        Resource,
        Triple(PROV.hasPrimarySource, PropertyStatus.recommended, map_resource_to_uri),
    ]

    def __init__(self, uri: str):
        NewResource.__init__(self, uri)
        self.rdf_types.add(PROV.Entity)
