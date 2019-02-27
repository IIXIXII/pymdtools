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
import pytest

if (__package__ in [None, '']) and ('.' not in __name__):
    import mdtopdf
    import test_general
else:
    from . import mdtopdf
    from . import test_general

###############################################################################
# find the file for test
###############################################################################
def find_convert_to_pdf_test():
    return test_general.find_test_file_couple(
        ".pdf", filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/convert_to_pdf/")

###############################################################################
# Create result ConvertToPdf
###############################################################################
def create_result_convert_to_pdf(force_creation=False):
    test_general.create_result_transform_file(
        mdtopdf.convert_md_to_pdf,
        ".pdf",
        folder_search=test_general.get_test_folder() + "/convert_to_pdf/",
        force_creation=force_creation)

###############################################################################
# test the md_file_beautifier
###############################################################################
@pytest.mark.parametrize("filename, filename_result",
                         find_convert_to_pdf_test())
def test_convert_to_pdf(filename, filename_result):
    test_general.check_transform_file_function(
        filename,
        filename_result,
        mdtopdf.convert_md_to_pdf, ".pdf")

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

    #  create_result_convert_to_pdf(force_creation = True)

    # print(find_convert_to_pdf_test())
    test_general.find_and_launch_test(
        find_convert_to_pdf_test,
        test_convert_to_pdf)

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
