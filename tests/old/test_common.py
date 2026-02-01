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
import codecs
import pytest

import pymdtools.common as common
import pymdtools.filetools as filetools
import pymdtools.mdcommon as mdcommon


def test_today():
    stamp = common.now_utc_timestamp()
    assert len(stamp) > 0
    dtime = common.parse_timestamp(stamp)
    assert stamp == str(dtime)


def test_search_link_in_md_text_1():
    # ------
    result = mdcommon.search_link_in_md_text(
        """[label]    (#metadonneelabel) cqsc qsc qs""")
    assert len(result) == 1
    assert result[0]["name"] == """label"""
    assert result[0]["url"] == """#metadonneelabel"""
    assert result[0]["title"] is None
    # ------
    result = mdcommon.search_link_in_md_text(
        """[Professeur de danse](www.guichet.fr)""")
    assert len(result) == 1
    assert result[0]["name"] == """Professeur de danse"""
    assert result[0]["url"] == """www.guichet.fr"""
    assert result[0]["title"] is None
    # ------
    result = mdcommon.search_link_in_md_text(
        """[Professeur de danse](www.guichet.fr "avec un title")""")
    assert len(result) == 1
    assert result[0]["name"] == """Professeur de danse"""
    assert result[0]["url"] == """www.guichet.fr"""
    assert result[0]["title"] == """avec un title"""
    # ------
    result = mdcommon.search_link_in_md_text("""[ref1][id1] reference-style
    link.
[id1]: http://example.com/id1  "un title sur
 plusieurs lignes" """)
    assert len(result) == 1
    assert result[0]["name"] == """ref1"""
    assert result[0]["url"] == """http://example.com/id1"""
    assert result[0]["title"] == """un title sur
 plusieurs lignes"""


# -----------------------------------------------------------------------------
# Test the link method
# -----------------------------------------------------------------------------
def test_replace_link_in_md_text():
    # ------
    new_link = {'name': 'scnge', 'url': 'www.guichet-entreprises.fr',
                'title': 'le site du guichet'}

    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec un """
        """title à remplacer également") la fin du texte""",
        new_link)
    assert result == """du texte et un lien : [scnge](""" \
        """www.guichet-entreprises.fr "le site """ \
        """du guichet") la fin du texte""" \

    list_new_link = [new_link]

    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec un """
        """title à remplacer également") la fin du texte""",
        list_new_link)
    assert result == """du texte et un lien : [scnge](""" \
        """www.guichet-entreprises.fr "le site """ \
        """du guichet") la fin du texte""" \

    new_link = {'name': 'scnge', 'url': 'www.guichet-entreprises.fr'}
    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec un """
        """title à remplacer également") la fin du texte""", new_link)
    assert result == """du texte et un lien : [scnge]""" \
        """(www.guichet-entreprises.fr) la fin du texte"""

    new_link = {'name_to_replace': 'scnge',
                'name': 'Guichet',
                'url': 'www.guichet-entreprises.fr',
                'title': 'le site du guichet'}
    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec """
        """un title à remplacer également") la fin du texte""",
        new_link)
    assert result == """du texte et un lien : [Guichet]""" \
        """(www.guichet-entreprises.fr "le site du guichet") la fin du texte"""

    new_link1 = {'name_to_replace': 'scnge',
                 'name': 'Guichet',
                 'url': 'www.guichet-entreprises.fr',
                 'title': 'le site du guichet'}
    new_link2 = {'name': 'google', 'url': 'www.google.fr'}
    list_link = [new_link1, new_link2]
    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec """
        """un title à remplacer également") le milleu du texte """
        """toujours du texte : [google](mon_2eme_lien_à_remplacer) """
        """la fin du texte""", list_link)
    assert result == """du texte et un lien : [Guichet]""" \
        """(www.guichet-entreprises.fr "le site du guichet") le milleu """ \
        """du texte toujours du texte : [google](www.google.fr) """ \
        """la fin du texte"""

    new_link = {'name': 'ref1',
                'url': 'www.guichet-entreprises.fr',
                'title': "un title"}
    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [ref1][id1] reference-style link. """
        """[id1]: http://example.com/id1
