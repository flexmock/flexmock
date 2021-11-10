"""Flexmock Sphinx documentation configuration file.

This file adds Sphinx support for documentation so that man pages can be
generated using Sphinx.
"""
import os
import sys

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "flexmock"
copyright = "2021, Slavek Kabrda, Herman Sheremetyev"

# -- General configuration ---------------------------------------------------

extensions = ["myst_parser"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "toctree"
exclude_patterns = ["api.md", "changelog.md", "contributing.md"]

# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ("toctree", "flexmock", "flexmock Documentation", ["Slavek Kabrda, Herman Sheremetyev"], 1)
]
