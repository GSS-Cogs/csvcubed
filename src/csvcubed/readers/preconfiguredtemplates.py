"""
Pre-configured JSON Templates
-----------------------------

Functionality to help augment JSON files with configuration from some pre-configured templates.
"""
import logging
from os import linesep
from typing import Dict, Any
from requests.exceptions import JSONDecodeError, HTTPError

from csvcubed.utils.cache import session
from csvcubed.utils.uri import csvw_column_name_safe

TEMPLATE_BASE_URL = "https://purl.org/csv-cubed/qube-config/templates"

_logger = logging.getLogger(__name__)


def _get_template_file_from_template_lookup(template_value: str) -> str:
    """
    Given the `from_template` value, look up the template in the git repo
    """
    template_lookup_url = f"{TEMPLATE_BASE_URL}/preset_column_config.json"
    template_lookup_response = session.get(template_lookup_url)
    _logger.debug("The template lookup/index file: %s", template_lookup_url)

    if not template_lookup_response.ok:
        raise HTTPError(
            f"Unable to get from url {template_lookup_url}. Status code: {template_lookup_response.status_code}"
        )

    try:
        template_lookup = template_lookup_response.json()
    except JSONDecodeError as e:
        raise Exception(
            f"Could not decode response {linesep}{template_lookup_response}{linesep} from {template_lookup_url}"
        ) from e

    template_file = template_lookup.get(template_value)
    if not template_file:
        raise Exception(f"Couldn't find template your looking for '{template_value}'.")

    return template_file


def _get_properties_from_template_file(template_file: str) -> dict:
    """
    Given the file path to the template, read in all the propeties of that particular template
    """
    template_url = f"{TEMPLATE_BASE_URL}/{template_file}"
    template_response = session.get(template_url)

    if not template_response.ok:
        raise HTTPError(
            f"Unable to get from url {template_url}. Status code: {template_response.status_code}"
        )

    try:
        fetch_template = template_response.json()
    except JSONDecodeError as e:
        raise Exception(
            f"Could not decode response {linesep}{template_response}{linesep} from {template_url}"
        ) from e

    return fetch_template


def apply_preconfigured_values_from_template(
    column_config: Dict[str, Any], column_name: str
) -> None:
    """
    Preset templates are found through template lookup file. Properties are then taken from templates and
    added to column config, with user specified properties overriding template properties.
    """
    # if column_config doesn't have the `from_template` property, just terminate the function now
    if "from_template" not in column_config:
        _logger.debug('Column config for "%s" has no preset template to collect from.', column_name)
        return

    # if column_config has `from_template` property, extract that value
    # remove the `from_template` property
    template_value = column_config["from_template"]
    del column_config["from_template"]

    # given the `from_template` value, look up the template in the git repo
    template_file = _get_template_file_from_template_lookup(template_value)

    # given the file path to the template, read in all the propeties of that particular template
    fetch_template = _get_properties_from_template_file(template_file)

    # insert values from column_config (as long as the user hasn't provided an overriding value for them)
    for template_property in fetch_template:
        if template_property not in column_config:
            if isinstance(fetch_template[template_property], str):
                column_config[template_property] = fetch_template[
                    template_property
                ].replace("<column_name>", csvw_column_name_safe(column_name))
            else:
                column_config[template_property] = fetch_template[template_property]
