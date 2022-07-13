Feature: Cube!
  As a data engineer.
  I want to create a cube from a tidy data csv, with or without a config json file
  That conforms to the documented conventions for column headings.

  Scenario: Output a cube and errors when created from both config and data
    Given The config json file "v1.0/cube_data_config_ok.json" and the existing tidy data csv file "v1.0/cube_data_config_ok.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
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
    Then The cube data should match
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
    Given The existing tidy data csv file "v1.0/cube_data_convention_ok.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
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
    Then The cube data should match
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
    Given The config json file "v1.0/cube_data_part_config.json" and the existing tidy data csv file "v1.0/cube_data_part_config.csv"
    When The cube is created
    Then The cube Metadata should match
      """
      {"title": "Tests/test-cases/config/schema-cube-data-config-ok",
      "identifier": "schema-id",
      "summary": "a summary",
      "description": "Schema for testing",
      "creator_uri": "https://www.gov.uk/government/organisations/office-for-national-statistics",
      "publisher_uri": "http://statistics.data.gov.uk",
      "landing_page_uris": [],
      "theme_uris": ["A Theme"],
      "keywords": ["two"],
      "dataset_issued": "2022-03-04T17:00:00",
      "dataset_modified": "2022-03-04T18:00:00",
      "license_uri": "the license",
      "public_contact_point_uri": None,
      "uri_safe_identifier_override": None
      }

      """

  Scenario: Output a cube when the code list is defined using code list config schema v1.0 and when the concepts are hierarchical, and the sort order is defined with sort object
    Given The config json file "v1.1/cube_config_hierarchical.json" and the existing tidy data csv file "v1.1/data.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
      """
      [
        "Dimension",
        "Value",
        "Measure",
        "Unit"
      ]
      """
    Then The cube data should match
      """
      [
        {
          "Dimension": "a",
          "Value": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Value": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Value": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Value": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Value": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when the code list is defined using code list config schema v1.0 and when the concepts are not hierarchical, and the sort order is defined with sort object
    Given The config json file "v1.1/cube_config_none_hierarchical.json" and the existing tidy data csv file "v1.1/data.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
      """
      [
        "Dimension",
        "Value",
        "Measure",
        "Unit"
      ]
      """
    Then The cube data should match
      """
      [
        {
          "Dimension": "a",
          "Value": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Value": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Value": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Value": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Value": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when an inline code list is defined using code list config schema v1.0, and the sort order is defined with sort object
    Given The config json file "v1.1/cube_config_inline_code_list.json" and the existing tidy data csv file "v1.1/data.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
      """
      [
        "Dimension",
        "Value",
        "Measure",
        "Unit"
      ]
      """
    Then The cube data should match
      """
      [
        {
          "Dimension": "a",
          "Value": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Value": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Value": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Value": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Value": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when the sort object is not defined but the sort order is defined
    Given The config json file "v1.1/cube_config_hierarchical_without_sort.json" and the existing tidy data csv file "v1.1/data.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
      """
      [
        "Dimension",
        "Value",
        "Measure",
        "Unit"
      ]
      """
    Then The cube data should match
      """
      [
        {
          "Dimension": "a",
          "Value": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Value": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Value": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Value": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Value": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when the code list is defined using code list config schema v1.0 and when there are references to concepts defined elsewhere.
    Given The config json file "v1.1/cube_config_with_concepts_defined_elsewhere.json" and the existing tidy data csv file "v1.1/data.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
      """
      [
        "Dimension",
        "Value",
        "Measure",
        "Unit"
      ]
      """
    Then The cube data should match
      """
      [
        {
          "Dimension": "a",
          "Value": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Value": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Value": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Value": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Value": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Output a cube when an inline code list is defined using code list config schema v1.0 and when there are references to concepts defined elsewhere.
    Given The config json file "v1.1/cube_config_inline_code_list_with_concepts_defined_elsewhere.json" and the existing tidy data csv file "v1.1/data.csv"
    When The cube is created
    Then The cube Metadata should match
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
    Then The cube Columns should match
      """
      [
        "Dimension",
        "Value",
        "Measure",
        "Unit"
      ]
      """
    Then The cube data should match
      """
      [
        {
          "Dimension": "a",
          "Value": 0,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "b",
          "Value": 1,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "c",
          "Value": 2,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "d",
          "Value": 3,
          "Measure": "length",
          "Unit": "cm"
        },
        {
          "Dimension": "e",
          "Value": 4,
          "Measure": "length",
          "Unit": "cm"
        }
      ]
      """

  Scenario: Supress a column when the config.json file has a boolean value assined to that column.
    Given The config json file "v1.3/cube_data_config_false_column.json" and the existing tidy data csv file "v1.3/cube_data_config_ok.csv"
    When The cube is created
    Then The cube Columns should match
      """
      [
        "Dim-0",
        "Dim-2",
        "Attr-1",
        "Amount",
        "Measure",
        "Units"
      ]
      """