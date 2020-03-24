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

# -----------------------------------------------------------------------------
# test the file normalize
#
# -----------------------------------------------------------------------------

import logging
import sys
import os
import os.path
import re
import pytest

import pymdtools.instruction as instruction
import test_general

def test_set_var_to_md_text():
    assert(instruction.set_var_to_md_text('<!-- var(essai) = "tes\\t" -->text',
                                          "test",
                                          "good") == '<!-- var(essai) = "tes'
           '\\t" -->\n'
           '<!-- var(test)="good" -->\n\ntext')
    assert(instruction.set_var_to_md_text('<!-- var(essai) = "tes\\t" -->text',
                                          "essai", "good") ==
           '<!-- var(essai)="good" -->text')

def test_strip_xml_comment():
    assert instruction.strip_xml_comment("<!---->") == ""
    assert instruction.strip_xml_comment("<!-- -->") == ""
    assert instruction.strip_xml_comment("<!-- test-->") == ""
    assert instruction.strip_xml_comment("<!-- test---->") == ""
    assert instruction.strip_xml_comment("A<!---->B") == "AB"
    assert instruction.strip_xml_comment("A<!-- -->B") == "AB"
    assert instruction.strip_xml_comment("A<!-- test-->B") == "AB"
    assert instruction.strip_xml_comment("A<!-- test---->B") == "AB"

    assert instruction.strip_xml_comment("<!---->x<!---->") == "x"
    assert instruction.strip_xml_comment("<!-- -->x<!-- -->") == "x"
    assert instruction.strip_xml_comment("<!-- test-->xx<!-- test---->") == \
        "xx"
    assert instruction.strip_xml_comment("<!-- test---->xx<!-- test---->") == \
        "xx"
    assert instruction.strip_xml_comment("A<!---->B<!---->") == "AB"
    assert instruction.strip_xml_comment("A<!-- -->B") == "AB"
    assert instruction.strip_xml_comment("A<!-- test--><!-- test-->B") == "AB"
    assert instruction.strip_xml_comment("A<!-- test---->"
                                         "<!-- test--><!-- test-->B") == \
        "AB"
    assert instruction.strip_xml_comment("""A<!-- test
    ----><!-- test--><!-- test-->B""") == \
        "AB"

# -----------------------------------------------------------------------------
# find the file for test
# -----------------------------------------------------------------------------
def find_md_include_test():
    return test_general.find_test_file_couple(
        "_MdInclude.md", filename_ext=".tmd",
        folder_search=test_general.get_test_folder() + "/md_include/")

# -----------------------------------------------------------------------------
# test the md_file_beautifier
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("filename, filename_result", find_md_include_test())
def test_md_file_include(filename, filename_result):
    test_general.check_trans_file_inside_fun(
        filename,
        filename_result,
        instruction.search_include_refs_to_md_file,
        filename_ext=".tmd")


# -----------------------------------------------------------------------------
# Create result md_beautifier
# -----------------------------------------------------------------------------
def create_result_md_include(force_creation=False):
    test_general.create_result_trans_file_inside(
        instruction.search_include_refs_to_md_file,
        "_MdInclude.md",
        folder_search=test_general.get_test_folder() + "/md_include/level1/",
        force_creation=force_creation,
        filename_ext=".tmd")

