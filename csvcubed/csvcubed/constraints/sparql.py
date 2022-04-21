from enum import Enum


class SPARQLQUERY(Enum):
    """
    A place to hold SPARQL queries is use by the ic suites.
    """

    COMPONENT_IS_NOT_A_QB_DIMENSION = """SELECT * {{
            ?component <http://purl.org/linked-data/cube#componentProperty> ?componentproperty .
            FILTER CONTAINS(str(?component), "{implicit_component_postfix}") .
            FILTER NOT EXISTS {{ ?dimensionProperty <http://purl.org/linked-data/cube#dimension> ?componentproperty }}
            }}
        """
