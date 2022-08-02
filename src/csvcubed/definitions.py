"""
Definitions
-----------

Defines the root project path as well as holding the constants that represent uri templates special properties.
"""

from pathlib import Path

"""
Defines a variable to the project root path.
**Must not be used to refer to anything that is not bundled into the whl package**.
"""
APP_ROOT_DIR_PATH = Path(__file__).parent.resolve()


# Special properties that are valid without definition in all uri templates
# Please see: https://www.w3.org/TR/2015/REC-tabular-metadata-20151217/#h-uri-template-properties
URI_TEMPLATE_SPECIAL_PROPERTIES = [
    "_column",
    "_sourceColumn",
    "_row",
    "_sourceRow",
    "_name",
]
