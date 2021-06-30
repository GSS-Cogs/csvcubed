from typing import Annotated, Set, Union

from rdflib import URIRef

from sharedmodels.rdf.rdfresource import RdfResource, map_entity_to_uri
from sharedmodels.rdf.triple import Triple, PropertyStatus

CollectionMemberType = Union["Concept", "Collection"]


class Collection(RdfResource):
    """Collection - """
    members: Annotated[Set[CollectionMemberType], Triple(URIRef("http://www.w3.org/2004/02/skos/core#member"),
                                                         PropertyStatus.recommended, map_entity_to_uri)]
    """has member - """

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(URIRef("http://www.w3.org/2004/02/skos/core#Collection"))
        self.members = set()


class OrderedCollection(Collection):
    """Ordered Collection - """
    memberList: Annotated[list, Triple(URIRef("http://www.w3.org/2004/02/skos/core#memberList"),
                                       PropertyStatus.recommended, map_entity_to_uri)]
    """has member list - For any resource, every item in the list given as the value of the
      skos:memberList property is also a value of the skos:member property."""

    def __init__(self, uri: str):
        Collection.__init__(self, uri)
        self.rdf_types.add(URIRef("http://www.w3.org/2004/02/skos/core#OrderedCollection"))
        self.memberList = []


class ConceptScheme(RdfResource):
    """Concept Scheme - """
    hasTopConcepts: Annotated[Set["Concept"], Triple(URIRef("http://www.w3.org/2004/02/skos/core#hasTopConcept"),
                                                     PropertyStatus.recommended, map_entity_to_uri)]
    """has top concept - """

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(URIRef("http://www.w3.org/2004/02/skos/core#ConceptScheme"))
        self.hasTopConcepts = set()


class Concept(RdfResource):
    """Concept - """
    topConceptOf: Annotated["ConceptScheme", Triple(URIRef("http://www.w3.org/2004/02/skos/core#topConceptOf"),
                                                    PropertyStatus.recommended, map_entity_to_uri)]
    """is top concept in scheme - """

    semanticRelation: Annotated["Concept", Triple(URIRef("http://www.w3.org/2004/02/skos/core#semanticRelation"),
                                                  PropertyStatus.recommended, map_entity_to_uri)]
    """is in semantic relation with - """

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(URIRef("http://www.w3.org/2004/02/skos/core#Concept"))
