Feature: cube-config.json
  As an external data publisher,
  I want to be able to create a cube from a tidy data csv, with or without a qube-config json file.

  Scenario: Output a cube and errors when created from both config and data
    Given the config json file "v1.0/cube_data_config_ok.json" and the existing tidy data csv file "v1.0/cube_data_config_ok.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Tests/test-cases/config/schema-cube-data-config-ok",
      "identifier": "schema-cube-data-config-ok",
      "summary": "a summary",
      "description": "Schema for testing",
      "creator_uri": "https://www.gov.uk/government/organisations/office-for-national-statistics",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": ["https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments"],
      "keywords": ["A keyword", "Another keyword"],
      "dataset_issued": "2022-03-04",
      "dataset_modified": "2022-03-04T15:00:00+00:00",
      "license_uri": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
      "public_contact_point_uri": "mailto:csvcubed@example.com",
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dim-0",
        "Dim-1",
        "Dim-2",
        "Attr-1",
        "Amount",
        "Measure",
        "Units"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dim-0": "1",
          "Dim-1": "2009",
          "Dim-2": "import",
          "Attr-1": "goods",
          "Amount": 100,
          "Measure": "billions",
          "Units": "pounds"
        },
        {
          "Dim-0": "2",
          "Dim-1": "2010",
          "Dim-2": "export",
          "Attr-1": "services",
          "Amount": 321,
          "Measure": "billions",
          "Units": "pounds"
        }
      ]
      """

  Scenario: Output a cube and errors when created data only
    Given the existing tidy data csv file "v1.0/cube_data_convention_ok.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Cube Data Convention Ok",
      "identifier": None,
      "summary": "",
      "description": "",
      "creator_uri": None,
      "publisher_uri": None,
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": [],
      "dataset_issued": None,
      "dataset_modified": None,
      "license_uri": None,
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None,
      }
      """
    Then the cube Columns should match
      """
      [
        "Period",
        "Geography",
        "Observation",
        "Measure",
        "Unit",
        "Attribute"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Period": "2010",
          "Geography": "london",
          "Observation": 0,
          "Measure": "cost-of-living-index",
          "Unit": "index",
          "Attribute": "blue"
        },
        {
          "Period": "2011",
          "Geography": "london",
          "Observation": 1,
          "Measure": "cost-of-living-index",
          "Unit": "index",
          "Attribute": "green"
        },
        {
          "Period": "2012",
          "Geography": "london",
          "Observation": 2,
          "Measure": "cost-of-living-index",
          "Unit": "index",
          "Attribute": "red"
        },
        {
          "Period": "2013",
          "Geography": "london",
          "Observation": 3,
          "Measure": "cost-of-living-index",
          "Unit": "index",
          "Attribute": "orange"
        }
      ]
      """

  Scenario: Output a cube combining config and convention
    Given the config json file "v1.0/cube_data_part_config.json" and the existing tidy data csv file "v1.0/cube_data_part_config.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {"title": "Tests/test-cases/config/schema-cube-data-config-ok",
      "identifier": "schema-id",
      "summary": "a summary",
      "description": "Schema for testing",
      "creator_uri": "https://www.gov.uk/government/organisations/office-for-national-statistics",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": ["https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments"],
      "keywords": ["two"],
      "dataset_issued": "2022-03-04T17:00:00",
      "dataset_modified": "2022-03-04T18:00:00",
      "license_uri": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """

  Scenario: Output a cube when the code list is defined using code list config schema v1.0 and when the concepts are hierarchical, and the sort order is defined with sort object
    Given the config json file "v1.1/cube_config_hierarchical.json" and the existing tidy data csv file "v1.1/data.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Test cube config",
      "identifier": None,
      "summary": "Test cube config summary",
      "description": "Test cube config description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dimension": "a",
          "Val": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Val": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Val": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Val": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Val": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when the code list is defined using code list config schema v1.0 and when the concepts are not hierarchical, and the sort order is defined with sort object
    Given the config json file "v1.1/cube_config_none_hierarchical.json" and the existing tidy data csv file "v1.1/data.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Test cube config",
      "identifier": None,
      "summary": "Test cube config summary",
      "description": "Test cube config description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dimension": "a",
          "Val": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Val": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Val": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Val": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Val": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when an inline code list is defined using code list config schema v1.0, and the sort order is defined with sort object
    Given the config json file "v1.1/cube_config_inline_code_list.json" and the existing tidy data csv file "v1.1/data.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Test cube config",
      "identifier": None,
      "summary": "Test cube config summary",
      "description": "Test cube config description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dimension": "a",
          "Val": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Val": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Val": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Val": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Val": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when the sort object is not defined but the sort order is defined
    Given the config json file "v1.1/cube_config_hierarchical_without_sort.json" and the existing tidy data csv file "v1.1/data.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Test cube config",
      "identifier": None,
      "summary": "Test cube config summary",
      "description": "Test cube config description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dimension": "a",
          "Val": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Val": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Val": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Val": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Val": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when the code list is defined using code list config schema v1.0 and when there are references to concepts defined elsewhere.
    Given the config json file "v1.1/cube_config_with_concepts_defined_elsewhere.json" and the existing tidy data csv file "v1.1/data.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Test cube config",
      "identifier": None,
      "summary": "Test cube config summary",
      "description": "Test cube config description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dimension": "a",
          "Val": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Val": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Val": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Val": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Val": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when an inline code list is defined using code list config schema v1.0 and when there are references to concepts defined elsewhere.
    Given the config json file "v1.1/cube_config_inline_code_list_with_concepts_defined_elsewhere.json" and the existing tidy data csv file "v1.1/data.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Test cube config",
      "identifier": None,
      "summary": "Test cube config summary",
      "description": "Test cube config description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
        {
          "Dimension": "a",
          "Val": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Val": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Val": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Val": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Val": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Successfully outputs a cube using schema v1.2
    Given the config json file "v1.2/qudt-unit-template-testing.json" and the existing tidy data csv file "v1.2/data.csv"
    Then a valid cube can be built and serialised to CSV-W

  Scenario: Output a cube when the code list is defined using code list config schema v1.1 with concepts in which the uri_safe_identifier_override is defined.
    Given the config json file "v1.3/cube_config_with_concept_uri_safe_identifier_override.json" and the existing tidy data csv file "v1.3/data_uri_safe_identifier_override.csv"
    When a valid cube is built and serialised to CSV-W
    Then the cube Metadata should match
      """
      {
      "title": "Uri safe identifier override",
      "identifier": None,
      "summary": "Uri safe identifier override summary",
      "description": "Uri safe identifier override description",
      "creator_uri": "http://statistics.data.gov.uk",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": [],
      "keywords": ["Test cube"],
      "dataset_issued": "2022-04-08",
      "dataset_modified": None,
      "license_uri": "https://creativecommons.org/licenses/by/4.0/",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }
      """
    Then the cube Columns should match
      """
      [
        "Dimension",
        "Val",
        "Measure",
        "Unit"
      ]
      """
    Then the cube data should match
      """
      [
      {
      "Dimension": "first",
      "Val": 0,
      "Measure": "length",
      "Unit": "cm",
      },
      {
      "Dimension": "b",
      "Val": 1,
      "Measure": "length",
      "Unit": "cm"
      },
      {
      "Dimension": "c",
      "Val": 2,
      "Measure": "length",
      "Unit": "cm"
      },
      {
      "Dimension": "d",
      "Val": 3,
      "Measure": "length",
      "Unit": "cm"
      },
      {
      "Dimension": "e",
      "Val": 4,
      "Measure": "length",
      "Unit": "cm"
      }
      ]
      """

  Scenario: Successfully outputs a cube using schema v1.3
    Given the config json file "v1.3/qudt-unit-template-testing.json" and the existing tidy data csv file "v1.3/data.csv"
    Then a valid cube can be built and serialised to CSV-W

  Scenario: Successfully outputs a cube using schema v1.4
    Given the config json file "v1.4/basic-test.json" and the existing tidy data csv file "v1.4/basic-test.csv"
    Then a valid cube can be built and serialised to CSV-W

  Scenario: Generate a valid multi-measure pivoted data set containing attributes and units columns given ATTRIBUTE_VALUE_CODELISTS is False
    Given the config json file "v1.4/multi-measure-pivoted-dataset-units-and-attributes.json" and the existing tidy data csv file "v1.4/multi-measure-pivoted-dataset-units-and-attributes.csv"
    And the ATTRIBUTE_VALUE_CODELISTS feature flag is set to False
    When a valid cube is built and serialised to CSV-W
    Then csvwcheck validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests
    And the RDF should contain
      """
      @base <{{rdf_input_directory}}/multi-measure-pivoted-dataset-units-and-attributes.csv>.
      @prefix sector: <{{rdf_input_directory}}/sector.csv#>.
      @prefix year: <{{rdf_input_directory}}/year.csv#>.
      @prefix qb: <http://purl.org/linked-data/cube#>.
      @prefix sdmxa: <http://purl.org/linked-data/sdmx/2009/attribute#>.

      <#obs/2021,services@imports-monetary-value> a qb:Observation;
      <#attribute/imports-status> <#attribute/imports-status/final>;
      <#dimension/sector> sector:services;
      <#dimension/year> year:2021;
      <#measure/imports-monetary-value> 150.0;
      qb:dataSet <#qbDataSet>;
      qb:measureType <#measure/imports-monetary-value>;
      sdmxa:unitMeasure <#unit/pounds-millions> .

      <#obs/2021,services@exports-monetary-value> a qb:Observation;
      <#attribute/exports-status> <#attribute/exports-status/final>;
      <#dimension/sector> sector:services;
      <#dimension/year> year:2021;
      <#measure/exports-monetary-value> 80.0;
      qb:dataSet <#qbDataSet>;
      qb:measureType <#measure/exports-monetary-value>;
      sdmxa:unitMeasure <#unit/pounds-millions>.
    """

  Scenario: Generate a valid multi-measure pivoted data set containing attributes and units columns given ATTRIBUTE_VALUE_CODELISTS is True
    Given the config json file "v1.4/multi-measure-pivoted-dataset-units-and-attributes.json" and the existing tidy data csv file "v1.4/multi-measure-pivoted-dataset-units-and-attributes.csv"
    And the ATTRIBUTE_VALUE_CODELISTS feature flag is set to True
    When a valid cube is built and serialised to CSV-W
    Then csvlint validation of all CSV-Ws should succeed
    And csv2rdf on all CSV-Ws should succeed
    And the RDF should pass "qb, skos" SPARQL tests
    And the RDF should contain
    """
      @base <{{rdf_input_directory}}/multi-measure-pivoted-dataset-units-and-attributes.csv>.
      @prefix sector: <{{rdf_input_directory}}/sector.csv#>.
      @prefix year: <{{rdf_input_directory}}/year.csv#>.
      @prefix attribute: <{{rdf_input_directory}}/multi-measure-pivoted-dataset-units-and-attributes.csv#attribute/>.
      @prefix qb: <http://purl.org/linked-data/cube#>.
      @prefix sdmxa: <http://purl.org/linked-data/sdmx/2009/attribute#>.

    <#obs/2021,services@imports-monetary-value> a qb:Observation;
        attribute:imports-status <{{rdf_input_directory}}/imports-status.csv#final>;
        <#dimension/sector> sector:services;
        <#dimension/year> year:2021;
        <#measure/imports-monetary-value> 150.0;
        qb:dataSet <#qbDataSet>;
        qb:measureType <#measure/imports-monetary-value>;
        sdmxa:unitMeasure <#unit/pounds-millions> .

    <#obs/2021,services@exports-monetary-value> a qb:Observation;
        attribute:exports-status <{{rdf_input_directory}}/exports-status.csv#final>;
        <#dimension/sector> sector:services;
        <#dimension/year> year:2021;
        <#measure/exports-monetary-value> 80.0;
        qb:dataSet <#qbDataSet>;
        qb:measureType <#measure/exports-monetary-value>;
        sdmxa:unitMeasure <#unit/pounds-millions>.
    """
