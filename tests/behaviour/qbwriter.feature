Feature: Test outputting CSV-Ws with Qb flavouring.

  Scenario: A QbCube should generate appropriate DCAT Metadata
    Given a single-measure QbCube with identifier "qb-id-10002" named "Some Qube"
    When the cube is serialised to CSV-W
    Then the file at "qb-id-10002.csv" should exist
    And the file at "qb-id-10002.csv-metadata.json" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qb-id-10002.csv#dataset> a <http://www.w3.org/ns/dcat#Dataset>;
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
    And csvlint validation of "some-qube.csv-metadata.json" should succeed
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
    Then csvlint validation of "some-qube.csv-metadata.json" should succeed

  Scenario: A single-measure QbCube with duplicate rows should fail validation
    Given a single-measure QbCube named "Duplicate Qube" with duplicate rows
    When the cube is serialised to CSV-W
    Then csvlint validation of "duplicate-qube.csv-metadata.json" should fail with "duplicate_key"

  Scenario: A multi-measure QbCube should pass validation
    Given a multi-measure QbCube named "Duplicate Qube"
    When the cube is serialised to CSV-W
    Then csvlint validation of "duplicate-qube.csv-metadata.json" should succeed

  Scenario: A multi-measure QbCube with duplicate rows should fail validation
    Given a multi-measure QbCube named "Duplicate Qube" with duplicate rows
    When the cube is serialised to CSV-W
    Then csvlint validation of "duplicate-qube.csv-metadata.json" should fail with "duplicate_key"

  Scenario: QbCube new attribute values and units should be serialised
    Given a single-measure QbCube named "Some Qube" with new attribute values and units
    When the cube is serialised to CSV-W
    Then the file at "some-qube.csv" should exist
    And the file at "some-qube.csv-metadata.json" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
    """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qudt: <http://qudt.org/schema/qudt/>.
      @prefix om2: <http://www.ontology-of-units-of-measure.org/resource/om-2/>.

      <file:/tmp/some-qube.csv#attribute/new-attribute/pending>
        a rdfs:Resource;
        rdfs:label "pending"@en.

      <file:/tmp/some-qube.csv#attribute/new-attribute/final>
        a rdfs:Resource;
        rdfs:label "final"@en.

      <file:/tmp/some-qube.csv#attribute/new-attribute/in-review>
        a rdfs:Resource;
        rdfs:label "in-review"@en.

      <file:/tmp/some-qube.csv#unit/some-unit>
        a qudt:Unit, om2:Unit;
        rdfs:label "Some Unit"@en.
    """

  Scenario: QbCube extended units (and new base units) should be serialised correctly.
    Given a single-measure QbCube named "Some Qube" with one new unit extending another new unit
    When the cube is serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
    """
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      @prefix qudt: <http://qudt.org/schema/qudt/>.
      @prefix om2: <http://www.ontology-of-units-of-measure.org/resource/om-2/>.
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

      <file:/tmp/some-qube.csv#unit/some-base-unit>
        a qudt:Unit, om2:Unit;
        rdfs:label "Some Base Unit"@en.

      <file:/tmp/some-qube.csv#unit/some-extending-unit>
        a qudt:Unit, om2:Unit;
        qudt:isScalingOf <file:/tmp/some-qube.csv#unit/some-base-unit>;
        qudt:hasQuantityKind <http://some-quantity-kind>;
        qudt:conversionMultiplier "25.123123"^^xsd:float;
        om2:hasUnit <file:/tmp/some-qube.csv#unit/some-base-unit>;
        om2:hasFactor "1000.0"^^xsd:float;
        rdfs:label "Some Extending Unit"@en.
    """

  Scenario: A QbCube with string literal new attributes should validate successfully
    Given a single-measure QbCube named "Qube with string literals" with "new" "string" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "qube-with-string-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qube-with-string-literals.csv#obs/uss-cerritos> <file:/tmp/qube-with-string-literals.csv#attribute/first-captain>
      "William Riker".
      """
    And the RDF should contain
      """
      <file:/tmp/qube-with-string-literals.csv#obs/uss-titan> <file:/tmp/qube-with-string-literals.csv#attribute/first-captain>
      "Carol Freeman".
      """

  Scenario: A QbCube with numeric literal new attributes should validate successfully
    Given a single-measure QbCube named "Qube with int literals" with "new" "int" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "qube-with-int-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qube-with-int-literals.csv#obs/uss-cerritos> <file:/tmp/qube-with-int-literals.csv#attribute/reg>
      "75567"^^<http://www.w3.org/2001/XMLSchema#int>.
      """
    And the RDF should contain
      """
      <file:/tmp/qube-with-int-literals.csv#obs/uss-titan> <file:/tmp/qube-with-int-literals.csv#attribute/reg>
      "80102"^^<http://www.w3.org/2001/XMLSchema#int>.
      """

  Scenario: A QbCube with date literal new attributes should validate successfully
    Given a single-measure QbCube named "Qube with date literals" with "new" "date" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "qube-with-date-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qube-with-date-literals.csv#obs/uss-cerritos> <file:/tmp/qube-with-date-literals.csv#attribute/appeared>
      "2020-08-06"^^<http://www.w3.org/2001/XMLSchema#date>.
      """
    And the RDF should contain
      """
      <file:/tmp/qube-with-date-literals.csv#obs/uss-titan> <file:/tmp/qube-with-date-literals.csv#attribute/appeared>
      "2020-10-08"^^<http://www.w3.org/2001/XMLSchema#date>.
      """

  Scenario: A QbCube with string literal existing attributes should validate successfully
    Given a single-measure QbCube named "Qube with string literals" with "existing" "string" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "qube-with-string-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qube-with-string-literals.csv#obs/uss-cerritos> <http://some-uri> "William Riker".
      """
    And the RDF should contain
      """
      <file:/tmp/qube-with-string-literals.csv#obs/uss-titan> <http://some-uri> "Carol Freeman".
      """

  Scenario: A QbCube with numeric literal existing attributes should validate successfully
    Given a single-measure QbCube named "Qube with int literals" with "existing" "int" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "qube-with-int-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qube-with-int-literals.csv#obs/uss-cerritos> <http://some-uri> "75567"^^<http://www.w3.org/2001/XMLSchema#int>.
      """
    And the RDF should contain
      """
      <file:/tmp/qube-with-int-literals.csv#obs/uss-titan> <http://some-uri> "80102"^^<http://www.w3.org/2001/XMLSchema#int>.
      """

  Scenario: A QbCube with date literal existing attributes should validate successfully
    Given a single-measure QbCube named "Qube with date literals" with "existing" "date" attribute
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "qube-with-date-literals.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
      """
      <file:/tmp/qube-with-date-literals.csv#obs/uss-cerritos> <http://some-uri> "2020-08-06"^^<http://www.w3.org/2001/XMLSchema#date>.
      """
    And the RDF should contain
      """
      <file:/tmp/qube-with-date-literals.csv#obs/uss-titan> <http://some-uri> "2020-10-08"^^<http://www.w3.org/2001/XMLSchema#date>.
      """

  Scenario: A QbCube, by default, should include file endings in URIs
    Given a single-measure QbCube named "Default URI style qube"
    When the cube is serialised to CSV-W
    Then the cube's metadata should contain URLs with file endings
    And csvlint validation of "default-uri-style-qube.csv-metadata.json" should succeed

  Scenario: A QbCube configured with Standard URI style should include file endings in URIs
    Given a single-measure QbCube named "Standard URI style qube" configured with "Standard" URI style
    When the cube is serialised to CSV-W
    Then the cube's metadata should contain URLs with file endings
    And csvlint validation of "standard-uri-style-qube.csv-metadata.json" should succeed

  Scenario: A QbCube configured with WithoutFileExtensions URI style should exclude file endings in URIs
    Given a single-measure QbCube named "WithoutFileExtensions URI style qube" configured with "WithoutFileExtensions" URI style
    When the cube is serialised to CSV-W
    Then the cube's metadata should contain URLs without file endings
    And csvlint validation of "withoutfileextensions-uri-style-qube.csv-metadata.json" should succeed

  Scenario: A single-measure QbCube should pass skos+qb SPARQL test constraints
    Given a single-measure QbCube named "Some Qube"
    When the cube is serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
    # PMD test constraints won't pass because the CSV-W we're outputting needs to pass
    # through Jenkins to pick up PMD-specific augmentation.

  Scenario: A multi-measure QbCube should pass skos+qb SPARQL test constraints
    Given a multi-measure QbCube named "Some Qube"
    When the cube is serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
    # PMD test constraints won't pass because the CSV-W we're outputting needs to pass
    # through Jenkins to pick up PMD-specific augmentation.

  Scenario: A locally defined single-measure dataset (with code-lists) can be serialised to a standard CSV-qb
    Given a single-measure QbCube named "single-measure qube with new definitions" with all new units/measures/dimensions/attributes/codelists
    When the cube is serialised to CSV-W
    Then csvlint validation of "single-measure-qube-with-new-definitions.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests

  Scenario: A locally defined multi-measure dataset (with code-lists) can be serialised to a standard CSV-qb
    Given a multi-measure QbCube named "multi-measure qube with new definitions" with all new units/measures/dimensions/attributes/codelists
    When the cube is serialised to CSV-W
    Then csvlint validation of "multi-measure-qube-with-new-definitions.csv-metadata.json" should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
    And the RDF should contain
    """
      <file:/tmp/multi-measure-qube-with-new-definitions.csv#structure> <http://purl.org/linked-data/cube#component> <file:/tmp/multi-measure-qube-with-new-definitions.csv#component/new-dimension>.
      <file:/tmp/multi-measure-qube-with-new-definitions.csv#dimension/new-dimension> <http://purl.org/linked-data/cube#codeList> <file:/tmp/a-new-codelist.csv#code-list>.

      <file:/tmp/multi-measure-qube-with-new-definitions.csv#obs/a@part-time> a <http://purl.org/linked-data/cube#Observation>;
        <file:/tmp/multi-measure-qube-with-new-definitions.csv#dimension/new-dimension> <file:/tmp/a-new-codelist.csv#a>.

      <file:/tmp/a-new-codelist.csv#code-list> a <http://www.w3.org/2004/02/skos/core#ConceptScheme>.
      <file:/tmp/a-new-codelist.csv#a> a <http://www.w3.org/2004/02/skos/core#Concept>.
    """

  Scenario: A single-measure dataset (with code-list) having existing resources can be serialised to a standard CSV-qb
    Given a single measure QbCube named "single-measure qube with existing resources" with existing units/measure/dimensions/attribute/codelists
    When the cube is serialised to CSV-W
    Then csvlint validation of "single-measure-qube-with-existing-resources.csv-metadata.json" should succeed
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
    Then csvlint validation of "multi-measure-qube-with-existing-resources.csv-metadata.json" should succeed
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

  Scenario: A codelist defined in a CSV-W should be copied to the output directory
    Given the existing test-case file "qbwriter/code-list.csv-metadata.json"
    And the existing test-case file "qbwriter/code-list.table.json"
    And the existing test-case file "qbwriter/code-list.csv"
    And a QbCube named "Some Qube" with code-list defined in an existing CSV-W "qbwriter/code-list.csv-metadata.json"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then the file at "code-list.csv-metadata.json" should exist
    And the file at "code-list.table.json" should exist
    And the file at "code-list.csv" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "skos, qb" SPARQL tests
    And the RDF should contain
    """
      <file:/tmp/some-qube.csv#structure> <http://purl.org/linked-data/cube#component> <file:/tmp/some-qube.csv#component/d-code-list>.
      <file:/tmp/some-qube.csv#component/d-code-list> <http://purl.org/linked-data/cube#dimension> <file:/tmp/some-qube.csv#dimension/d-code-list>.
      <file:/tmp/some-qube.csv#dimension/d-code-list> <http://purl.org/linked-data/cube#codeList> <http://gss-data.org.uk/def/trade/concept-scheme/age-of-business>.

      <file:/tmp/some-qube.csv#obs/a,10-20> <file:/tmp/some-qube.csv#dimension/d-code-list> <http://gss-data.org.uk/def/trade/concept/age-of-business/10-20>.

      <http://gss-data.org.uk/def/trade/concept-scheme/age-of-business> a <http://www.w3.org/2004/02/skos/core#ConceptScheme>.
      <http://gss-data.org.uk/def/trade/concept/age-of-business/10-20> a <http://www.w3.org/2004/02/skos/core#Concept>;
        <http://www.w3.org/2004/02/skos/core#inScheme> <http://gss-data.org.uk/def/trade/concept-scheme/age-of-business>.
    """

  Scenario: A cube with an option attribute which has missing data values should validate successfully
    Given a single-measure QbCube named "Some Qube" with optional attribute values missing
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed

  Scenario: Each Observation should have Type http://purl.org/linked-data/cube#Observation and be part of the dataset
    Given a single-measure QbCube named "Some Qube"
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csv2rdf on "some-qube.csv-metadata.json" should succeed
    And the RDF should contain
    """
       @prefix qb: <http://purl.org/linked-data/cube#>.

       <file:/tmp/some-qube.csv#obs/a,e> a qb:Observation;
                                         qb:dataSet <file:/tmp/some-qube.csv#dataset>.
       <file:/tmp/some-qube.csv#obs/b,f> a qb:Observation;
                                         qb:dataSet <file:/tmp/some-qube.csv#dataset>.
       <file:/tmp/some-qube.csv#obs/c,g> a qb:Observation;
                                         qb:dataSet <file:/tmp/some-qube.csv#dataset>.
    """

  Scenario: Observation Values are Required where no `sdmxa:ObsStatus` Attribute Column is Present
    Given a single-measure QbCube named "Bad Qube" with missing observation values
    Then the CSVqb should fail validation with "Missing value(s) found for 'Value' in row(s) 1"
    When the cube is serialised to CSV-W
    # CSV-W validation will catch this error since the obs column is marked as `required` since no `sdmxa:obsStatus` column is defined.
    Then csvlint validation of "bad-qube.csv-metadata.json" should fail with "required. Row: 3,3"

  Scenario: Observation Values are Optional where an `sdmxa:ObsStatus` Attribute is Present
    Given a single-measure QbCube named "Good Qube" with missing observation values and `sdmxa:obsStatus` replacements
    Then the CSVqb should pass all validations
    When the cube is serialised to CSV-W
    Then csvlint validation of "good-qube.csv-metadata.json" should succeed

  Scenario: Observation Values are Required where an `sdmxa:ObsStatus` Attribute Column is present but no value is set.
    Given a single-measure QbCube named "Bad Qube" with missing observation values and missing `sdmxa:obsStatus` replacements
    Then the CSVqb should fail validation with "Missing value(s) found for 'Value' in row(s) 0"
    When the cube is serialised to CSV-W
    # Unfortunately, CSV-W validation will *not* catch this error since the obs column cannot be marked as `required`
    # since an `sdmxa:obsStatus` Attribute column has been defined.
    Then csvlint validation of "bad-qube.csv-metadata.json" should succeed

  # Related to issue #389
  Scenario: A QbCube which references a legacy composite code list should pass all tests
    Given a QbCube named "Some Qube" which references a legacy composite code-list
    When the cube is serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests

  Scenario: A QbCube with a dimension containing URI-unsafe chars can be correctly serialised.
    Given a QbCube named "URI-Unsafe Cube" which has a dimension containing URI-unsafe chars
    When the cube is serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed

  Scenario: Local Code List Metadata Dependencies are Well Defined
    Given a single-measure QbCube named "A Qube With Dependencies"
    When the cube is serialised to CSV-W
    Then the file at "a-code-list.csv-metadata.json" should exist
    And the file at "d-code-list.csv-metadata.json" should exist
    And csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
    """
      @prefix void: <http://rdfs.org/ns/void#>.

      <file:/tmp/a-qube-with-dependencies.csv#dependency/a-code-list> a void:Dataset;
        void:dataDump <file:/tmp/a-code-list.csv-metadata.json>;
        void:uriSpace "a-code-list.csv#".

      <file:/tmp/a-qube-with-dependencies.csv#dependency/d-code-list> a void:Dataset;
        void:dataDump <file:/tmp/d-code-list.csv-metadata.json>;
        void:uriSpace "d-code-list.csv#".
    """

  Scenario: A QbCube with complex datatypes should validate successfully and contain the expected types
    Given The config json file "v1.0/cube_datatypes.json" and the existing tidy data csv file "v1.0/cube_datatypes.csv"
    When the cube is created
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    # The following checks for the expected datatypes as defined in models.cube.qb.components.constants
    # and declared via v1.0/cube_datatypes.json.
    # There is one one check per datatype and they follow the order of declaration.
    And the RDF should contain
    """
    <file:/tmp/cube-datatypes.csv#attribute/anyuri-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "anyURI attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#anyURI> .

    <file:/tmp/cube-datatypes.csv#attribute/boolean-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "boolean attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#boolean> .

    <file:/tmp/cube-datatypes.csv#attribute/decimal-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "decimal attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#decimal> .

    <file:/tmp/cube-datatypes.csv#attribute/int-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "int attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#int> .

    <file:/tmp/cube-datatypes.csv#attribute/long-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "long attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#long> .

    <file:/tmp/cube-datatypes.csv#attribute/integer-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "integer attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#integer> .

    <file:/tmp/cube-datatypes.csv#attribute/short-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "short attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#short> .

    <file:/tmp/cube-datatypes.csv#attribute/nonnegativeinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "nonNegativeInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#nonNegativeInteger> .

    <file:/tmp/cube-datatypes.csv#attribute/positiveinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "positiveInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#positiveInteger> .

    <file:/tmp/cube-datatypes.csv#attribute/unsignedlong-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "unsignedLong attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#unsignedLong> .
 
    <file:/tmp/cube-datatypes.csv#attribute/unsignedint-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "unsignedInt attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#unsignedInt> .
 
    <file:/tmp/cube-datatypes.csv#attribute/unsignedshort-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "unsignedShort attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#unsignedShort> .

    <file:/tmp/cube-datatypes.csv#attribute/nonpositiveinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "nonPositiveInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#nonPositiveInteger> .

    <file:/tmp/cube-datatypes.csv#attribute/negativeinteger-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "negativeInteger attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#negativeInteger> .

    <file:/tmp/cube-datatypes.csv#attribute/double-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "double attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#double> .

    <file:/tmp/cube-datatypes.csv#attribute/float-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "float attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#float> .

    <file:/tmp/cube-datatypes.csv#attribute/string-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "string attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#string> .

    <file:/tmp/cube-datatypes.csv#attribute/language-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "language attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#language> .

    <file:/tmp/cube-datatypes.csv#attribute/date-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "date attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#date> .

    <file:/tmp/cube-datatypes.csv#attribute/datetime-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "dateTime attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#dateTime> .

    <file:/tmp/cube-datatypes.csv#attribute/datetimestamp-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "dateTimeStamp attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#dateTimeStamp> .

    <file:/tmp/cube-datatypes.csv#attribute/time-attribute> <http://www.w3.org/2000/01/rdf-schema#label> "time attribute"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#time> .
    """
    # The datatype of the measure, we've set this to a non default datatype
    And the RDF should contain
    """
    <file:/tmp/cube-datatypes.csv#measure/count> <http://www.w3.org/2000/01/rdf-schema#label> "count"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#integer> .
    """

  Scenario: A QbCube configured by convention should contain appropriate datatypes
    Given the existing tidy data csv file "v1.0/cube_data_convention_ok.csv"
    When the cube is created
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should contain
    """
    <file:/tmp/cube-data-convention-ok.csv#measure/cost-of-living-index> <http://www.w3.org/2000/01/rdf-schema#label> "Cost of living index"@en;
      <http://www.w3.org/2000/01/rdf-schema#range> <http://www.w3.org/2001/XMLSchema#decimal> .
    """