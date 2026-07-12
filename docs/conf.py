#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
# pylint: skip-file

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pymdtools as mymodule
from pymdtools import _about as about


# -- Project information -----------------------------------------------------

project = mymodule.__name__
copyright = getattr(mymodule, '__copyright__', about.__copyright__)
author = getattr(mymodule, '__author__', about.__author__)
release = mymodule.__version__
language = 'en'

# -- General configuration ---------------------------------------------------

html_static_path = ['layout']
templates_path = ['_templates']
exclude_patterns = ['_build']
extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

master_doc = 'index'

# Tell sphinx what the primary language being documented is.
primary_domain = 'py'

# Tell sphinx what the pygments highlight language should be.
highlight_language = 'python'

# -- Options for HTML output -------------------------------------------------
pygments_style = 'friendly'

html_theme = 'sphinx_rtd_theme'
