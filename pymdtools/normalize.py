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
"""All functions To normalize a markdown file."""

import logging
import os
import os.path

from . import common
from . import mistunege as mistune
from . import mdrender


# -----------------------------------------------------------------------------
# Normalize a markdown text.
# with a double conversion, the markdown text is normalized
#
# @param text The markdown text
# @return the normalized markdown text
# -----------------------------------------------------------------------------
def md_beautifier(text):
    logging.debug('Beautify a md content')

    the_renderer = mdrender.MdRenderer()
    markdown = mistune.Markdown(renderer=the_renderer)

    result = markdown(text).strip()

    return result

# -----------------------------------------------------------------------------
# Normalize a markdown text.
# with a double conversion, the markdown text is normalized
# This function take a file, load the content, create a backup (if needed)
# and do some change in the file which is supposed to be a markdown file.
# Then saved the new file with the same filename. The goal is to
# beautify the markdown file.
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param backup_option This parameter is set to true by default.
#                      If the backup option is set,
#                             then a file named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @return the filename normalized
# -----------------------------------------------------------------------------
def md_file_beautifier(filename, backup_option=True, filename_ext=".md"):
    """
    This function take a file, load the content, create a backup (if needed)
    and do some change in the file which is supposed to be a markdown file.
    Then saved the new file with the same filename. The goal is to beautify
    the markdown file.

    @type filename: string
    @param filename: The name and path of the file to work with. This file is
                     supposed to be a markdown file.

    @type backup_option: boolean
    @param backup_option: This parameter is set to true by default.
                          If the backup option is set,
                          then a file named filename.bak will be created.

    @type filename_ext: string
    @param filename_ext: This parameter the markdown extension
                         for the filename.

    @return nothing
    """
    logging.debug('Beautify the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename)
    if len(text) == 0:
        logging.error('The fielname %s seem empty', filename)
        raise Exception('The fielname %s seem empty' % filename)

    # Create Backup
    if backup_option:
        common.create_backup(filename)

    # Change inside
    text = md_beautifier(text)

    # Save the file
    os.remove(filename)
    common.set_file_content(filename, text, encoding="utf-8")
