#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################

###############################################################################
# All functions To normalize a markdown file.
#
###############################################################################

import logging
import sys
import os
import os.path

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
    import mistunege as mistune
    import mdrender
else:
    from . import common
    from . import mistunege as mistune
    from . import mdrender


###############################################################################
# Normalize a markdown text.
# with a double conversion, the markdown text is normalized
#
# @param text The markdown text
# @return the normalized markdown text
###############################################################################
def md_beautifier(text):
    logging.debug('Beautify a md content')

    the_renderer = mdrender.MdRenderer()
    markdown = mistune.Markdown(renderer=the_renderer)

    result = markdown(text)

    return result

###############################################################################
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
###############################################################################
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

###############################################################################
# Get the local folder of this script
#
# @return the local folder.
###############################################################################
def get_local_folder():
    return os.path.split(os.path.abspath(os.path.realpath(
        __get_this_filename())))[0]


###############################################################################
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return the filename of THIS script.
###############################################################################
def __get_this_filename():
    result = ""

    if getattr(sys, 'frozen', False):
        # frozen
        result = sys.executable
    else:
        # unfrozen
        result = __file__

    return result

###############################################################################
# Set up the logging system
###############################################################################
def __set_logging_system():
    log_filename = os.path.splitext(os.path.abspath(
        os.path.realpath(__get_this_filename())))[0] + '.log'
    logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                        format='%(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

###############################################################################
# Launch the test
###############################################################################
def __launch_test():
    import pytest
    pytest.main(__get_this_filename())

###############################################################################
# Main script call only if this script is runned directly
###############################################################################
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

    #  __launch_test()

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