la fin du texte""", new_link)

    assert result == """du texte et un lien : [ref1][id1] """ \
        """reference-style link. [id1]: www.guichet-entreprises.fr "un title"
la fin du texte"""

    new_link = {'name_to_replace': 'scnge',
                'name': 'le guichet',
                'url': 'www.guichet-entreprises.fr', 'title': "un title"}
    result = mdcommon.update_links_in_md_text(
        """du texte et un lien : [scnge][id1] reference-style link.
[id1]: mon_lien_à_remplacer
la fin du texte""", new_link)
    assert result == """du texte et un lien : [le guichet][id1] """ \
        """reference-style link.
[id1]: www.guichet-entreprises.fr "un title"
la fin du texte"""

    old_link2 = {'name': 'le gip guichet?',
                 'url': 'www.gip-entreprises.fr',
                 'title': "le GIP"}
    new_link2 = {'name': 'le guichet nouveau et arrivé',
                 'url': 'www.guichet-entreprises.fr',
                 'title': "le site du guichet"}
    old_link1 = {'name': 'au autre lien',
                 'url': 'www.gle.fr'}
    new_link1 = {'name': 'GOOGLE!',
                 'url': 'www.google.fr'}
    result = mdcommon.update_links_from_old_link(
        """du texte et un lien : [le gip guichet?]"""
        """(www.gip-entreprises.fr "le """
        """GIP") la fin du texte[au autre lien](www.gle.fr)""",
        [(old_link1, new_link1), (old_link2, new_link2)])
    assert result == """du texte et un lien : """ \
        """[le guichet nouveau et arrivé](""" \
        """www.guichet-entreprises.fr "le site """ \
        """du guichet") la fin du texte[GOOGLE!](www.google.fr)""" \


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_normpath():
    # current_dir = os.path.split(__get_this_filename())[0]
    # root = os.path.abspath(os.path.join(current_dir, "./../../"))
    # assert normpath(current_dir + "/././../") == root + "\\python"
    # assert normpath(current_dir + "/././../../") == root
    assert common.normpath("C:/") == "C:\\"


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_ensure_folder():
    current_folder = os.path.abspath("./")
    assert common.ensure_folder("./") == current_folder

    random_name = '.{}'.format(hash(os.times()))
    test_foldername = "./" + random_name

    with pytest.raises(RuntimeError):
        common.check_folder(test_foldername)
    assert common.ensure_folder(
        test_foldername) == os.path.abspath(test_foldername)
    assert common.check_folder(
        test_foldername) == os.path.abspath(test_foldername)

    os.rmdir(test_foldername)
    with pytest.raises(RuntimeError):
        common.check_folder(test_foldername)

    with pytest.raises(RuntimeError):
        common.ensure_folder(__file__)


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_check_is_file_and_correct():
    random_name = '.{}'.format(hash(os.times()))
    test_filename = "./" + random_name + ".txt"

    with pytest.raises(RuntimeError):
        common.check_folder(test_filename)

    assert common.check_file(
        __get_this_filename()) == os.path.abspath(__get_this_filename())


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_path_depth():
    assert common.path_depth("A/B") == 1
    assert common.path_depth("A/////B") == 1
    assert common.path_depth("A\\\\B") == 1
    assert common.path_depth("/A/B") == 1
    assert common.path_depth("//A/////B") == 1
    assert common.path_depth("//A\\\\B") == 1


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_create_backup():

    random_name = '.{}'.format(hash(os.times()))
    test_filename = "./" + random_name + ".txt"

    with pytest.raises(Exception):
        common.check_file(test_filename)

    file_content = "Test"

    # create the file
    output_file = codecs.open(test_filename, "w", encoding="utf-8")
    output_file.write(file_content)
    output_file.close()

    assert(common.check_file(
        test_filename) == os.path.abspath(test_filename))

    today = common.today_utc()
    bak1 = os.path.abspath("./" + test_filename + "." + today + "-000.bak")
    bak2 = os.path.abspath("./" + test_filename + "." + today + "-001.bak")

    if os.path.isfile(bak1):
        os.remove(bak1)
    if os.path.isfile(bak2):
        os.remove(bak2)

    with pytest.raises(Exception):
        common.check_file(bak1)
    with pytest.raises(Exception):
        common.check_file(bak2)

    assert common.create_backup(test_filename) == bak1
    assert common.create_backup(test_filename) == bak2
    assert common.check_file(bak1) == os.path.abspath(bak1)
    assert common.check_file(bak2) == os.path.abspath(bak2)

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
        common.check_file(bak1)
    with pytest.raises(Exception):
        common.check_file(bak2)

    if os.path.isfile(test_filename):
        os.remove(test_filename)

    with pytest.raises(Exception):
        common.check_file(test_filename)


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_get_file_content():

    random_name = '.{}'.format(hash(os.times()))
    test_filename_1 = "./" + random_name + "1.txt"
    test_filename_2 = "./" + random_name + "2.txt"

    with pytest.raises(Exception):
        common.check_file(test_filename_1)
    with pytest.raises(Exception):
        common.check_file(test_filename_2)

    file_content = "Test"

    # create the file
    output_file = codecs.open(test_filename_1, "w", encoding="utf-8")
    output_file.write(file_content)
    output_file.close()
    # create the file
    output_file = codecs.open(test_filename_2, "w", encoding="utf-8")
    output_file.write(u'\ufeff' + file_content)
    output_file.close()

    assert common.check_file(
        test_filename_1) == os.path.abspath(test_filename_1)
    assert common.check_file(
        test_filename_2) == os.path.abspath(test_filename_2)

    assert common.get_file_content(test_filename_1) == file_content
    assert common.get_file_content(test_filename_2) == file_content

    if os.path.isfile(test_filename_1):
        os.remove(test_filename_1)
    if os.path.isfile(test_filename_2):
        os.remove(test_filename_2)

    with pytest.raises(Exception):
        common.check_file(test_filename_2)
    with pytest.raises(Exception):
        common.check_file(test_filename_2)


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_set_file_content():
    random_name = '.{}'.format(hash(os.times()))
    test_filename1 = "./" + random_name + "1.txt"
    test_filename2 = "./" + random_name + "2.txt"

    with pytest.raises(Exception):
        common.check_file(test_filename1)
    with pytest.raises(Exception):
        common.check_file(test_filename2)

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
        common.check_file(test_filename2)
    with pytest.raises(Exception):
        common.check_file(test_filename2)


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_get_valid_filename():
    assert common.get_valid_filename("common.py") == "common.py"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!èè````'':;,") == "_.__;,§_;,MLjkML;,!èè````''_;,"


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_get_flat_filename():
    assert common.get_valid_filename("common.py") == "common.py"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!:;,") == "_.__;,§_;,MLjkML;,!_;,"
    assert common.get_valid_filename(
        "/.?:;,§/;,MLjkML;,!èè````'':;,") == "_.__;,§_;,MLjkML;,!èè````''_;,"


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_make_temp_dir():
    temp1 = common.make_temp_dir()
    temp2 = common.make_temp_dir()

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


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_today_utc():
    assert len(common.today_utc()) == 10
    assert common.today_utc()[4] == "-"
    assert common.today_utc()[7] == "-"


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
def test_search_for_file():
    start_point = os.path.split(__get_this_filename())[0]
    assert(common.search_for_file("common.py", ["./", start_point],
                                  ["./", "python", "pymdtools"]) is not None)


# -----------------------------------------------------------------------------
def test_filecontent():
    test_folder = os.path.join(os.path.split(
        __get_this_filename())[0], 'test-md')

    test1 = filetools.FileContent()

    test1.full_filename = "toto.test"
    test1.filename = "toto.test"
    test1.content = r"lkhà_çèé-_è'è-('è-('"
    test1.filename_path = test_folder

    print(test1)

    md_obj = filetools.FileContent(
        filename=os.path.join(test_folder, "test-0.md"))
    print(md_obj)


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


# -------------------------------------------------------------------------###
# Main script call only if this script is runned directly
# -----------------------------------------------------------------------------
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

    test_today()

    logging.info('Finished')
    # ------------------------------------


# -----------------------------------------------------------------------------
# Call main function if the script is main
# Exec only if this script is runned directly
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    __set_logging_system()
    __main()
