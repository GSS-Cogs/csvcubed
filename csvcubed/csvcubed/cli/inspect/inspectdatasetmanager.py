"""
Inspect Dataset Manager
-----------------------

Collection of functions handling csv-related operations used in the inspect cli.
"""


import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd


from csvcubed.models.inspectsparqlresults import (
    QubeComponentResult,
)
from csvcubed.utils.qb.components import (
    ComponentField,
    ComponentPropertyAttributeURI,
    ComponentPropertyType,
    get_component_property_as_relative_path,
)
from csvcubed.models.inspectdataframeresults import (
    DatasetObservationsByMeasureUnitInfoResult,
    DatasetObservationsInfoResult,
    DatasetSingleMeasureResult,
)
from csvcubed.models.csvcubedexception import (
    CsvToDataFrameLoadFailedException,
    InvalidNumberOfRecordsException,
)

_logger = logging.getLogger(__name__)


def _filter_components_from_dsd(
    components: List[QubeComponentResult],
    field: ComponentField,
    filter: str,
) -> List[QubeComponentResult]:
    """
    Filters the components for the given filter.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `List[QubeComponentResult]` - filtered results.
    """

    return [
        component
        for component in components
        if component.as_dict()[field.value] == filter
    ]


def load_csv_to_dataframe(json_path: Path, csv_path: Path) -> pd.DataFrame:
    """
    Loads the csv in given path to a Panda Dataframe.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `DataFrame` - Dataframe of the csv.
    """

    try:
        dataset_path = json_path.parent / csv_path
        _logger.debug(f"Dataset path: {dataset_path.absolute()}")

        dataset = pd.DataFrame(pd.read_csv(dataset_path))
        _logger.info("Successfully loaded csv into dataframe.")

        return dataset
    except Exception as ex:
        raise CsvToDataFrameLoadFailedException from ex


def get_measure_col_name_from_dsd(
    components: List[QubeComponentResult],
) -> Optional[str]:
    """
    Identifies the name of measure column.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `Optional[str]`
    """
    filtered_components = _filter_components_from_dsd(
        components,
        ComponentField.Property,
        ComponentPropertyAttributeURI.MeasureType.value,
    )

    return (
        filtered_components[0].csv_col_title
        if filtered_components[0] and filtered_components[0].csv_col_title != ""
        else None
    )


def get_unit_col_name_from_dsd(
    components: List[QubeComponentResult],
) -> Optional[str]:
    """
    Identifies the name of unit column.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `Optional[str]`
    """
    filtered_components = _filter_components_from_dsd(
        components,
        ComponentField.Property,
        ComponentPropertyAttributeURI.UnitMeasure.value,
    )

    return (
        filtered_components[0].csv_col_title
        if filtered_components[0] and filtered_components[0].csv_col_title != ""
        else None
    )


def get_single_measure_from_dsd(
    components: List[QubeComponentResult], json_path: Path
) -> DatasetSingleMeasureResult:
    """
    Identifies the measure uri and label for single-measure dataset.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `DatasetSingleMeasureResult`
    """
    filtered_components = _filter_components_from_dsd(
        components, ComponentField.PropertyType, ComponentPropertyType.Measure.value
    )

    if len(filtered_components) != 1:
        raise InvalidNumberOfRecordsException(
            excepted_num_of_records=1, num_of_records=len(filtered_components)
        )

    return DatasetSingleMeasureResult(
        measure_uri=get_component_property_as_relative_path(
            json_path, filtered_components[0].property
        ),
        measure_label=filtered_components[0].property_label,
    )


def get_dataset_observations_info(
    dataset: pd.DataFrame,
) -> DatasetObservationsInfoResult:
    """
    Generates the `DatasetObservationsInfoResult` from the dataset.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `DatasetObservationsInfoResult`
    """
    return DatasetObservationsInfoResult(
        len(dataset.index),
        dataset.duplicated().sum(),
        dataset.head(n=10),
        dataset.tail(n=10),
    )


def get_dataset_val_counts_info(
    dataset: pd.DataFrame, measure_col: str, unit_col: str
) -> DatasetObservationsByMeasureUnitInfoResult:
    """
    Generates the `DatasetObservationsByMeasureUnitInfoResult` from the dataset.

    Member of :file:`./inspectdatasetmanager.py`

    :return: `DatasetObservationsByMeasureUnitInfoResult`
    """
    _logger.debug(f"Dataset measure column name: {measure_col}")
    _logger.debug(f"Dataset unit column name: {unit_col}")

    by_measure_and_unit_grouped = dataset.groupby([measure_col, unit_col])

    return DatasetObservationsByMeasureUnitInfoResult(
        by_measure_and_unit_val_counts_df=pd.DataFrame(
            by_measure_and_unit_grouped.size().reset_index()
        )
    )
