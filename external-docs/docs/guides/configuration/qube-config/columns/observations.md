# Observations columns

This page discusses what an observations column is, where one should be used, and how one can be defined.

> For a detailed look at an observations column's configuration options, see the [Reference table](#reference) at the bottom of this page.

## What is an observations column?

Observations columns contain the numerical values of observations recorded in the data set, and are the most important component of a cube. In order to be valid, a data cube must include at least one observations column, each of which must have a unit and a measure associated with it. Measures and units can either be defined against the observations column, or can be contained in separate [units](./units.md) and [measures](./measures.md) columns.

## When to use one

Observations columns contain the observed values of your data, and as such your data set must always contain at least one observations column. The configuration of these columns in your data set will primarily depend on the [shape of your data](../../../shape-data/index.md). This is discussed in more detail below.

## Basic configuration

Recall that there are [reserved names](../../convention.md#conventional-column-names) for each column type in your CSV file when following the [configuration by convention](../../convention.md) approach. If your observations column title does not use one of these reserved names, you will need to provide a `qube-config.json` file specifying the column `type` as `observations`.

### Standard shape data sets

| Year | Location | Value |                  Measure |                   Unit |
|:-----|:---------|------:|-------------------------:|-----------------------:|
| 2022 | London   |    35 | Number of Arthur's Bakes |                  Count |
| 2022 | London   |    25 |                  Revenue | GBP Sterling, Millions |
| 2021 | Cardiff  |    26 | Number of Arthur's Bakes |                  Count |
| 2021 | Cardiff  |    18 |                  Revenue | GBP Sterling, Millions |

In this data set the value, measure and unit details are contained in their own columns, so the observations column can be configured as follows; note that this configuration applies to both single and multiple measure standard shape data sets:

```json
{
   "$schema": "https://purl.org/csv-cubed/qube-config/v1",
   "title": "Arthur's Bakes data set",
   "description": "Arthur's Bakes - number of stores and annual revenue",
   "columns": {
      "Value": {
         "type": "observations",
         "data_type": "integer"
      }
   }
}
```

### Pivoted shape data sets

| Year | Location | Number of Arthur's Bakes | Revenue |
|:-----|:---------|-------------------------:|--------:|
| 2022 | London   |                       35 |      25 |
| 2021 | Cardiff  |                       26 |      18 |

In this example of a pivoted shape data set, there are two observation value columns: `Number of Arthur's Bakes` and `Revenue`. As you can see, measure and unit information has been configured within the observations column definitions. For more information on the configuration options available for units and measures, please refer to the [units](./units.md) and [measures](./measures.md) pages:

```json
{
   "$schema": "https://purl.org/csv-cubed/qube-config/v1",
   "title": "Arthur's Bakes data set",
   "description": "Arthur's Bakes - number of stores and annual revenue",
   "columns": {
      "Number of Arthur's Bakes": {
         "type": "observations",
         "data_type": "integer",
         "unit": {
            "label": "Count"
         },
         "measure": {
            "label": "Number of Stores"
         }
      },
      "Revenue": {
         "type": "observations",
         "data_type": "integer",
         "unit": {
            "label": "GBP Sterling (Millions)"
         },
         "measure": {
            "label": "Revenue"
         }
      }
   }
}
```

## Reference

This table shows a list of the possible fields that can be entered when configuring an observations column.

| **field name** | **description**                                                                                                                                                                                                                                                                                                                                                              | **default value** |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| `type`         | The type of the column; to configure an observations column use the value `observations`. (Required)                                                                                                                                                                                                                                                                         | *dimension*       |
| `data_type`    | The [data type](https://www.w3.org/TR/2015/REC-tabular-metadata-20151217/#h-built-in-datatypes) of the observations. This should generally be a decimal or integer. (Optional)                                                                                                                                                                                               | *decimal*         |
| `unit`         | The unit for this observations column; this can be a URI to an existing unit, or a JSON object containing a new or extended existing unit. If there is a unit column this field **must not** be provided. (Optional)                                                                                                                                                         | *none*            |
| `measure`      | The measure for this observations column; this can be a URI to an existing dimension, or a JSON object containing a new or extended existing measure. If your data set is in the [pivoted multi-measure shape](../../../shape-data/pivoted-shape.md#multiple-measures), this field is required. If there is a measure column this field **must not** be provided. (Optional) | *none*            |
