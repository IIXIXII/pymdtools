#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
# Copyright (c) 2018 Florent TOURNOIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# -----------------------------------------------------------------------------
"""@package pymdtools
Markdown Tools developed for Gucihet Entreprises
"""

import logging
import sys

from .common import print_conv
from .normalize import md_file_beautifier as markdown_file_beautifier
from .mdtopdf import convert_md_to_pdf
from .instruction import search_include_refs_to_md_file
from .version import __version_info__
from .version import __release_date__


__version__ = '.'.join(str(c) for c in __version_info__)
__author__ = "Florent Tournois"
__copyright__ = "Copyright 2018, Florent Tournois"
__credits__ = ["Arnaud Boidard"]
__license__ = "MIT"
__maintainer__ = "Florent Tournois"
__email__ = "florent.tournois@gmail.fr"
__status__ = "Production"
__module_name__ = "pymdtools"

__all__ = [
    'print_conv',
    'markdown_file_beautifier',
    'convert_md_to_pdf',
    'search_include_refs_to_md_file',
]
