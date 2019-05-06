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
# test the file normalize
#
###############################################################################

import logging
import sys
import os
import os.path
import pytest

if (__package__ in [None, '']) and ('.' not in __name__):
    import instruction
    import test_general
else:
    from . import instruction
    from . import test_general

def test_strip_xml_comment():
        kjhlfkjsdh
    assert strip_xml_comment("<!---->") == ""
    assert strip_xml_comment("<!-- -->") == ""
    assert strip_xml_comment("<!-- test-->") == ""
    assert strip_xml_comment("<!-- test---->") == ""
    assert strip_xml_comment("A<!---->B") == "AB"
    assert strip_xml_comment("A<!-- -->B") == "AB"
    assert strip_xml_comment("A<!-- test-->B") == "AB"
    assert strip_xml_comment("A<!-- test---->B") == "AB"

    assert strip_xml_comment("<!---->x<!---->") == "x"
    assert strip_xml_comment("<!-- -->x<!-- -->") == "x"
    assert strip_xml_comment("<!-- test-->xx<!-- test---->") == "xx"
    assert strip_xml_comment("<!-- test---->xx<!-- test---->") == "xx"
    assert strip_xml_comment("A<!---->B<!---->") == "AB"
    assert strip_xml_comment("A<!-- -->B") == "AB"
    assert strip_xml_comment("A<!-- test--><!-- test-->B") == "AB"
    assert strip_xml_comment("A<!-- test----><!-- test--><!-- test-->B") == \
        "AB"
    assert strip_xml_comment("""A<!-- test
    ----><!-- test--><!-- test-->B""") == \
        "AB"

###############################################################################
# find the file for test
###############################################################################
def find_md_include_test():
    return test_general.find_test_file_couple(
        "_MdInclude.md", filename_ext=".tmd",
        folder_search=test_general.get_test_folder() + "/md_include/")

###############################################################################
# test the md_file_beautifier
###############################################################################
@pytest.mark.parametrize("filename, filename_result", find_md_include_test())
def test_md_file_include(filename, filename_result):
    test_general.check_trans_file_inside_fun(
        filename,
        filename_result,
        instruction.search_include_refs_to_md_file,
        filename_ext=".tmd")


###############################################################################
# Create result md_beautifier
###############################################################################
def create_result_md_include(force_creation=False):
    test_general.create_result_trans_file_inside(
        instruction.search_include_refs_to_md_file,
        "_MdInclude.md",
        folder_search=test_general.get_test_folder() + "/md_include/level1/",
        force_creation=force_creation,
        filename_ext=".tmd")

###############################################################################
# find the file for test
###############################################################################
def find_md_var_test():
    return test_general.find_test_file_couple(
        "_MdVar.md", filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/md_var/")

###############################################################################
# test the md_file_beautifier
###############################################################################
@pytest.mark.parametrize("filename, filename_result", find_md_var_test())
def test__md_file_var(filename, filename_result):
    test_general.check_trans_file_inside_fun(
        filename, filename_result, instruction.search_include_vars_to_md_file)

###############################################################################
# Create result md_beautifier
###############################################################################
def create_result_md_var(force_creation=False):
    test_general.create_result_trans_file_inside(
        instruction.search_include_vars_to_md_file,
        "_MdVar.md",
        folder_search=test_general.get_test_folder() + "/md_var/",
        force_creation=force_creation,
        filename_ext=".md")

###############################################################################
# find the file for test
###############################################################################
def find_include_file_test():
    return test_general.find_test_file_couple(
        "_IncludeFile.md",
        filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/include_file/")

###############################################################################
# test the md_file_beautifier
###############################################################################
@pytest.mark.parametrize("filename, filename_result", find_include_file_test())
def test_include_files_to_md_file(filename, filename_result):
    test_general.check_trans_file_inside_fun(
        filename, filename_result, instruction.include_files_to_md_file)

###############################################################################
# Create result md_beautifier
###############################################################################
def create_result_include_file(force_creation=False):
    test_general.create_result_trans_file_inside(
        instruction.include_files_to_md_file,
        "_IncludeFile.md",
        folder_search=test_general.get_test_folder() + "/include_file/",
        force_creation=force_creation,
        filename_ext=".md")


###############################################################################
# Launch the test
###############################################################################
def __launch_test():
    pytest.main(__get_this_filename())


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
# Main script call only if this script is runned directly
###############################################################################
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

    #  create_result_md_include(force_creation = True)
    #  create_result_md_var(force_creation = True)
    #  create_result_include_file(force_creation = True)

    test_general.find_and_launch_test(
        find_md_include_test, test_md_file_include)
    test_general.find_and_launch_test(find_md_var_test, test__md_file_var)
    test_general.find_and_launch_test(
        find_include_file_test, test_include_files_to_md_file)

    __launch_test()

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
