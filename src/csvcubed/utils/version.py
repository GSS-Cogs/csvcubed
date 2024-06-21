"""
Version
---

Utility to return csvcubed version specific infomation.
"""

from csvcubed.__init__ import __version__


def get_csvcubed_version_uri():
    version_number = f"https://github.com/GSS-Cogs/csvcubed/releases/tag/v{__version__}"
    return version_number


def get_csvcubed_version_string():
    version_string = f"csvcubed v{__version__}"
    return version_string


def get_pypi_release_url():
    pypi_release_url = f"https://pypi.org/project/csvcubed/{__version__}/"
    return pypi_release_url
