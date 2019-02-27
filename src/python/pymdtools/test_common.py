#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# @copyright Copyright (C) Guichet Entreprises - All Rights Reserved
# 	All Rights Reserved.
# 	Unauthorized copying of this file, via any medium is strictly prohibited
# 	Dissemination of this information or reproduction of this material
# 	is strictly forbidden unless prior written permission is obtained
# 	from Guichet Entreprises.
###############################################################################

###############################################################################
# test the file normalize
#
###############################################################################

import logging
import sys
import os
import os.path
import codecs
import pytest

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
else:
    from . import common

###############################################################################
#
###############################################################################
def test_set_correct_path():
    # current_dir = os.path.split(__get_this_filename())[0]
    # root = os.path.abspath(os.path.join(current_dir, "./../../"))
    # assert set_correct_path(current_dir + "/././../") == root + "\\python"
    # assert set_correct_path(current_dir + "/././../../") == root
    assert common.set_correct_path("C:/") == "C:\\"


###############################################################################
#
###############################################################################
def test_check_folder():
    # current_dir = os.path.split(__get_this_filename())[0]
    # root = os.path.abspath(os.path.join(current_dir, "./../../"))
    # assert check_folder(current_dir + "/././../") == root + "\\python"
    # assert check_folder(current_dir + "/././../../") == root
    assert common.check_folder("C:/") == "C:\\"

    with pytest.raises(RuntimeError):
        common.check_folder(__file__)
    with pytest.raises(RuntimeError):
        common.check_folder("AA:/")

###############################################################################
#
###############################################################################
def test_check_create_folder():
    current_folder = os.path.abspath("./")
    assert common.check_create_folder("./") == current_folder

    random_name = '.{}'.format(hash(os.times()))
    test_foldername = "./" + random_name

    with pytest.raises(RuntimeError):
        common.check_folder(test_foldername)
    assert common.check_create_folder(
        test_foldername) == os.path.abspath(test_foldername)
    assert common.check_folder(
        test_foldername) == os.path.abspath(test_foldername)

    os.rmdir(test_foldername)
    with pytest.raises(RuntimeError):
        common.check_folder(test_foldername)

    with pytest.raises(RuntimeError):
        common.check_create_folder(__file__)


###############################################################################
#
###############################################################################
def test_check_is_file_and_correct():
    random_name = '.{}'.format(hash(os.times()))
    test_filename = "./" + random_name + ".txt"

    with pytest.raises(RuntimeError):
        common.check_folder(test_filename)

    assert common.check_is_file_and_correct_path(
        __get_this_filename()) == os.path.abspath(__get_this_filename())


###############################################################################
#
###############################################################################
def test_number_of_subfolder():
    assert common.number_of_subfolder("A/B") == 1
    assert common.number_of_subfolder("A/////B") == 1
    assert common.number_of_subfolder("A\\\\B") == 1
    assert common.number_of_subfolder("/A/B") == 1
    assert common.number_of_subfolder("//A/////B") == 1
    assert common.number_of_subfolder("//A\\\\B") == 1


###############################################################################
#
###############################################################################
def test_create_backup():

    random_name = '.{}'.format(hash(os.times()))
    test_filename = "./" + random_name + ".txt"

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename)

    file_content = "Test"

    # create the file
    output_file = codecs.open(test_filename, "w", encoding="utf-8")
    output_file.write(file_content)
    output_file.close()

    assert(common.check_is_file_and_correct_path(
        test_filename) == os.path.abspath(test_filename))

    today = common.get_today()
    bak1 = os.path.abspath("./" + test_filename + "." + today + "-000.bak")
    bak2 = os.path.abspath("./" + test_filename + "." + today + "-001.bak")

    if os.path.isfile(bak1):
        os.remove(bak1)
    if os.path.isfile(bak2):
        os.remove(bak2)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(bak1)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(bak2)

    assert common.create_backup(test_filename) == bak1
    assert common.create_backup(test_filename) == bak2
    assert common.check_is_file_and_correct_path(bak1) == os.path.abspath(bak1)
    assert common.check_is_file_and_correct_path(bak2) == os.path.abspath(bak2)

    input_file = codecs.open(bak1, mode="r", encoding="utf-8")
    content_bak1 = input_file.read()
    input_file.close()

    input_file = codecs.open(bak2, mode="r", encoding="utf-8")
    content_bak2 = input_file.read()
    input_file.close()

    assert file_content == content_bak1
    assert file_content == content_bak2

    if os.path.isfile(bak1):
        os.remove(bak1)
    if os.path.isfile(bak2):
        os.remove(bak2)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(bak1)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(bak2)

    if os.path.isfile(test_filename):
        os.remove(test_filename)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename)


