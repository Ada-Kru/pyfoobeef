# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
import sys
from pathlib import Path

module_dir = Path(__file__).absolute().parent
lib_path = str(module_dir / "lib")
sys.path.insert(0, lib_path)


# -- Project information -----------------------------------------------------

project = "pyfoobeef"
copyright = "2019, Adam Krueger"
author = "Adam Krueger"

# The full version, including alpha/beta/rc tags
release = "0.9"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.autosummary"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "setup.py",
    "helper_funcs.py",
    "types.py",
    "exceptions.py",
    "endpoints.py",
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "classic"
html_theme_options = {
    "stickysidebar": True,
    "externalrefs": True,
    "sidebarbgcolor": "#444",
    "sidebarlinkcolor": "#FFF04B",
    "bgcolor": "#DDDDDD",
    "linkcolor": "FFEA00",
    "visitedlinkcolor": "DDC800",
    "codebgcolor": "#EEE",
    "codetextcolor": "#DDDDDD",
    "relbarbgcolor": "#222",
    "headbgcolor": "#222",
    "headtextcolor": "#EEEEEE",
    "footerbgcolor": "#222",
    "footertextcolor": "#EEEEEE",
}
pygments_style = "tango"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_sidebars = {
    "**": [
        "globaltoc.html",
        "relations.html",
        "sourcelink.html",
        "searchbox.html",
    ]
}
