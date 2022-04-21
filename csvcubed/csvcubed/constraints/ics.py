"""
A scalable pure python in-memory implementations of the qb integrity constraints.

NOTE:
At time of writing (31/3/2022) only a small number of these tests can be applied as our cube dataset structure is
still in an mvp place. However they should be written in such a way to allow quite rapid update and iteration
once a more complete qb RDF structure is in place.

IMPRTANT - When we do update to final product outputs, please remove any stopgap_ prefixes and update the
docstrings accordingly.

NOTE: spike code only. This probably needs to be organised like an actual test suite rather than just bombing out
on first fail as per this implementation.
"""

from columns import ColumnRef
from virtualiser import Virtualiser
from sparql import SPARQLQUERY

from rdflib.plugins.sparql.processor import SPARQLResult

class ConstraintSuiteIC:
    """
    A class for grouping the standard qb integrity constraints into a validation suite
    """

    def __init__(self, v: Virtualiser):
        self.v = v

    def validate(self):
        """The 'run all' option"""
        self.stopgap_ic_04_dimensions_have_range()
        self.ic_13_required_attributes()

    # example 1: a stopgap "something is better than nothing" ic implementation
    def stopgap_ic_04_dimensions_have_range(self):
        """
        Representing:
        -------------
        Every dimension declared in a qb:DataStructureDefinition must have a declared rdfs:range.
        ic_04_dimensions_have_range - https://raw.githubusercontent.com/GSS-Cogs/gdp-sparql-tests/master/tests/qb/qb-ics/ic-04-dimensions-have-range.sparql
        TODO: Awaiting preconditions: qb:DimensionProperty with rdfs:range

        Stopgap Implementation
        -----------------------
        Confirm that all components we can infer as being defined as dimensions have a qb:componentProperty
        which is a qb:dimenson
        """

        col: ColumnRef
        for col in self.v.column_reference.get_dimensions():
            query_str: str = SPARQLQUERY.COMPONENT_IS_NOT_A_QB_DIMENSION.value.format(
                implicit_component_postfix=col.implicit_component_postfix
            )
            result: SPARQLResult = self.v.query_metadata_graph(query_str)
            assert len(result.bindings) == 0, (f'Inferred dimension component "{col.implicit_component_postfix}"'
                'does not have a qb:dimension property')

    # example 1: closer to a final production ic implementation
    def ic_13_required_attributes(self):
        """
        Representing:
        -------------
        Every qb:Observation has a value for each declared attribute that is marked as required.
        https://raw.githubusercontent.com/GSS-Cogs/gdp-sparql-tests/master/tests/qb/qb-ics/ic-13-required_attributes.sparql

        Logic
        -----
        If every column that is declared as type attribute with a required=True declaration is fully populated with values
        then every observation (once transformed to RDF) will have this declared attribute once the csv+csvw is
        transformed to RDF.
        """

        col: ColumnRef
        for col in self.v.column_reference.get_attributes():
            if not col.required:
                continue

            for cell_value in self.v._column_value_yielder(col.title):
                assert cell_value != "", f'You have a blank cell in the required attribute column: {col.title}'
