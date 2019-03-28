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
# test framework
#
###############################################################################

import logging
import sys
import os
import os.path
import shutil
import pytest

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
else:
    from . import common

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
# Folder to find the file for test
###############################################################################
@common.static(__folder_md_test__=None)
def get_test_folder():
    if get_test_folder.__folder_md_test__ is None:
        get_test_folder.__folder_md_test__ = common.check_folder(os.path.join(
            os.path.split(__get_this_filename())[0], "test-md"))

    return get_test_folder.__folder_md_test__

###############################################################################
# Compare two files
###############################################################################
def check_same_files(file1, file2):
    content1 = common.get_file_content(file1)
    content2 = common.get_file_content(file2)

    content1 = content1.replace('\r', '')
    content2 = content2.replace('\r', '')

    return (len(content1) == len(content2)) and (content1 == content2)

###############################################################################
# Function to test the transformation from a text
# From a function function_trans you can convert filename to filename_result
###############################################################################
def check_transform_text_function(filename, filename_result,
                                  transform_function):
    input_filename = common.check_is_file_and_correct_path(filename)
    result_filename = common.check_is_file_and_correct_path(filename_result)

    input1 = common.get_file_content(input_filename)
    result = common.get_file_content(result_filename)

    trans1 = transform_function(input1)
    trans2 = transform_function(trans1)

    trans1 = trans1.replace('\r', '')
    trans2 = trans2.replace('\r', '')
    result = result.replace('\r', '')

    assert trans1 == result
    # assert trans2 == result

###############################################################################
# Function to test the transformation from a text
# From a function function_trans you can convert filename to filename_result
###############################################################################
def check_trans_text_function_one(filename, filename_result,
                                  transform_function):
    input_filename = common.check_is_file_and_correct_path(filename)
    result_filename = common.check_is_file_and_correct_path(filename_result)

    input1 = common.get_file_content(input_filename)
    result = common.get_file_content(result_filename)

    trans1 = transform_function(input1)

    trans1 = trans1.replace('\r', '')
    result = result.replace('\r', '')

    assert trans1 == result

###############################################################################
# Function to test the transformation from a text
# From a function function_trans you can convert filename to filename_result
###############################################################################
def check_trans_file_inside_fun(filename,
                                filename_result,
                                transform_function,
                                filename_ext=".md"):
    input_filename = \
        common.check_is_file_and_correct_path(
            filename, filename_ext=filename_ext)
    result_filename = common.check_is_file_and_correct_path(filename_result)

    local_folder = os.path.split(input_filename)[0]
    random_name = '.{}'.format(hash(os.times()))
    filename_temp_ext = ".md"
    test_filename = common.set_correct_path(os.path.join(
        local_folder,
        common.get_flat_filename(random_name) + filename_temp_ext))

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename)

    shutil.copyfile(input_filename, test_filename)

    assert os.path.isfile(test_filename)

    transform_function(test_filename, backup_option=True,
                       filename_ext=filename_temp_ext)

    new_test_filename = "%s.%s-%03d%s" % (test_filename,
                                          common.get_today(), 0, ".bak")
    bak1 = common.set_correct_path(new_test_filename)

    assert os.path.isfile(bak1)

    assert check_same_files(bak1, input_filename)
    assert check_same_files(test_filename, result_filename)

    if os.path.isfile(test_filename):
        os.remove(test_filename)
    if os.path.isfile(bak1):
        os.remove(bak1)

    # with pytest.raises(Exception):
    #     common.check_is_file_and_correct_path(test_filename)

    # with pytest.raises(Exception):
    #     common.check_is_file_and_correct_path(bak1)

###############################################################################
# Function to test the transformation from a file
# From a function function_trans you can convert filename to filename_result
###############################################################################
def check_transform_file_function(filename,
                                  filename_result,
                                  transform_function,
                                  new_extension_for_result,
                                  filename_ext=".md"):
    input_filename = \
        common.check_is_file_and_correct_path(
            filename, filename_ext=filename_ext)
    common.check_is_file_and_correct_path(filename_result)

    local_folder = os.path.split(__get_this_filename())[0]
    random_name = '.{}'.format(hash(os.times()))
    filename_temp_ext = ".md"
    test_filename = common.set_correct_path(
        local_folder +
        common.get_flat_filename(random_name) + filename_temp_ext)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename)

    shutil.copyfile(input_filename, test_filename)

    assert os.path.isfile(test_filename)

    transform_function(test_filename, filename_ext=filename_temp_ext)
    test_filename_result = common.set_correct_path(
        os.path.splitext(test_filename)[0] +
        new_extension_for_result)

    assert os.path.isfile(test_filename_result)

    #  assert(check_same_files(test_filename_result,result_filename))

    if os.path.isfile(test_filename):
        os.remove(test_filename)
    if os.path.isfile(test_filename_result):
        os.remove(test_filename_result)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename_result)

