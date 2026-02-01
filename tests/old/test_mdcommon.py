#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================


# -----------------------------------------------------------------------------
# test the file normalize
#
# -----------------------------------------------------------------------------

import logging
import sys
import os
import os.path
import pytest

import pymdtools.mdcommon as mdcommon
import test_general

# -----------------------------------------------------------------------------
def test_is_url():
    assert mdcommon.is_external_link("mailto:contact@guichet-partenaires.fr")
    assert mdcommon.is_external_link("http://www.google.fr/")

# -----------------------------------------------------------------------------
# find the file for test
# -----------------------------------------------------------------------------
def find_search_link_in_md_t_test():
    return test_general.find_test_file_couple(
        "_LinkInMdText.json",
        filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/search_links/")

# -----------------------------------------------------------------------------
# test the md_file_beautifier
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("filename, filename_result",
                         find_search_link_in_md_t_test())
def test_search_link_in_md_text(filename, filename_result):
    test_general.check_trans_text_function_one(
        filename, filename_result, mdcommon.search_link_in_md_text_json)

# -----------------------------------------------------------------------------
# Create result md_beautifier
# -----------------------------------------------------------------------------
def create_search_link_in_md_text(force_creation=False):
    test_general.create_result_transform_text(
        mdcommon.search_link_in_md_text_json,
        "_LinkInMdText.json",
        filename_ext=".md",
        folder_search=test_general.get_test_folder() + "/SearchLinks/",
        force_creation=force_creation)

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

    #  create_search_link_in_md_text(force_creation = True)

    # test_general.find_and_launch_test(
    #     find_search_link_in_md_t_test,
    #     test_search_link_in_md_text)

    test_is_url()

    logging.info('Finished')
    # ------------------------------------


# -----------------------------------------------------------------------------
# Call main function if the script is main
# Exec only if this script is runned directly
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    __set_logging_system()
    __main()
