Feature: Test outputting CSV-Ws with Qb flavouring.

  Scenario: A QbCube should generate appropriate DCAT Metadata
    Given a single-measure QbCube with identifier "qb-id-10002" named "Some Qube"
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10002.csv" should exist
    And the file at "qb-id-10002.csv-metadata.json" should exist
    And csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qb-id-10002.csv#dataset> a <http://www.w3.org/ns/dcat#Dataset>;
      <http://purl.org/dc/terms/description> "Description"^^<https://www.w3.org/ns/iana/media-types/text/markdown#Resource>;
      <http://purl.org/dc/terms/license> <http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>;
      <http://purl.org/dc/terms/creator> <https://www.gov.uk/government/organisations/office-for-national-statistics>;
      <http://purl.org/dc/terms/publisher> <https://www.gov.uk/government/organisations/office-for-national-statistics>;
      <http://purl.org/dc/terms/title> "Some Qube"@en;
      <http://www.w3.org/2000/01/rdf-schema#comment> "Summary"@en;
      <http://www.w3.org/2000/01/rdf-schema#label> "Some Qube"@en;
      <http://www.w3.org/ns/dcat#keyword> "Key word one"@en, "Key word two"@en;
      <http://www.w3.org/ns/dcat#landingPage> <http://example.org/landing-page>;
      <http://www.w3.org/ns/dcat#theme> <http://gss-data.org.uk/def/gdp#some-test-theme>;
      <http://www.w3.org/ns/dcat#contactPoint> <mailto:something@example.org>;
      <http://purl.org/dc/terms/identifier> "qb-id-10002".
      """

  Scenario: A QbCube should validate successfully where foreign key constraints are met.
    Given a single-measure QbCube named "Some Qube"
    When the cube is serialised to CSV-W
    Then the file at "a-code-list.csv-metadata.json" should exist
    And csvwcheck validation of "some-qube.csv-metadata.json" should succeed
    And csv2rdf on "some-qube.csv-metadata.json" should succeed
    And the RDF should not contain any instances of "http://www.w3.org/2004/02/skos/core#ConceptScheme"

  Scenario: A QbCube should fail to validate where foreign key constraints are not met.
    Given a single-measure QbCube named "Some Qube" with codes not defined in the code-list
    When the cube is serialised to CSV-W (suppressing missing uri value exceptions)
    Then the file at "a-code-list.csv-metadata.json" should exist
    And csvlint validation of "some-qube.csv-metadata.json" should fail with "unmatched_foreign_key_reference"

  Scenario: A QbCube with existing dimensions should not do foreign key checks.
    Given a single-measure QbCube named "Some Qube" with existing dimensions
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "some-qube.csv-metadata.json" should succeed

  Scenario: A single-measure QbCube with duplicate rows should fail validation
    Given a single-measure QbCube named "Duplicate Qube" with duplicate rows
    When the cube is serialised to CSV-W
    Then csvlint validation of "duplicate-qube.csv-metadata.json" should fail with "duplicate_key"

  Scenario: A multi-measure QbCube should pass validation
    Given a multi-measure QbCube named "Duplicate Qube"
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "duplicate-qube.csv-metadata.json" should succeed

  Scenario: A multi-measure QbCube with duplicate rows should fail validation
    Given a multi-measure QbCube named "Duplicate Qube" with duplicate rows
    When the cube is serialised to CSV-W
    Then csvlint validation of "duplicate-qube.csv-metadata.json" should fail with "duplicate_key"

  Scenario: QbCube new attribute values and units should be serialised given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure QbCube named "Some Qube" with new attribute values and units
    When the cube is serialised to CSV-W
    Then the file at "some-qube.csv" should exist
    And the file at "some-qube.csv-metadata.json" should exist
    And csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qudt: <http://qudt.org/schema/qudt/>.
      @prefix om2: <http://www.ontology-of-units-of-measure.org/resource/om-2/>.

      <{{rdf_input_directory}}/some-qube.csv#attribute/new-attribute/pending>
      a rdfs:Resource;
      rdfs:label "pending"@en.

      <{{rdf_input_directory}}/some-qube.csv#attribute/new-attribute/final>
      a rdfs:Resource;
      rdfs:label "final"@en.

      <{{rdf_input_directory}}/some-qube.csv#attribute/new-attribute/in-review>
      a rdfs:Resource;
      rdfs:label "in-review"@en.

      <{{rdf_input_directory}}/some-qube.csv#unit/some-unit>
      a qudt:Unit, om2:Unit;
      rdfs:label "Some Unit"@en.
      """

  Scenario: QbCube new attribute values and units should be serialised given ATTRIBUTE_VALUE_CODELISTS is True
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to True
    And a single-measure QbCube named "Some Qube" with new attribute values and units
    When the cube is serialised to CSV-W
    Then the file at "some-qube.csv" should exist
    And the file at "some-qube.csv-metadata.json" should exist
    And the file at "new-attribute.csv" should exist
    And the file at "new-attribute.csv-metadata.json" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qudt: <http://qudt.org/schema/qudt/>.
      @prefix om2: <http://www.ontology-of-units-of-measure.org/resource/om-2/>.
      @prefix skos: <http://www.w3.org/2004/02/skos/core#>.
      @prefix ui: <http://www.w3.org/ns/ui#>.

      <{{rdf_input_directory}}/new-attribute.csv#final>
      a skos:Concept;
      rdfs:label "final";
      skos:inScheme <{{rdf_input_directory}}/new-attribute.csv#code-list>;
      skos:notation "final";
      ui:sortPriority 0.

      <{{rdf_input_directory}}/new-attribute.csv#in-review>
      a skos:Concept;
      rdfs:label "in-review";
      skos:inScheme <{{rdf_input_directory}}/new-attribute.csv#code-list>;
      skos:notation "in-review";
      ui:sortPriority 1.

      <{{rdf_input_directory}}/new-attribute.csv#pending>
      a skos:Concept;
      rdfs:label "pending";
      skos:inScheme <{{rdf_input_directory}}/new-attribute.csv#code-list>;
      skos:notation "pending";
      ui:sortPriority 2.

      <{{rdf_input_directory}}/some-qube.csv#unit/some-unit>
      a qudt:Unit, om2:Unit;
      rdfs:label "Some Unit"@en.
      """

  Scenario: QbCube extended units (and new base units) should be serialised correctly.
    Given a single-measure QbCube named "Some Qube" with one new unit extending another new unit
    When the cube is serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qudt: <http://qudt.org/schema/qudt/>.
      @prefix om2: <http://www.ontology-of-units-of-measure.org/resource/om-2/>.
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

      <{{rdf_input_directory}}/some-qube.csv#unit/some-base-unit>
      a qudt:Unit, om2:Unit;
      rdfs:label "Some Base Unit"@en.

      <{{rdf_input_directory}}/some-qube.csv#unit/some-extending-unit>
      a qudt:Unit, om2:Unit;
      qudt:isScalingOf <{{rdf_input_directory}}/some-qube.csv#unit/some-base-unit>;
      qudt:hasQuantityKind <http://some-quantity-kind>;
      qudt:conversionMultiplier "25.123123"^^xsd:float;
      om2:hasUnit <{{rdf_input_directory}}/some-qube.csv#unit/some-base-unit>;
      om2:hasFactor "1000.0"^^xsd:float;
      rdfs:label "Some Extending Unit"@en.
      """

  Scenario: A QbCube with string literal new attributes should validate successfully
    Given a single-measure QbCube named "Qube with string literals" with "new" "string" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "qube-with-string-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-string-literals.csv#obs/uss-cerritos@some-measure> <{{rdf_input_directory}}/qube-with-string-literals.csv#attribute/first-captain>
      "William Riker".
      """
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-string-literals.csv#obs/uss-titan@some-measure> <{{rdf_input_directory}}/qube-with-string-literals.csv#attribute/first-captain>
      "Carol Freeman".
      """

  Scenario: A QbCube with numeric literal new attributes should validate successfully
    Given a single-measure QbCube named "Qube with int literals" with "new" "int" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "qube-with-int-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-int-literals.csv#obs/uss-cerritos@some-measure> <{{rdf_input_directory}}/qube-with-int-literals.csv#attribute/reg>
      "75567"^^<http://www.w3.org/2001/XMLSchema#int>.
      """
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-int-literals.csv#obs/uss-titan@some-measure> <{{rdf_input_directory}}/qube-with-int-literals.csv#attribute/reg>
      "80102"^^<http://www.w3.org/2001/XMLSchema#int>.
      """

  Scenario: A QbCube with date literal new attributes should validate successfully
    Given a single-measure QbCube named "Qube with date literals" with "new" "date" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "qube-with-date-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-date-literals.csv#obs/uss-cerritos@some-measure> <{{rdf_input_directory}}/qube-with-date-literals.csv#attribute/appeared>
      "2020-08-06"^^<http://www.w3.org/2001/XMLSchema#date>.
      """
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-date-literals.csv#obs/uss-titan@some-measure> <{{rdf_input_directory}}/qube-with-date-literals.csv#attribute/appeared>
      "2020-10-08"^^<http://www.w3.org/2001/XMLSchema#date>.
      """

  Scenario: A QbCube with string literal existing attributes should validate successfully
    Given a single-measure QbCube named "Qube with string literals" with "existing" "string" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "qube-with-string-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-string-literals.csv#obs/uss-cerritos@some-measure> <http://some-uri> "William Riker".
      """
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-string-literals.csv#obs/uss-titan@some-measure> <http://some-uri> "Carol Freeman".
      """

  Scenario: A QbCube with numeric literal existing attributes should validate successfully
    Given a single-measure QbCube named "Qube with int literals" with "existing" "int" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "qube-with-int-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-int-literals.csv#obs/uss-cerritos@some-measure> <http://some-uri> "75567"^^<http://www.w3.org/2001/XMLSchema#int>.
      """
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-int-literals.csv#obs/uss-titan@some-measure> <http://some-uri> "80102"^^<http://www.w3.org/2001/XMLSchema#int>.
      """

  Scenario: A QbCube with date literal existing attributes should validate successfully
    Given a single-measure QbCube named "Qube with date literals" with "existing" "date" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "qube-with-date-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-date-literals.csv#obs/uss-cerritos@some-measure> <http://some-uri> "2020-08-06"^^<http://www.w3.org/2001/XMLSchema#date>.
      """
    And the RDF should contain
      """
      <{{rdf_input_directory}}/qube-with-date-literals.csv#obs/uss-titan@some-measure> <http://some-uri> "2020-10-08"^^<http://www.w3.org/2001/XMLSchema#date>.
      """

  Scenario: A QbCube, by default, should include file endings in URIs
    Given a single-measure QbCube named "Default URI style qube"
    When the cube is serialised to CSV-W
    Then the cube's metadata should contain URLs with file endings
    And csvwcheck validation of "default-uri-style-qube.csv-metadata.json" should succeed

  Scenario: A QbCube configured with Standard URI style should include file endings in URIs
    Given a single-measure QbCube named "Standard URI style qube" configured with "Standard" URI style
    When the cube is serialised to CSV-W
    Then the cube's metadata should contain URLs with file endings
    And csvwcheck validation of "standard-uri-style-qube.csv-metadata.json" should succeed

  Scenario: A QbCube configured with WithoutFileExtensions URI style should exclude file endings in URIs
    Given a single-measure QbCube named "WithoutFileExtensions URI style qube" configured with "WithoutFileExtensions" URI style
    When the cube is serialised to CSV-W
    Then the cube's metadata should contain URLs without file endings
    And csvwcheck validation of "withoutfileextensions-uri-style-qube.csv-metadata.json" should succeed

  Scenario: A single-measure QbCube should pass skos+qb SPARQL test constraints
    Given a single-measure QbCube named "Some Qube"
    When the cube is serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
  # PMD test constraints won't pass because the CSV-W we're outputting needs to pass
  # through Jenkins to pick up PMD-specific augmentation.

  Scenario: A multi-measure QbCube should pass skos+qb SPARQL test constraints
    Given a multi-measure QbCube named "Some Qube"
    When the cube is serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
  # PMD test constraints won't pass because the CSV-W we're outputting needs to pass
  # through Jenkins to pick up PMD-specific augmentation.

  Scenario: A locally defined single-measure dataset with code-lists can be serialised to a standard CSV-qb.
    Given a single-measure QbCube named "single-measure qube with new definitions" with all new units/measures/dimensions/attributes/codelists
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "single-measure-qube-with-new-definitions.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests

  Scenario: A locally defined multi-measure dataset with code-lists can be serialised to a standard CSV-qb.
    Given a multi-measure QbCube named "multi-measure qube with new definitions" with all new units/measures/dimensions/attributes/codelists
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "multi-measure-qube-with-new-definitions.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
    And the RDF should contain
      """
      <{{rdf_input_directory}}/multi-measure-qube-with-new-definitions.csv#structure> <http://purl.org/linked-data/cube#component> <{{rdf_input_directory}}/multi-measure-qube-with-new-definitions.csv#component/new-dimension>.
      <{{rdf_input_directory}}/multi-measure-qube-with-new-definitions.csv#dimension/new-dimension> <http://purl.org/linked-data/cube#codeList> <{{rdf_input_directory}}/a-new-codelist.csv#code-list>.

      <{{rdf_input_directory}}/multi-measure-qube-with-new-definitions.csv#obs/a@part-time> a <http://purl.org/linked-data/cube#Observation>;
      <{{rdf_input_directory}}/multi-measure-qube-with-new-definitions.csv#dimension/new-dimension> <{{rdf_input_directory}}/a-new-codelist.csv#a>.

      <{{rdf_input_directory}}/a-new-codelist.csv#code-list> a <http://www.w3.org/2004/02/skos/core#ConceptScheme>.
      <{{rdf_input_directory}}/a-new-codelist.csv#a> a <http://www.w3.org/2004/02/skos/core#Concept>.
      """

  Scenario: A single-measure dataset (with code-list) having existing resources can be serialised to a standard CSV-qb
    Given a single measure QbCube named "single-measure qube with existing resources" with existing units/measure/dimensions/attribute/codelists
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "single-measure-qube-with-existing-resources.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And some additional turtle is appended to the resulting RDF
      """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qb: <http://purl.org/linked-data/cube#>.
      @prefix skos: <http://www.w3.org/2004/02/skos/core#>.
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

      <http://existing/dimension>
      rdfs:label "Some Existing Dimension"@en;
      a qb:DimensionProperty;
      qb:codeList <http://existing/dimension/code-list>;
      rdfs:range <http://some/range/thingy>.

      <http://existing/dimension/code-list> a skos:ConceptScheme;
      skos:hasTopConcept <http://existing/dimension/code-list/all>.

      <http://existing/dimension/code-list/all> a skos:Concept;
      rdfs:label "All possible things"@en;
      skos:inScheme <http://existing/dimension/code-list>.

      <http://existing/dimension/code-list/a> a skos:Concept;
      rdfs:label "A"@en;
      skos:inScheme <http://existing/dimension/code-list>;
      skos:broader <http://existing/dimension/code-list/all>.

      <http://existing/dimension/code-list/b> a skos:Concept;
      rdfs:label "B"@en;
      skos:inScheme <http://existing/dimension/code-list>;
      skos:broader <http://existing/dimension/code-list/all>.

      <http://existing/dimension/code-list/c> a skos:Concept;
      rdfs:label "C"@en;
      skos:inScheme <http://existing/dimension/code-list>;
      skos:broader <http://existing/dimension/code-list/all>.

      <http://existing/attribute> a qb:AttributeProperty;
      rdfs:label "Some existing attribute property"@en.

      <http://existing/measure> a qb:MeasureProperty;
      rdfs:label "Some existing measure property"@en;
      rdfs:range xsd:decimal.

      <http://existing/unit> rdfs:label "Some Existing Unit"@en.
      """
    And the RDF should pass "skos, qb" SPARQL tests

  Scenario: A multi-measure dataset (with code-list) having existing resources can be serialised to a standard CSV-qb
    Given a multi measure QbCube named "multi-measure qube with existing resources" with existing units/measure/dimensions/attribute/codelists
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "multi-measure-qube-with-existing-resources.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And some additional turtle is appended to the resulting RDF
      """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qb: <http://purl.org/linked-data/cube#>.
      @prefix skos: <http://www.w3.org/2004/02/skos/core#>.
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

      <http://existing/dimension>
      rdfs:label "Some Existing Dimension"@en;
      a qb:DimensionProperty;
      qb:codeList <http://existing/dimension/code-list>;
      rdfs:range <http://some/range/thingy>.

      <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist> a skos:ConceptScheme;
      skos:hasTopConcept <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/all>.

      <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/all> a skos:Concept;
      rdfs:label "All possible things"@en;
      skos:inScheme <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist>.

      <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/d> a skos:Concept;
      rdfs:label "D"@en;
      skos:inScheme <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist>;
      skos:broader <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/all>.

      <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/e> a skos:Concept;
      rdfs:label "E"@en;
      skos:inScheme <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist>;
      skos:broader <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/all>.

      <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/f> a skos:Concept;
      rdfs:label "F"@en;
      skos:inScheme <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist>;
      skos:broader <http://gss-data.org.uk/def/concept-scheme/some-existing-codelist/all>.

      <http://existing/dimension/code-list> a skos:ConceptScheme;
      skos:hasTopConcept <http://existing/dimension/code-list/all>.

      <http://existing/dimension/code-list/all> a skos:Concept;
      rdfs:label "All possible things"@en;
      skos:inScheme <http://existing/dimension/code-list>.

      <http://existing/dimension/code-list/a> a skos:Concept;
      rdfs:label "A"@en;
      skos:inScheme <http://existing/dimension/code-list>;
      skos:broader <http://existing/dimension/code-list/all>.

      <http://existing/dimension/code-list/b> a skos:Concept;
      rdfs:label "B"@en;
      skos:inScheme <http://existing/dimension/code-list>;
      skos:broader <http://existing/dimension/code-list/all>.

      <http://existing/dimension/code-list/c> a skos:Concept;
      rdfs:label "C"@en;
      skos:inScheme <http://existing/dimension/code-list>;
      skos:broader <http://existing/dimension/code-list/all>.

      <http://existing/attribute> a qb:AttributeProperty;
      rdfs:label "Some existing attribute property"@en.

      <http://existing/measure/part-time> a qb:MeasureProperty;
      rdfs:label "Part-time"@en;
      rdfs:range xsd:decimal.

      <http://existing/measure/full-time> a qb:MeasureProperty;
      rdfs:label "Full-time"@en;
      rdfs:range xsd:decimal.

      <http://existing/measure/flex-time> a qb:MeasureProperty;
      rdfs:label "Flex-time"@en;
      rdfs:range xsd:decimal.

      <http://existing/unit/gbp> rdfs:label "Pounds Sterling"@en.
      <http://existing/unit/count> rdfs:label "Count"@en.
      """
    And the RDF should pass "skos, qb" SPARQL tests

  Scenario: A cube with an optional attribute which has missing data values should validate successfully given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure QbCube named "Some Qube" with optional attribute values missing
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed

  Scenario: Observation Values are Optional where an 'sdmxa:ObsStatus' Attribute is Present given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure QbCube named "Good Qube" with missing observation values and `sdmxa:obsStatus` replacements
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "good-qube.csv-metadata.json" should succeed

  Scenario: Observation Values are Required where an 'sdmxa:ObsStatus' Attribute Column is present but no value is set given ATTRIBUTE_VALUE_CODELISTS is False.
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure QbCube named "Bad Qube" with missing observation values and missing `sdmxa:obsStatus` replacements
    Then the CSVqb should fail validation with "Missing value(s) found for 'Val' in row(s) 0"
    When the cube is serialised to CSV-W
    # Unfortunately, CSV-W validation will *not* catch this error since the obs column cannot be marked as `required`
    # since an `sdmxa:obsStatus` Attribute column has been defined.
    Then csvlint validation of "bad-qube.csv-metadata.json" should succeed

  Scenario: Each Observation should have Type http://purl.org/linked-data/cube#Observation and be part of the distribution
    Given a single-measure QbCube named "Some Qube"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csv2rdf on "some-qube.csv-metadata.json" should succeed
    And the RDF should contain
      """
      @prefix qb: <http://purl.org/linked-data/cube#>.

      <{{rdf_input_directory}}/some-qube.csv#obs/a,e@some-measure> a qb:Observation;
      qb:dataSet <{{rdf_input_directory}}/some-qube.csv#qbDataSet>.
      <{{rdf_input_directory}}/some-qube.csv#obs/b,f@some-measure> a qb:Observation;
      qb:dataSet <{{rdf_input_directory}}/some-qube.csv#qbDataSet>.
      <{{rdf_input_directory}}/some-qube.csv#obs/c,g@some-measure> a qb:Observation;
      qb:dataSet <{{rdf_input_directory}}/some-qube.csv#qbDataSet>.
      """

  Scenario: Observation Values are Required where no 'sdmxa:ObsStatus' Attribute Column is Present given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure QbCube named "Bad Qube" with missing observation values
    Then the CSVqb should fail validation with "Missing value(s) found for 'Val' in row(s) 1"
    When the cube is serialised to CSV-W
    # CSV-W validation will catch this error since the obs column is marked as `required` since no `sdmxa:obsStatus` column is defined.
    Then csvlint validation of "bad-qube.csv-metadata.json" should fail with "required. Row: 3,3"

  Scenario: Observation Values are Optional where an 'sdmxa:ObsStatus' Attribute is Present given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure QbCube named "Good Qube" with missing observation values and `sdmxa:obsStatus` replacements
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvwcheck validation of "good-qube.csv-metadata.json" should succeed

  Scenario: A QbCube with a dimension containing URI-unsafe chars can be correctly serialised.
    Given a QbCube named "URI-Unsafe Cube" which has a dimension containing URI-unsafe chars
    When the cube is serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed

  Scenario: Local Code List Metadata Dependencies are Well Defined
    Given a single-measure QbCube named "A Qube With Dependencies"
    When the cube is serialised to CSV-W
    Then the file at "a-code-list.csv-metadata.json" should exist
    And the file at "d-code-list.csv-metadata.json" should exist
    And csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      @prefix void: <http://rdfs.org/ns/void#>.

      <{{rdf_input_directory}}/a-qube-with-dependencies.csv#dependency/a-code-list> a void:Dataset;
      void:dataDump <{{rdf_input_directory}}/a-code-list.csv-metadata.json>;
      void:uriSpace "a-code-list.csv#".

      <{{rdf_input_directory}}/a-qube-with-dependencies.csv#dependency/d-code-list> a void:Dataset;
      void:dataDump <{{rdf_input_directory}}/d-code-list.csv-metadata.json>;
      void:uriSpace "d-code-list.csv#".
      """

  Scenario: A QbCube with complex datatypes should validate successfully and contain the expected types
    Given The config json file "v1.0/cube_datatypes.json" and the existing tidy data csv file "v1.0/cube_datatypes.csv"
    When a valid cube is built and serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    # The following checks for the expected datatypes as defined in models.cube.qb.components.constants
    # and declared via v1.0/cube_datatypes.json.
    # There is one one check per datatype and they follow the order of declaration.
    And the RDF should contain
      """
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/anyuri-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "anyURI attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#anyURI> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/boolean-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "boolean attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#boolean> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/decimal-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "decimal attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#decimal> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/int-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "int attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#int> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/long-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "long attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#long> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/integer-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "integer attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#integer> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/short-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "short attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#short> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/nonnegativeinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "nonNegativeInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#nonNegativeInteger> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/positiveinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "positiveInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#positiveInteger> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/unsignedlong-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "unsignedLong attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#unsignedLong> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/unsignedint-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "unsignedInt attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#unsignedInt> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/unsignedshort-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "unsignedShort attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#unsignedShort> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/nonpositiveinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "nonPositiveInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#nonPositiveInteger> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/negativeinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "negativeInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#negativeInteger> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/double-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "double attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#double> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/float-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "float attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#float> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/string-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "string attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#string> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/language-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "language attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#language> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/date-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "date attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#date> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/datetime-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "dateTime attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#dateTime> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/datetimestamp-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "dateTimeStamp attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#dateTimeStamp> .

      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/time-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "time attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#time> .
      """
    # The datatype of the measure, we've set this to a non default datatype
    And the RDF should contain
      """
      <{{rdf_input_directory}}/cube-datatypes.csv#measure/count> <http://www.w3.org/2000/01/rdf-schema#label> "count"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#integer> .
      """
    # The attribute values output should be formatted as expected
    And the RDF should contain
      """
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <{{rdf_input_directory}}/cube-datatypes.csv#obs/foo,bar,baz@count> <{{rdf_input_directory}}/cube-datatypes.csv#attribute/anyuri-attribute> "http://www.foo.com"^^xsd:anyURI ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/boolean-attribute> true ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/date-attribute> "2019-09-07"^^xsd:date ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/datetime-attribute> "2019-09-07T15:50:00"^^xsd:dateTime ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/datetimestamp-attribute> "2004-04-12T13:20:00Z"^^xsd:dateTimeStamp ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/decimal-attribute> 0.11 ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/double-attribute> 3.142e-02 ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/float-attribute> "0.03142"^^xsd:float ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/int-attribute> "-1"^^xsd:int ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/integer-attribute> -1 ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/language-attribute> "english"^^xsd:language ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/long-attribute> "-2147483647"^^xsd:long ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/negativeinteger-attribute> "-1"^^xsd:negativeInteger ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/nonnegativeinteger-attribute> "1"^^xsd:nonNegativeInteger ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/nonpositiveinteger-attribute> "-1"^^xsd:nonPositiveInteger ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/positiveinteger-attribute> "1"^^xsd:positiveInteger ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/short-attribute> "-32768"^^xsd:short ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/string-attribute> "foo" ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/time-attribute> "14:30:43"^^xsd:time ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/unsignedint-attribute> "1"^^xsd:unsignedInt ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/unsignedlong-attribute> "2147483646"^^xsd:unsignedLong ;
      <{{rdf_input_directory}}/cube-datatypes.csv#attribute/unsignedshort-attribute> "32768"^^xsd:unsignedShort .
      """

  Scenario: A QbCube configured by convention should contain appropriate datatypes
    Given the existing tidy data csv file "v1.0/cube_data_convention_ok.csv"
    When a valid cube is built and serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <{{rdf_input_directory}}/cube-data-convention-ok.csv#measure/cost-of-living-index> <http://www.w3.org/2000/01/rdf-schema#label> "Cost of living index"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#decimal> .
      """

  Scenario: A QbCube should generate csvcubed version specific rdf
    Given a single-measure QbCube with identifier "qb-id-10002" named "Some Qube"
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10002.csv" should exist
    And the file at "qb-id-10002.csv-metadata.json" should exist
    And csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    Given the version identifier
    Then the RDF should contain
      """
      @prefix prov: <http://www.w3.org/ns/prov#>.

      <{{rdf_input_directory}}/a-code-list.csv#code-list> a prov:Entity;
      prov:wasGeneratedBy <{{rdf_input_directory}}/a-code-list.csv#csvcubed-build-activity>.

      <{{rdf_input_directory}}/qb-id-10002.csv#csvcubed-build-activity> a prov:Activity;
      prov:used <{{csvcubed_version_identifier}}>.
      """

  Scenario: A multi-measure pivoted shape cube should be produced as the output for the multi-measure pivoted shape inputs given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a multi-measure pivoted shape cube with identifier "qb-id-10003" named "Pivoted Shape Cube"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10003.csv" should exist
    And the file at "qb-id-10003.csv-metadata.json" should exist
    And csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests
    And the RDF should contain
      """
      @prefix cube: <http://purl.org/linked-data/cube#> .
      @prefix measure: <{{rdf_input_directory}}/qb-id-10003.csv#measure/> .
      @prefix dimension: <{{rdf_input_directory}}/qb-id-10003.csv#dimension/> .
      @prefix attribute: <{{rdf_input_directory}}/qb-id-10003.csv#attribute/> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/a@some-other-measure> a cube:Observation ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#a> ;
      measure:some-other-measure 2.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-other-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/b@some-other-measure> a cube:Observation ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#b> ;
      measure:some-other-measure 4.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-other-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/c@some-other-measure> a cube:Observation ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#c> ;
      measure:some-other-measure 6.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-other-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#slice/a> cube:observation <{{rdf_input_directory}}/qb-id-10003.csv#obs/a@some-measure> .

      <{{rdf_input_directory}}/qb-id-10003.csv#slice/b> cube:observation <{{rdf_input_directory}}/qb-id-10003.csv#obs/b@some-measure> .

      <{{rdf_input_directory}}/qb-id-10003.csv#slice/c> cube:observation <{{rdf_input_directory}}/qb-id-10003.csv#obs/c@some-measure> .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/a@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/qb-id-10003.csv#attribute/some-attribute/attr-a> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#a> ;
      measure:some-measure 1.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/b@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/qb-id-10003.csv#attribute/some-attribute/attr-b> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#b> ;
      measure:some-measure 2.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/c@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/qb-id-10003.csv#attribute/some-attribute/attr-c> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#c> ;
      measure:some-measure 3.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      measure:some-measure a cube:ComponentProperty,
      cube:MeasureProperty,
      rdf:Property,
      rdfs:Resource ;
      rdfs:label "Some Measure"@en ;
      rdfs:range xsd:decimal .

      measure:some-other-measure a cube:ComponentProperty,
      cube:MeasureProperty,
      rdf:Property,
      rdfs:Resource ;
      rdfs:label "Some Other Measure"@en ;
      rdfs:range xsd:decimal .
      """

  Scenario: A multi-measure pivoted shape cube should be produced as the output for the multi-measure pivoted shape inputs given ATTRIBUTE_VALUE_CODELISTS is True
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to True
    And a multi-measure pivoted shape cube with identifier "qb-id-10003" named "Pivoted Shape Cube"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10003.csv" should exist
    And the file at "qb-id-10003.csv-metadata.json" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests
    And the RDF should contain
      """
      @prefix cube: <http://purl.org/linked-data/cube#> .
      @prefix measure: <{{rdf_input_directory}}/qb-id-10003.csv#measure/> .
      @prefix dimension: <{{rdf_input_directory}}/qb-id-10003.csv#dimension/> .
      @prefix attribute: <{{rdf_input_directory}}/qb-id-10003.csv#attribute/> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/a@some-other-measure> a cube:Observation ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#a> ;
      measure:some-other-measure 2.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-other-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/b@some-other-measure> a cube:Observation ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#b> ;
      measure:some-other-measure 4.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-other-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/c@some-other-measure> a cube:Observation ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#c> ;
      measure:some-other-measure 6.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-other-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#slice/a> cube:observation <{{rdf_input_directory}}/qb-id-10003.csv#obs/a@some-measure> .

      <{{rdf_input_directory}}/qb-id-10003.csv#slice/b> cube:observation <{{rdf_input_directory}}/qb-id-10003.csv#obs/b@some-measure> .

      <{{rdf_input_directory}}/qb-id-10003.csv#slice/c> cube:observation <{{rdf_input_directory}}/qb-id-10003.csv#obs/c@some-measure> .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/a@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/some-attribute.csv#attr-a> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#a> ;
      measure:some-measure 1.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/b@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/some-attribute.csv#attr-b> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#b> ;
      measure:some-measure 2.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10003.csv#obs/c@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/some-attribute.csv#attr-c> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#c> ;
      measure:some-measure 3.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10003.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      measure:some-measure a cube:ComponentProperty,
      cube:MeasureProperty,
      rdf:Property,
      rdfs:Resource ;
      rdfs:label "Some Measure"@en ;
      rdfs:range xsd:decimal .

      measure:some-other-measure a cube:ComponentProperty,
      cube:MeasureProperty,
      rdf:Property,
      rdfs:Resource ;
      rdfs:label "Some Other Measure"@en ;
      rdfs:range xsd:decimal .
      """

  Scenario: A single-measure pivoted shape cube should be produced as the output for the single-measure pivoted shape inputs given ATTRIBUTE_VALUE_CODELISTS is False
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    And a single-measure pivoted shape cube with identifier "qb-id-10004" named "Pivoted Shape Cube"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10004.csv" should exist
    And the file at "qb-id-10004.csv-metadata.json" should exist
    And csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests
    And the RDF should contain
      """
      @prefix cube: <http://purl.org/linked-data/cube#> .
      @prefix measure: <{{rdf_input_directory}}/qb-id-10004.csv#measure/> .
      @prefix dimension: <{{rdf_input_directory}}/qb-id-10004.csv#dimension/> .
      @prefix attribute: <{{rdf_input_directory}}/qb-id-10004.csv#attribute/> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <{{rdf_input_directory}}/qb-id-10004.csv#slice/a> cube:observation <{{rdf_input_directory}}/qb-id-10004.csv#obs/a@some-measure> .

      <{{rdf_input_directory}}/qb-id-10004.csv#slice/b> cube:observation <{{rdf_input_directory}}/qb-id-10004.csv#obs/b@some-measure> .

      <{{rdf_input_directory}}/qb-id-10004.csv#slice/c> cube:observation <{{rdf_input_directory}}/qb-id-10004.csv#obs/c@some-measure> .

      <{{rdf_input_directory}}/qb-id-10004.csv#obs/a@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/qb-id-10004.csv#attribute/some-attribute/attr-a> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#a> ;
      measure:some-measure 1.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10004.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10004.csv#obs/b@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/qb-id-10004.csv#attribute/some-attribute/attr-b> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#b> ;
      measure:some-measure 2.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10004.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10004.csv#obs/c@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/qb-id-10004.csv#attribute/some-attribute/attr-c> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#c> ;
      measure:some-measure 3.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10004.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      measure:some-measure a cube:ComponentProperty,
      cube:MeasureProperty,
      rdf:Property,
      rdfs:Resource ;
      rdfs:label "Some Measure"@en ;
      rdfs:range xsd:decimal .
      """

  Scenario: A single-measure pivoted shape cube should be produced as the output for the single-measure pivoted shape inputs given ATTRIBUTE_VALUE_CODELISTS is True
    Given the ATTRIBUTE_VALUE_CODELISTS feature flag is set to True
    And a single-measure pivoted shape cube with identifier "qb-id-10004" named "Pivoted Shape Cube"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10004.csv" should exist
    And the file at "qb-id-10004.csv-metadata.json" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests
    And the RDF should contain
      """
      @prefix cube: <http://purl.org/linked-data/cube#> .
      @prefix measure: <{{rdf_input_directory}}/qb-id-10004.csv#measure/> .
      @prefix dimension: <{{rdf_input_directory}}/qb-id-10004.csv#dimension/> .
      @prefix attribute: <{{rdf_input_directory}}/qb-id-10004.csv#attribute/> .
      @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

      <{{rdf_input_directory}}/qb-id-10004.csv#slice/a> cube:observation <{{rdf_input_directory}}/qb-id-10004.csv#obs/a@some-measure> .

      <{{rdf_input_directory}}/qb-id-10004.csv#slice/b> cube:observation <{{rdf_input_directory}}/qb-id-10004.csv#obs/b@some-measure> .

      <{{rdf_input_directory}}/qb-id-10004.csv#slice/c> cube:observation <{{rdf_input_directory}}/qb-id-10004.csv#obs/c@some-measure> .

      <{{rdf_input_directory}}/qb-id-10004.csv#obs/a@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/some-attribute.csv#attr-a> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#a> ;
      measure:some-measure 1.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10004.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10004.csv#obs/b@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/some-attribute.csv#attr-b> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#b> ;
      measure:some-measure 2.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10004.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      <{{rdf_input_directory}}/qb-id-10004.csv#obs/c@some-measure> a cube:Observation ;
      attribute:some-attribute <{{rdf_input_directory}}/some-attribute.csv#attr-c> ;
      dimension:some-dimension <{{rdf_input_directory}}/some-dimension.csv#c> ;
      measure:some-measure 3.0 ;
      cube:dataSet <{{rdf_input_directory}}/qb-id-10004.csv#qbDataSet> ;
      cube:measureType measure:some-measure .

      measure:some-measure a cube:ComponentProperty,
      cube:MeasureProperty,
      rdf:Property,
      rdfs:Resource ;
      rdfs:label "Some Measure"@en ;
      rdfs:range xsd:decimal .
      """
