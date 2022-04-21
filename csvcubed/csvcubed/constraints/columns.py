from dataclasses import dataclass
from enum import Enum
import json
from typing import Dict, List, Optional


class ColType(Enum):
    DIMENSION = "dimension"
    MEASURE = "measure"
    ATTRIBUTE = "attribute"
    MEASURE_TYPE = "measure type"


@dataclass
class ColumnRef:
    """
    A class to hold the information from the [tables][tableSchema] dictionary of the csvw
    defining a column, along with additional information that can inferred from that.
    """

    csvw_as_dict: Optional[dict]  # pointer
    initial_column_dict: dict

    # (possible) existing values
    name: Optional[str]
    title: Optional[str]
    required: Optional[str] = None
    propertyUrl: Optional[str] = None
    valueUrl: Optional[str] = None

    # values we (possibly) are inferring
    implicit_component_postfix: Optional[str] = None
    implicit_url_differentiator: Optional[str] = None
    implied_type: Optional[ColType] = None

    def serialised(self) -> str:
        """
        Simple json serialiser for debugging
        """
        jsonified = {
            "from_csvw_column_definition": {
                "name": self.name,
                "title": self.title,
                "required": self.required,
                "propertyUrl": self.propertyUrl,
                "valueUrl": self.valueUrl,
            },
            "implied_extrapolated_values": {
                "implicit_component_postfix": self.implicit_component_postfix,
                "implicit_url_differentiator": self.implicit_url_differentiator,
                "implied_type": self.implied_type.value,
            },
        }

        return json.dumps(jsonified, indent=2)

    def populate(self):
        """
        Populates fields we can infer but don't have to begin with
        """
        self.set_implied_type()
        self.set_implicit_component_postfix()
        self.set_impicit_url_differentiator()

    # TODO - consider case of not having a propertyUrl
    def set_implied_type(self):
        """
        From the information we have, "guess" the type of column based on the
        information provided within a given columns propertyUrl
        """
        if not self.propertyUrl:
            return  # TODO - consider ramifications

        matches = []

        if any(["/dimension/" in self.propertyUrl, "/dimension#" in self.propertyUrl]):
            matches.append(ColType.DIMENSION)

        elif any(
            [
                "/attribute/" in self.propertyUrl,
                "#attribute/" in self.propertyUrl,
                "/attribute#" in self.propertyUrl,
            ]
        ):
            matches.append(ColType.ATTRIBUTE)

        elif "/measure/" in self.propertyUrl:
            matches.append(ColType.MEASURE)

        elif "/cube#measureType" in self.propertyUrl:
            matches.append(ColType.MEASURE_TYPE)

        else:
            raise ValueError(
                f"Unable to identify column type from propertyUrl {self.propertyUrl}"
            )

        assert len(matches) == 1, (
            f"Logic error. {self.propertyUrl} is matching"
            "more than one implied column type."
        )
        self.implied_type = matches[0]

    def set_implicit_component_postfix(self):
        """
        The end part of the implied component identifier being used by csvcubed,

        example:
        uk-services-trade-by-business-characteristics.csv#component/period
        from:
        <SOME-ROOT-DOMAIN/uk-services-trade-by-business-characteristics.csv#component/period>
        """
        url = self.csvw_as_dict["tables"][0]["url"]
        self.implicit_component_postfix = (
            f'{url}#component/{self.name.replace("_", "-")}'
        )

    def set_impicit_url_differentiator(self):
        """
        By "impicit_url_differentiator" I mean the bit on the end of urls that
        renders them unique within a given namespace.

        Examples:
        refPeriod        : http://purl.org/linked-data/sdmx/2009/dimension#refPeriod
        flow-directions  : http://gss-data.org.uk/def/trade/property/dimension/flow-directions
        """

        if "propertyUrl" not in self.initial_column_dict:
            return  # TODO - consider ramifications

        property_url_value = self.initial_column_dict["propertyUrl"]
        implicit_identifier_index = max(
            property_url_value.rfind("/"), property_url_value.rfind("#")
        )
        implicit_url_differentiator = property_url_value[implicit_identifier_index+1:]

        self.implicit_url_differentiator = implicit_url_differentiator


class ColumnRefList:
    """
    A class denoting a list of class: ColumnRef with attached methods for
    filtering and/or acquiring specific subsets of said column classes without
    having to repeat expensive reads.
    """

    def __init__(self, csvw_as_dict: dict):
        column_dicts_as_list = csvw_as_dict["tables"][0]["tableSchema"]["columns"]
        self.columnref_objects: Dict[str, ColumnRef] = {}
        for column_dict in column_dicts_as_list:

            # ignore virtual columns
            # TODO: consider if this is wise
            name: str = column_dict["name"]
            if name.startswith("virt_"):
                continue

            col_ref: ColumnRef = ColumnRef(
                csvw_as_dict=csvw_as_dict,
                initial_column_dict=column_dict,
                name=name,
                title=column_dict.get("titles")[0]
                if isinstance(column_dict, list)
                else column_dict.get("titles")
                if column_dict.get("titles")
                else None,
                propertyUrl=column_dict.get("propertyUrl"),
                valueUrl=column_dict.get("valueUrl"),
                required=column_dict.get("required"),
            )
            col_ref.populate()

            self.columnref_objects[name] = col_ref

    def get_all(self) -> List[ColumnRef]:
        """
        Get all ColumnRef objects in a list
        """
        return list(self.columnref_objects.values())

    def get(self, column_label: str) -> ColumnRef:
        """
        Get a specific ColumnRef object by name
        """
        colref: Optional[ColumnRef] = self.columnref_objects.get(column_label)
        if not colref:
            raise KeyError('No ColumnRef object found under the name '
                f'{column_label}, got {self.columnref_objects}')
        return colref

    def get_dimensions(self) -> List[ColumnRef]:
        """
        Get a list of class ColumnRef representing dimensions
        """
        return [x for x in self.get_all() if x.implied_type == ColType.DIMENSION]

    def get_attributes(self) -> List[ColumnRef]:
        """
        Get a list of class ColumnRef representing attributes
        """
        return [x for x in self.get_all() if x.implied_type == ColType.ATTRIBUTE]

    def get_measures(self) -> List[ColumnRef]:
        """
        Get a list of class ColumnRef representing measures
        """
        return [x for x in self.get_all() if x.implied_type == ColType.MEASURE]

    def get_measuretype(self) -> ColumnRef:
        """
        Get the class ColumnRef representing measureType
        """

        measure_type = [
            x for x in self.get_all() if x.implied_type == ColType.MEASURE_TYPE
        ]
        assert len(measure_type) == 1
        return measure_type[0]
