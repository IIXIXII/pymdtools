#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
# pylint: skip-file

import os
import sys

sys.path.insert(0, os.path.abspath('..'))

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
exclude_patterns = []
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              ]
source_suffix = ['.rst']

master_doc = 'index'

# Tell sphinx what the primary language being documented is.
primary_domain = 'py'

# Tell sphinx what the pygments highlight language should be.
highlight_language = 'python'

# -- Options for HTML output -------------------------------------------------
pygments_style = 'friendly'

# -- Options for HTML output -------------------------------------------------
# on_rtd is whether we are on readthedocs.org,
# this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'
else:
    html_theme = 'default'