# -----------------------------------------------------------------------------
# find the file for test
# -----------------------------------------------------------------------------
def find_md_var_test():
    return test_general.find_test_file_couple(
        "_MdVar.md", filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/md_var/")

# -----------------------------------------------------------------------------
# test the md_file_beautifier
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("filename, filename_result", find_md_var_test())
def test__md_file_var(filename, filename_result):
    test_general.check_trans_file_inside_fun(
        filename, filename_result, instruction.search_include_vars_to_md_file)

# -----------------------------------------------------------------------------
# Create result md_beautifier
# -----------------------------------------------------------------------------
def create_result_md_var(force_creation=False):
    test_general.create_result_trans_file_inside(
        instruction.search_include_vars_to_md_file,
        "_MdVar.md",
        folder_search=test_general.get_test_folder() + "/md_var/",
        force_creation=force_creation,
        filename_ext=".md")

# -----------------------------------------------------------------------------
# find the file for test
# -----------------------------------------------------------------------------
def find_include_file_test():
    return test_general.find_test_file_couple(
        "_IncludeFile.md",
        filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/include_file/")

# -----------------------------------------------------------------------------
# test the md_file_beautifier
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("filename, filename_result", find_include_file_test())
def test_include_files_to_md_file(filename, filename_result):
    test_general.check_trans_file_inside_fun(
        filename, filename_result, instruction.include_files_to_md_file)

# -----------------------------------------------------------------------------
# Create result md_beautifier
# -----------------------------------------------------------------------------
def create_result_include_file(force_creation=False):
    test_general.create_result_trans_file_inside(
        instruction.include_files_to_md_file,
        "_IncludeFile.md",
        folder_search=test_general.get_test_folder() + "/include_file/",
        force_creation=force_creation,
        filename_ext=".md")

def test_get_vars_from_md_text():
    assert(instruction.get_vars_from_md_text('<!-- var(essai) = "tes\\t" -->')
           ['essai'] == "tes\\t")
    assert(instruction.get_vars_from_md_text('<!-- var(essai) = "tes\"t" -->')
           ['essai'] == "tes\"t")
    assert(instruction.get_vars_from_md_text(
        '<!-- var(essai)="test" -->'
        '<!-- var(essai2)="test" -->')['essai'] == "test")

def test_del_var_to_md_text():
    fun = instruction.del_var_to_md_text
    assert(fun('<!-- var(essai) = "tes\\t" -->', "test") ==
           '<!-- var(essai) = "tes\\t" -->')
    assert(fun('x<!-- var(essai) = "tes\\t" -->x', "essai") == 'xx')

def test_get_title_from_md_text():
    assert instruction.get_title_from_md_text("""
DQP002 - ADMINISTRATEUR JUDICIAIRE
==================================

1°. Définition de l'activité
-----------------

L'administrateur judiciaire est un professionnel
""") == "DQP002 - ADMINISTRATEUR JUDICIAIRE"

    assert instruction.get_title_from_md_text("""
<!--
qsdlkjhl
=======
-->

qsdfqsdf
qsdf
DQP002 - ADMINISTRATEUR JUDICIAIRE
==================================

1°. Définition de l'activité
-----------------

L'administrateur judiciaire est un professionnel
""") == "DQP002 - ADMINISTRATEUR JUDICIAIRE"

def test_set_title_in_md_text():
    result = """
    DQP015 - Anatomie et cytologie
==============================
===========================

1------------------"""
    new_second_line = "=============================="
    line_re = new_second_line + '(\n|\r\n)' + "(=+)(\n|\r\n)"
    result = re.sub(line_re, new_second_line + '\n', result)
    result = instruction.set_title_in_md_text(result, "yitruytr")
    # print(repr(result))

def test_get_file_content_include():
    assert instruction.get_file_content_to_include(
        "license.txt")[0:4] == "Copy"
    assert instruction.get_file_content_to_include(
        "license.en.txt")[0:4] == "Copy"

def test_include_files_to_md_text():
    result1 = instruction.include_files_to_md_text(
        '<!-- include-file(license.txt) -->')
    result2 = instruction.include_files_to_md_text(result1)
    assert result1 == result2

def test_set_include_file_():
    assert(instruction.set_include_file_to_md_text(
        '<!-- include-file(test) -->',
        "test") == '<!-- include-file(test) -->')
    assert(instruction.set_include_file_to_md_text(
        '<!-- include-file(essai) -->text',
        "test") == '<!-- include-file(essai) -->\n'
                   '<!-- include-file(test) -->\n\ntext')

def test_del_include_file_():
    assert(instruction.del_include_file_to_md_text(
        '<!-- include-file(test) -->',
        "test") == '')
    assert(instruction.del_include_file_to_md_text(
        '<!-- include-file(essai) -->',
        "test") == '<!-- include-file(essai) -->')


# -----------------------------------------------------------------------------
# Launch the test
# -----------------------------------------------------------------------------
def __launch_test():
    pytest.main(__get_this_filename())


# -----------------------------------------------------------------------------
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return the filename of THIS script.
# -----------------------------------------------------------------------------
def __get_this_filename():
    result = ""

    if getattr(sys, 'frozen', False):
        # frozen
        result = sys.executable
    else:
        # unfrozen
        result = __file__

    return result

# -----------------------------------------------------------------------------
# Set up the logging system
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Main script call only if this script is runned directly
# -----------------------------------------------------------------------------
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

    # test_strip_xml_comment()

    # create_result_md_include(force_creation=True)
    #  create_result_md_var(force_creation = True)
    create_result_include_file(force_creation=True)

#     test_general.find_and_launch_test(
#         find_md_include_test, test_md_file_include)
#     test_general.find_and_launch_test(find_md_var_test, test__md_file_var)
#     test_general.find_and_launch_test(
#         find_include_file_test, test_include_files_to_md_file)

#     __launch_test()

    logging.info('Finished')
    # ------------------------------------


# -----------------------------------------------------------------------------
# Call main function if the script is main
# Exec only if this script is runned directly
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    __set_logging_system()
    __main()
