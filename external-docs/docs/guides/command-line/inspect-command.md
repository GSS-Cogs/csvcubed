# inspect command
The inspect command is used to inspect the metadata of an existing cube.

**Syntax**  
`csvcubed inspect [OPTIONS] TIDY_CSV_PATH`

**Arguments**

| Argument      | Description                                                                                        |
| ------------- | -------------------------------------------------------------------------------------------------- |
| TIDY_CSV_PATH | The file path to the cube data file, formatted as [tidy data](../glossary/index.md#tidy-data) csv. |

**Options**

| Option      | Description                                                                                                      |
| ----------- | ---------------------------------------------------------------------------------------------------------------- |
| --help / -h | Show the command help text.                                                                                      |
| --log-level | Set the desired logging level to one of 'crit', 'err', 'warn', 'info' and 'debug'.  <br/> The default is 'warn'. |

## Logging

Please refer to the [Logging](./logging.md) section to know how the logging works in the inspect command.

## Input types

The inspect command takes data cubes and code lists that are provided in one of two specialised forms of tidy data (i.e. [standard shape](./../../guides/shape-data.md#standard-shape) and [pivoted shape](./../../guides/shape-data.md#pivoted-shape)) as inputs.
  
## Output format

In the following, the format of the outputs generated by the inspect command is discussed.

### Data cube

`csvcubed inspect ./datacube.csv-metadata.json`

```
- This file is a data cube.

- The data cube has the following catalog metadata:
        - Title: 
        - Label:
        - Issued:
        - Modified: 
        - License: 
        - Creator:
        - Publisher:
        - Landing Pages:
        - Themes:
        - Keywords:
        - Contact Point:
        - Identifier:
        - Comment:
        - Description:

- The data cube has the following data structure definition:
        - Dataset Label:
        - Number of Components:
        - Components:
        - Columns where suppress output is true:

- The data cube has the following code list information:
        - Number of Code Lists:
        - Code Lists:

- The data cube has the following dataset information:
        - Number of Observations:
        - Number of Duplicates:
        - First 10 Observations:
        - Last 10 Observations:
        
- The data cube has the following value counts:
        - Value counts broken-down by measure and unit (of measure):
```

* `This file is a data cube` - whether the input CSV-W is of type data cube or code list.
  
* `The data cube has the following catalog metadata`:

  | Sub-section   | Description                                                         |
  | ------------- | ------------------------------------------------------------------- |
  | Title         | Title of the data set.                                              |
  | Label         | Label of the data set.                                              |
  | Issued        | Data set issued timestamp in the `YYYY-DD-MM'T'HH:mm:ssZ` format.   |
  | Modified      | Data set modified timestamp in the `YYYY-DD-MM'T'HH:mm:ssZ` format. |
  | License       | License information.                                                |
  | Creator       | Creator information web page url.                                   |
  | Publisher     | Publisher information web page url.                                 |
  | Landing Pages | List of web urls of landing pages.                                  |
  | Themes        | List of web urls of theme information.                              |
  | Keywords      | List of keywords.                                                   |
  | Contact Point | Contact information.                                                |
  | Identifier    | Data set identifier.                                                |
  | Comment       | Any comments associated with the data set.                          |
  | Description   | Formatted description of the data set.                              |

* `The data cube has the following data structure definition`:

  | Sub-section                           | Description                                                                                                   |
  | ------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
  | Dataset Label                         | Label of the dataset.                                                                                         |
  | Number of Components                  | Number of components in the data structure definition.                                                        |
  | Components                            | List of components with component property, property label, property type, column title and required columns. |
  | Columns where suppress output is true | List of columns where the suppress output is true.                                                            |

* `The data cube has the following code list information`:

  | Sub-section          | Description                                                                 |
  | -------------------- | --------------------------------------------------------------------------- |
  | Number of Code Lists | Number of code lists in the data cube.                                      |
  | Code Lists           | List of codelists with code list uri, code list label, and columns used in. |
  
* `The data cube has the following dataset information`:

  | Sub-section            | Description                                         |
  | ---------------------- | --------------------------------------------------- |
  | Number of Observations | Number of observations (i.e. rows) in the data set. |
  | Number of Duplicates   | Number of duplicated observations in the data set.  |
  | First 10 Observations  | Sample consists of first 10 obervations.            |
  | Last 10 Observations   | Sample consists of last 10 obervations.             |

* `The data cube has the following value counts`- Data set value counts broken-down by measure and unit (of measure).

### Code list

`csvcubed inspect ./codelist.csv-metadata.json`

```
- This file is a code list.

- The code list has the following catalog metadata:
        - Title:
        - Label:
        - Issued:
        - Modified:
        - License:
        - Creator:
        - Publisher:
        - Landing Pages:
        - Themes:
        - Keywords:
        - Contact Point:
        - Identifier:
        - Comment:
        - Description:
        
- The code list has the following dataset information:
        - Number of Concepts:
        - Number of Duplicates:
        - First 10 Concepts:
        - Last 10 Concepts:

- The code list has the following concepts information:
        - Concepts hierarchy depth:
        - Concepts hierarchy:
```

* `This file is a code list` - whether the input CSV-W is of type data cube or code list.
  
* `The code list has the following catalog metadata`:
  
  | Sub-section   | Description                                                         |
  | ------------- | ------------------------------------------------------------------- |
  | Title         | Title of the data set.                                              |
  | Label         | Label of the data set.                                              |
  | Issued        | Data set issued timestamp in the `YYYY-DD-MM'T'HH:mm:ssZ` format.   |
  | Modified      | Data set modified timestamp in the `YYYY-DD-MM'T'HH:mm:ssZ` format. |
  | License       | License information.                                                |
  | Creator       | Creator information web page url.                                   |
  | Publisher     | Publisher information web page url.                                 |
  | Landing Pages | List of web urls of landing pages.                                  |
  | Themes        | List of web urls of theme information.                              |
  | Keywords      | List of keywords.                                                   |
  | Contact Point | Contact information.                                                |
  | Identifier    | Data set identifier.                                                |
  | Comment       | Any comments associated with the data set.                          |
  | Description   | Formatted description of the data set.                              |

* `The code list has the following dataset information`:

  | Sub-section           | Description                                     |
  | --------------------- | ----------------------------------------------- |
  | Number of Concepts    | Number of concepts (i.e. rows) in the data set. |
  | Number of Duplicates  | Number of duplicated concepts in the data set.  |
  | First 10 Observations | Sample consists of first 10 concepts.           |
  | Last 10 Observations  | Sample consists of last 10 concepts.            |

* `The code list has the following concepts information`:

  | Sub-section              | Description                                              |
  | ------------------------ | -------------------------------------------------------- |
  | Concepts hierarchy depth | The hierachy depth of the code list concepts.            |
  | Concepts hierarchy       | Tree representation of the code list concepts hierarchy. |

## Inspect command errors

When errors are encountered, please refer to the [errors guide](../guides/errors/index.md) for help on understanding and resolving them.

## Examples

### Getting help for the inspect command

`csvcubed inspect --help`

```
Options:
  --log-level [warn|err|crit|info|debug]
                                  select a logging level out of: 'warn',
                                  'err', 'crit', 'info' or 'debug'.
  -h, --help                      Show this message and exit.
```

### Inspecting a data cube

`csvcubed inspect ./alcohol-bulletin.csv-metadata.json`

```
- This file is a data cube.

- The data cube has the following catalog metadata:
        - Title: Alcohol Bulletin
        - Label: Alcohol Bulletin
        - Issued: 2016-02-26T09:30:00+00:00
        - Modified: 2022-02-11T21:00:09.286102+00:00
        - License: None
        - Creator: https://www.gov.uk/government/organisations/hm-revenue-customs
        - Publisher: https://www.gov.uk/government/organisations/hm-revenue-customs
        - Landing Pages: 
                -- https://www.gov.uk/government/statistics/alcohol-bulletin
        - Themes: 
                -- http://gss-data.org.uk/def/gdp#trade
        - Keywords: None
        - Contact Point: None
        - Identifier: Alcohol Bulletin
        - Comment: Quarterly statistics from the 4 different alcohol duty regimes administered by HM Revenue and Customs.
        - Description: The Alcohol Bulletin National Statistics present statistics from the 4
                different alcohol duties administered by HM Revenue and Customs (HMRC): [Wine
                Duty](https://www.gov.uk/government/collections/wine-duty) (wine and made-
                wine), [Spirits Duty](https://www.gov.uk/guidance/spirits-duty), [Beer
                Duty](https://www.gov.uk/guidance/beer-duty) and [Cider
                Duty](https://www.gov.uk/government/collections/cider-duty).

                The Alcohol Bulletin is updated quarterly and includes statistics on duty
                receipts up to the latest full month before its release, and statistics
                relating to clearances and production that are one month behind that of duty
                receipts.

                [Archive versions of the Alcohol Bulletin published on GOV.UK after August
                2019](https://webarchive.nationalarchives.gov.uk/ukgwa/*/https://www.gov.uk/government/statistics/alcohol-
                bulletin) are no longer hosted on this page and are instead available via the
                UK Government Web Archive, from the National Archives.

                [Archive versions of the Alcohol Bulletin published between 2008 and August
                2019](https://www.uktradeinfo.com/trade-data/tax-and-duty-bulletins/) are
                found on the UK Trade Info website.

                ## Quality report

                Further details for this statistical release, including data suitability and
                coverage, are included within the [Alcohol Bulletin quality
                report](https://www.gov.uk/government/statistics/quality-report-alcohol-
                duties-publications-bulletin-and-factsheet).

                  *[HMRC]: HM Revenue and Customs
                  *[UK]: United Kingdom

- The data cube has the following data structure definition:
        - Dataset Label: Alcohol Bulletin
        - Number of Components: 17
        - Components:
                                                        Property   Property Label Property Type     Column Title  Required
       http://purl.org/linked-data/sdmx/2009/dimension#refPeriod                      Dimension           Period      True
http://gss-data.org.uk/def/trade/property/dimension/alcohol-type                      Dimension     Alcohol Type      True
                 alcohol-bulletin.csv#dimension/alcohol-sub-type Alcohol Sub Type     Dimension Alcohol Sub Type      True
                  alcohol-bulletin.csv#dimension/alcohol-content  Alcohol Content     Dimension  Alcohol Content      True
                 alcohol-bulletin.csv#dimension/clearance-origin Clearance Origin     Dimension Clearance Origin      True
                    http://purl.org/linked-data/cube#measureType                      Dimension     Measure Type      True
        http://gss-data.org.uk/def/measure/alcohol-duty-receipts                        Measure                       True
           http://gss-data.org.uk/def/measure/beer-duty-receipts                        Measure                       True
          http://gss-data.org.uk/def/measure/cider-duty-receipts                        Measure                       True
                   http://gss-data.org.uk/def/measure/clearances                        Measure                       True
        http://gss-data.org.uk/def/measure/clearances-of-alcohol                        Measure                       True
            http://gss-data.org.uk/def/measure/production-volume                        Measure                       True
    http://gss-data.org.uk/def/measure/production-volume-alcohol                        Measure                       True
        http://gss-data.org.uk/def/measure/spirits-duty-receipts                        Measure                       True
           http://gss-data.org.uk/def/measure/wine-duty-receipts                        Measure                       True
     http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure                      Attribute             Unit      True
       http://purl.org/linked-data/sdmx/2009/attribute#obsStatus                      Attribute           Marker     False
        - Columns where suppress output is true: None

- The data cube has the following code list information:
        - Number of Code Lists: 3
        - Code Lists:
                                   Code List Code List Label  Columns Used In
alcohol-sub-type.csv#scheme/alcohol-sub-type                 Alcohol Sub Type
  alcohol-content.csv#scheme/alcohol-content                  Alcohol Content
clearance-origin.csv#scheme/clearance-origin                 Clearance Origin

- The data cube has the following dataset information:
        - Number of Observations: 10676
        - Number of Duplicates: 0
        - First 10 Observations: 
                   Period Alcohol Type Alcohol Sub Type Alcohol Content Clearance Origin      Value          Measure Type        Unit Marker
government-year/1999-2000         wine            still    up-to-15-abv              all 8721828.97            clearances hectolitres    NaN
government-year/1999-2000         wine        sparkling    up-to-15-abv              all  621067.74            clearances hectolitres    NaN
government-year/1999-2000         wine              all     over-15-abv              all  312545.57            clearances hectolitres    NaN
government-year/1999-2000         wine              all    over-5-5-abv          ex-ship 2248574.50            clearances hectolitres    NaN
government-year/1999-2000         wine              all    over-5-5-abv     ex-warehouse 7393838.35            clearances hectolitres    NaN
government-year/1999-2000         wine              all    over-5-5-abv        uk-origin   13029.44            clearances hectolitres    NaN
government-year/1999-2000         wine              all             all              all 9655442.29            clearances hectolitres    NaN
government-year/1999-2000         wine              all             all              all    1657.00    wine-duty-receipts gbp-million    NaN
government-year/1999-2000         wine              all             all              all    6429.00 alcohol-duty-receipts gbp-million    NaN
government-year/2000-2001         wine            still    up-to-15-abv              all 8920111.13            clearances hectolitres    NaN
        - Last 10 Observations: 
       Period   Alcohol Type Alcohol Sub Type Alcohol Content                    Clearance Origin  Value              Measure Type                 Unit        Marker
month/2021-09          cider              all             all                                 all  25.05       cider-duty-receipts          gbp-million   provisional
month/2021-10           beer               uk             all                                 all    NaN         production-volume thousand-hectolitres not-available
month/2021-10           beer               uk             all                                 all    NaN production-volume-alcohol thousand-hectolitres not-available
month/2021-10 beer-and-cider    uk-registered             all                                 all    NaN                clearances thousand-hectolitres not-available
month/2021-10 beer-and-cider              all             all ex-warehouse-and-ex-ship-clearances    NaN                clearances thousand-hectolitres not-available
month/2021-10           beer              all             all                                 all    NaN                clearances thousand-hectolitres not-available
month/2021-10           beer              all             all                                 all    NaN     clearances-of-alcohol thousand-hectolitres not-available
month/2021-10          cider              all             all                                 all    NaN                clearances thousand-hectolitres not-available
month/2021-10           beer              all             all                                 all 344.74        beer-duty-receipts          gbp-million   provisional
month/2021-10          cider              all             all                                 all  22.60       cider-duty-receipts          gbp-million   provisional
        

- The data cube has the following value counts:
        - Value counts broken-down by measure and unit (of measure):
                  Measure                   Unit  Count
    alcohol-duty-receipts            gbp-million    314
       beer-duty-receipts            gbp-million    314
      cider-duty-receipts            gbp-million    314
               clearances            hectolitres   4710
               clearances hectolitres-of-alcohol    942
               clearances   thousand-hectolitres   1256
    clearances-of-alcohol            hectolitres    942
    clearances-of-alcohol   thousand-hectolitres    314
        production-volume   thousand-hectolitres    314
production-volume-alcohol            hectolitres    314
production-volume-alcohol   thousand-hectolitres    314
    spirits-duty-receipts            gbp-million    314
       wine-duty-receipts            gbp-million    314
```
### Inspecting a code list

`csvcubed inspect ./itis-industry.csv-metadata.json`

```
- This file is a code list.

- The code list has the following catalog metadata:
        - Title: Itis Industry
        - Label: Itis Industry
        - Issued: 2021-04-13T10:04:13.589262
        - Modified: 2021-05-20T10:55:04.059085
        - License: None
        - Creator: None
        - Publisher: None
        - Landing Pages: None
        - Themes: None
        - Keywords: None
        - Contact Point: None
        - Identifier: None
        - Comment: Dataset representing the 'Itis Industry' code list.
        - Description: None
        

- The code list has the following dataset information:
        - Number of Concepts: 9
        - Number of Duplicates: 0
        - First 10 Concepts: 
                                                       Label                                                            Notation Parent Notation  Sort Priority  Description
                                              All industries                                                                 all             NaN              1          NaN
                                               Manufacturing                                              manufacturing-industry             all              2          NaN
                                          Wholesale & Retail                                           wholesale-retail-industry             all              3          NaN
                               Information and Communication                              information-and-communication-industry             all              4          NaN
              Professional, Scientific and Technical Support              professional-scientific-and-technical-support-industry             all              5          NaN
               Administrative and Support Service Activities              administrative-and-support-service-activities-industry             all              6          NaN
Arts, Entertainment, Recreation and Other Service Activities arts-entertainment-recreation-and-other-service-activities-industry             all              7          NaN
                                               Film Industry                              film-industry-excluding-other-services             all              8          NaN
                                         Television Industry                        television-industry-excluding-other-services             all              9          NaN
        - Last 10 Concepts: 
                                                       Label                                                            Notation Parent Notation  Sort Priority  Description
                                              All industries                                                                 all             NaN              1          NaN
                                               Manufacturing                                              manufacturing-industry             all              2          NaN
                                          Wholesale & Retail                                           wholesale-retail-industry             all              3          NaN
                               Information and Communication                              information-and-communication-industry             all              4          NaN
              Professional, Scientific and Technical Support              professional-scientific-and-technical-support-industry             all              5          NaN
               Administrative and Support Service Activities              administrative-and-support-service-activities-industry             all              6          NaN
Arts, Entertainment, Recreation and Other Service Activities arts-entertainment-recreation-and-other-service-activities-industry             all              7          NaN
                                               Film Industry                              film-industry-excluding-other-services             all              8          NaN
                                         Television Industry                        television-industry-excluding-other-services             all              9          NaN
        

- The code list has the following concepts information:
        - Concepts hierarchy depth: 2
        - Concepts hierarchy:
root
└── All industries
    ├── Administrative and Support Service Activities
    ├── Arts, Entertainment, Recreation and Other Service Activities
    ├── Film Industry
    ├── Information and Communication
    ├── Manufacturing
    ├── Professional, Scientific and Technical Support
    ├── Television Industry
    └── Wholesale & Retail
```