###############################################################################
#
###############################################################################
def test_get_file_content():

    random_name = '.{}'.format(hash(os.times()))
    test_filename_1 = "./" + random_name + "1.txt"
    test_filename_2 = "./" + random_name + "2.txt"

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename_1)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename_2)

    file_content = "Test"

    # create the file
    output_file = codecs.open(test_filename_1, "w", encoding="utf-8")
    output_file.write(file_content)
    output_file.close()
    # create the file
    output_file = codecs.open(test_filename_2, "w", encoding="utf-8")
    output_file.write(u'\ufeff' + file_content)
    output_file.close()

    assert common.check_is_file_and_correct_path(
        test_filename_1) == os.path.abspath(test_filename_1)
    assert common.check_is_file_and_correct_path(
        test_filename_2) == os.path.abspath(test_filename_2)

    assert common.get_file_content(test_filename_1) == file_content
    assert common.get_file_content(test_filename_2) == file_content

    if os.path.isfile(test_filename_1):
        os.remove(test_filename_1)
    if os.path.isfile(test_filename_2):
        os.remove(test_filename_2)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename_2)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename_2)


###############################################################################
#
###############################################################################
def test_set_file_content():
    random_name = '.{}'.format(hash(os.times()))
    test_filename1 = "./" + random_name + "1.txt"
    test_filename2 = "./" + random_name + "2.txt"

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename1)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename2)

    file_content = "Test"

    # create the file
    output_file = codecs.open(test_filename1, "w", encoding="utf-8")
    output_file.write(file_content)
    output_file.close()

    assert common.set_file_content(
        test_filename1, file_content) == os.path.abspath(test_filename1)
    assert common.set_file_content(
        test_filename2, file_content) == os.path.abspath(test_filename2)

    input_file = codecs.open(test_filename1, mode="r", encoding="utf-8")
    content_file1 = input_file.read()
    input_file.close()

    input_file = codecs.open(test_filename2, mode="r", encoding="utf-8")
    content_file2 = input_file.read()
    input_file.close()

    assert content_file1 == u'\ufeff' + file_content
    assert content_file2 == u'\ufeff' + file_content

    if os.path.isfile(test_filename1):
        os.remove(test_filename1)
    if os.path.isfile(test_filename2):
        os.remove(test_filename2)

    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename2)
    with pytest.raises(Exception):
        common.check_is_file_and_correct_path(test_filename2)


###############################################################################
#
###############################################################################
def test_get_valid_filename():
    assert common.get_valid_filename("common.py") == "common.py"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!èè````'':;,") == "_.__;,§_;,MLjkML;,!èè````''_;,"


###############################################################################
#
###############################################################################
def test_get_flat_filename():
    assert common.get_valid_filename("common.py") == "common.py"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!èè````'':;,") == "_.__;,§_;,MLjkML;,!èè````''_;,"


###############################################################################
#
###############################################################################
def test_get_new_temp_dir():
    temp1 = common.get_new_temp_dir()
    temp2 = common.get_new_temp_dir()

    assert temp1 != temp2
    assert common.check_folder(temp1) == os.path.abspath(temp1)
    assert common.check_folder(temp2) == os.path.abspath(temp2)

    assert len(os.listdir(temp1)) == 0
    assert len(os.listdir(temp2)) == 0

    if os.path.isdir(temp1):
        os.rmdir(temp1)
    if os.path.isdir(temp2):
        os.rmdir(temp2)

    with pytest.raises(RuntimeError):
        common.check_folder(temp1)
    with pytest.raises(RuntimeError):
        common.check_folder(temp2)


###############################################################################
#
###############################################################################
def test_get_today():
    assert len(common.get_today()) == 10
    assert common.get_today()[4] == "-"
    assert common.get_today()[7] == "-"


###############################################################################
#
###############################################################################
def test_search_for_file():
    start_point = os.path.split(__get_this_filename())[0]
    assert(common.search_for_file("common.py", ["./", start_point],
                                  ["./", "python"]) is not None)


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
    pytest.main(__get_this_filename())


##############################################################################
# Main script call only if this script is runned directly
###############################################################################
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

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
