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

import pymdtools.translate as translate

# -----------------------------------------------------------------------------
def test_eu_lang():
    assert len(translate.eu_lang_list()) == 26


# -----------------------------------------------------------------------------
def test_hello():
    assert translate.translate_txt(
        "bonjour", src="fr", dest="en").lower() == "hello"


# -----------------------------------------------------------------------------
def __get_this_folder():
    """ Return the folder of this script with frozen compatibility
    @return the folder of THIS script.
    """
    return os.path.split(os.path.abspath(os.path.realpath(
        __get_this_filename())))[0]


# -----------------------------------------------------------------------------
def __get_this_filename():
    """ Return the filename of this script with frozen compatibility
    @return the filename of THIS script.
    """
    return __file__ if not getattr(sys, 'frozen', False) else sys.executable


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

    test_eu_lang()
    test_hello()

    # import goslate
    # gs = goslate.Goslate()

    # print(gs.translate('hello world', 'de'))

    logging.info('Finished')
    # ------------------------------------


# -----------------------------------------------------------------------------
# Call main function if the script is main
# Exec only if this script is runned directly
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    __set_logging_system()
    __main()
