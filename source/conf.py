# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from csvcubed import __version__

project = "csvcubed"
author = "Integrated Data Service - Dissemination <csvcubed@gsscogs.uk>"
version = __version__
release = __version__
license = "Apache-2.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
]
templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "python_docs_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_sidebars = {"**": ["globaltoc.html", "sourcelink.html", "searchbox.html"]}
