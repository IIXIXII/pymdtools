#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================

import pymdtools as mymodule
from pymdtools import _about as about

# -- Project information -----------------------------------------------------

project = mymodule.__name__
copyright = getattr(mymodule, "__copyright__", about.__copyright__)
author = getattr(mymodule, "__author__", about.__author__)
release = mymodule.__version__
language = "en"

# -- General configuration ---------------------------------------------------

exclude_patterns = ["_build"]
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

master_doc = "index"

# Only explicitly marked snippets are executable; autodoc also contains
# illustrative console sessions that require caller-owned files or state.
doctest_test_doctest_blocks = ""

# Each page's executable examples share a disposable working directory.
doctest_global_setup = """
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_previous_directory = Path.cwd()
_example_directory = TemporaryDirectory(prefix="pymdtools-docs-")
os.chdir(_example_directory.name)
"""
doctest_global_cleanup = """
os.chdir(_previous_directory)
_example_directory.cleanup()
"""

# Tell sphinx what the primary language being documented is.
primary_domain = "py"

# Tell sphinx what the pygments highlight language should be.
highlight_language = "python"

# -- Options for HTML output -------------------------------------------------
pygments_style = "friendly"

html_theme = "sphinx_rtd_theme"
