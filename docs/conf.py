#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
# pylint: skip-file

from recommonmark.parser import CommonMarkParser
import os
import sys
import recommonmark
from recommonmark.transform import AutoStructify
import textwrap
import pymdtools as mymodule

sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = mymodule.__name__
copyright = mymodule.__copyright__
author = mymodule.__author__
release = mymodule.__version__
language = 'en'

# -- General configuration ---------------------------------------------------

html_static_path = ['layout']
templates_path = ['_templates']
exclude_patterns = []
extensions = ['m2r',
              'breathe',
              'exhale',
              ]
source_suffix = ['.rst', '.md']

master_doc = 'index'


# -- Setup the breathe extension ---------------------------------------------
breathe_projects = {
    "pymdtools": "./doxyoutput/xml"
}
breathe_default_project = "pymdtools"

# -- Setup the exhale extension ---------------------------------------------
exhale_args = {
    # These arguments are required
    "containmentFolder": "./api",
    "rootFileName": "library_root.rst",
    "rootFileTitle": "Library API",
    "doxygenStripFromPath": "..",
    # Suggested optional arguments
    "createTreeView": True,
    # TIP: if using the sphinx-bootstrap-theme, you need
    # "treeViewIsBootstrap": True,
    "exhaleExecutesDoxygen": True,
    # "exhaleDoxygenStdin": textwrap.dedent('''
    #     INPUT = ../pymdtools
    #     EXCLUDE_SYMBOLS  = *test_* \
    #                      __main \
    #                      __set_logging_system \
    #                      __get_this_filename \
    #                      __get_this_folder \
    #                      is_frozen \
    #                      __launch_test
    # ''')
    "exhaleDoxygenStdin": "INPUT = ../pymdtools"
}

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
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
else:
    html_theme = 'default'