###############################################################################
# Function to find all couple for test
###############################################################################
def find_test_file_couple(new_extension_for_result, filename_ext=".md",
                          folder_search=get_test_folder()):
    logging.info('Search test files for %s', new_extension_for_result)
    folder_search = common.check_folder(folder_search)
    len_end_of_filename = len(new_extension_for_result)

    result = []

    def __search_test_file__(filename):
        filename = common.check_is_file_and_correct_path(filename)
        result_filename = common.set_correct_path(os.path.splitext(filename)[
            0] + new_extension_for_result)

        # case when the filename is a result filename
        if (len(filename) > len_end_of_filename) \
                and (filename[-len_end_of_filename:] ==
                     new_extension_for_result):
            return

        if os.path.isfile(result_filename):
            result.append((filename, result_filename))

    common.apply_function_in_folder(
        folder_search, __search_test_file__, filename_ext=filename_ext)

    return result

###############################################################################
# Create result
###############################################################################
def create_result_transform_text(function_test, new_extension_for_result,
                                 filename_ext=".md",
                                 folder_search=get_test_folder(),
                                 force_creation=False):
    logging.info('Create result for %s', new_extension_for_result)
    folder_search = common.check_folder(folder_search)
    len_end_of_filename = len(new_extension_for_result)

    def __create_result__(filename):
        filename = common.check_is_file_and_correct_path(filename)
        result_filename = common.set_correct_path(os.path.splitext(filename)[
            0] + new_extension_for_result)

        if (len(filename) > len_end_of_filename) and \
                (filename[-len_end_of_filename:] ==
                 new_extension_for_result):
            return
        if (os.path.isfile(result_filename)) and (not force_creation):
            return

        logging.info('Create result for the file %s', filename)
        common.set_file_content(result_filename, function_test(
            common.get_file_content(filename)))

    common.apply_function_in_folder(
        folder_search, __create_result__, filename_ext=filename_ext)

###############################################################################
# Create result
###############################################################################
def create_result_transform_file(function_test,
                                 new_extension_for_result,
                                 filename_ext=".md",
                                 folder_search=get_test_folder(),
                                 force_creation=False):
    logging.info('Create result for %s', new_extension_for_result)
    folder_search = common.check_folder(folder_search)
    len_end_of_filename = len(new_extension_for_result)

    def __create_result__(filename):
        filename = common.check_is_file_and_correct_path(filename)
        result_filename = common.set_correct_path(os.path.splitext(filename)[
            0] + new_extension_for_result)

        if (len(filename) > len_end_of_filename) and \
                (filename[-len_end_of_filename:] == new_extension_for_result):
            return
        if (os.path.isfile(result_filename)) and (not force_creation):
            return

        logging.info('Create result for the file %s', filename)
        function_test(filename)
        common.check_is_file_and_correct_path(result_filename)

    common.apply_function_in_folder(
        folder_search, __create_result__, filename_ext=filename_ext)

###############################################################################
# Create result
###############################################################################
def create_result_trans_file_inside(function_test,
                                    new_extension_for_result,
                                    filename_ext=".md",
                                    folder_search=get_test_folder(),
                                    force_creation=False):
    logging.info('Create result for %s', new_extension_for_result)
    folder_search = common.check_folder(folder_search)
    len_end_of_filename = len(new_extension_for_result)

    def __create_result__(filename):
        filename = common.check_is_file_and_correct_path(filename)
        result_filename = common.set_correct_path(os.path.splitext(filename)[
            0] + new_extension_for_result)

        if (len(filename) > len_end_of_filename) and \
                (filename[-len_end_of_filename:] == new_extension_for_result):
            return
        if (os.path.isfile(result_filename)) and (not force_creation):
            return

        logging.info('Create result for the file %s', filename)
        shutil.copyfile(filename, result_filename)
        function_test(result_filename)
        new_result_filename = "%s.%s-" % (result_filename,
                                          common.get_today())
        if os.path.isfile(new_result_filename + "000.bak"):
            os.remove(new_result_filename + "000.bak")
        if os.path.isfile(new_result_filename + "001.bak"):
            os.remove(new_result_filename + "001.bak")

    common.apply_function_in_folder(
        folder_search, __create_result__, filename_ext=filename_ext)

###############################################################################
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return nothing
###############################################################################
def find_and_launch_test(fun_find, fun_test):
    files_found = fun_find()
    for files in files_found:
        print("file input:%s" % files[0])
        print("file output:%s" % files[1])
        fun_test(files[0], files[1])

###############################################################################
# rename some file reult
#
# @return nothing
###############################################################################
def rename_file_result(test_folder, extension, new_extension):
    logging.info('rename_file_result in %s from %s to %s',
                 test_folder, extension, new_extension)
    folder_search = common.check_folder(os.path.join(get_test_folder(),
                                                     test_folder))
    len_end_of_filename = len(extension)

    def __rename_test_file__(filename):
        filename = common.check_is_file_and_correct_path(filename)

        if (len(filename) > len_end_of_filename) \
                and (filename[-len_end_of_filename:] == extension):
            shutil.move(filename,
                        filename[:-len_end_of_filename] + new_extension)
            print(filename)
            return

    common.apply_function_in_folder(
        folder_search, __rename_test_file__, filename_ext=".md")

    return

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

    # rename_file_result("include_file", "_IncludeFile.md", "_include_file.md")

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
