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
# @package mdtools
# Markdown Tools develops for Guichet Entreprises
#
###############################################################################
import logging
import sys
import os
import re

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
else:
    from . import common


###############################################################################
# re expression used for instruction
###############################################################################
__comment_re__ = \
    r"<!--(?P<comment>[\s\S]*?)-->"
__begin_ref_re__ = \
    r"<!--\s+begin-ref\((?P<name>[a-zA-Z0-9_-]+)\)\s+-->"
__end_ref_re__ = \
    r"<!--\s+end-ref\s+-->"
__begin_include_re__ = \
    r"<!--\s+begin-include\((?P<name>[a-zA-Z0-9_-]+)\)\s+-->"
__end_include_re__ = \
    r"<!--\s+end-include\s+-->"
__var_re__ = \
    r"""<!--\s+var\((?P<name>[a-zA-Z0-9:_-]+)\)\s*""" \
    r"""=\s*(?P<quote>['\"])(?P<string>.*?)(?<!\\)(?P=quote)\s+-->"""
__begin_var_re__ = \
    r"<!--\s+begin-var\((?P<name>[a-zA-Z0-9_-]+)\)\s+-->"
__end_var_re__ = \
    r"<!--\s+end-var\s+-->"
__include_file_re__ = \
    r"<!--\s+include-file\((?P<name>[\.a-zA-Z0-9_-]+)\)(?P<content>[\s\S]*?)-->"

###############################################################################
# strip XML comment.
# Remove all xml comment from a text
#
# @param text the markdown text
# @return the text without xml comment
###############################################################################
def strip_xml_comment(text):
    result = re.sub(__comment_re__, "", text)

    return result

###############################################################################
# Find refs in a markdown text
#
# @param text the markdown text
# @param previous_refs the previous refs dict for a recursive call
# @return the dict with the refs found key-> value
###############################################################################
def get_refs_from_md_text(text, previous_refs=None):
    result = {}
    if previous_refs is not None:
        result = previous_refs

    # search begin
    match_begin = re.search(__begin_ref_re__, text)

    # finish if no match
    if not match_begin:
        return result

    # There is a match
    key = match_begin.group('name')
    logging.debug('Find the key reference %s', key)

    if key in result:
        logging.error(
            'Find a new begin-ref(%s), there is a double reference', key)
        raise Exception(
            'Find a new begin-ref(%s), there is a double reference' % (key))

    last_part = text[match_begin.end(0):]

    # match end
    match_end = re.search(__end_ref_re__, last_part)

    if not match_end:
        logging.error(
            'Find a begin-ref(%s) and not finding the end-ref', key)
        raise Exception(
            'Find a begin-ref(%s) and not finding the end-ref' % (key))

    # remove  XML comment and save
    result[key] = strip_xml_comment(last_part[0:match_end.start(0)])

    new_text = last_part[match_end.end(0):]

    result = get_refs_from_md_text(new_text, result)

    return result


###############################################################################
# Find refs in a markdown file
#
# @param filename the markdown file
# @param filename_ext the extension of the markdown file
# @param previous_refs the previous refs dict for a recursive call
# @return the dict with the refs found key-> value
###############################################################################
def get_refs_from_md_file(filename, filename_ext=".md", previous_refs=None):
    logging.debug('Find refs in the MD the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename, encoding="UNKNOWN")

    # Analyze
    result = get_refs_from_md_text(text, previous_refs=previous_refs)

    return result

###############################################################################
# Find refs in markdown file in a folder and subfolder.
# Depth parameter :
# 		- -1-> every subfolder.
# 		-  0-> the current level
# 		-  n-> (with n>0) n subfolder level of the folder
#
# @param folder the folder pathname
# @param filename_ext the extension of the markdown file
# @param previous_refs the previous refs dict for a recursive call
# @param depth the depth to search for.
# @return the dict with the refs found key-> value
###############################################################################
def get_refs_from_md_directory(folder, filename_ext=".md",
                               previous_refs=None, depth=-1):
    logging.debug('Find refs in the MD in the folder "%s"', folder)
    folder = common.check_folder(folder)

    result = {}
    if previous_refs is not None:
        result = previous_refs

    md_files = [os.path.join(folder, f) for f in os.listdir(folder)
                if (os.path.isfile(os.path.join(folder, f)) and
                    (os.path.splitext(f)[1] == filename_ext))]

    for filename in md_files:
        result = get_refs_from_md_file(filename, filename_ext, result)

    logging.debug('End refs in the MD the folder "%s"', folder)

    if depth == 0:
        return result

    folders = [os.path.join(folder, f) for f in os.listdir(folder)
               if os.path.isdir(os.path.join(folder, f))]

    for dirname in folders:
        result = get_refs_from_md_directory(
            dirname, filename_ext=".md", previous_refs=result, depth=depth - 1)

    return result

###############################################################################
# Find refs around a markdown file.
# Depth down parameter :
# 		- -1-> every subfolder.
# 		-  0-> the current level
# 		-  n-> (with n>0) n subfolder level of the folder
#
# @param filename the name of the markdown file
# @param filename_ext the extension of the markdown file
# @param previous_refs the previous refs dict for a recursive call
# @param depth_up the number of upper folder to search for.
# @param depth_down the depth to search for.
# @return the dict with the refs found key-> value
###############################################################################
def get_refs_around_md_file(filename, filename_ext=".md",
                            previous_refs=None, depth_up=1, depth_down=-1):
    logging.debug('Discover refs around the file "%s"', filename)
    filename = common.set_correct_path(filename)

    current_dir = os.path.abspath(os.path.dirname(filename))

    while depth_up > 0:
        new_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        if new_dir == current_dir:
            depth_up = 0
        else:
            depth_up = depth_up - 1
            if depth_down > 0:
                depth_down = depth_down + 1
        current_dir = new_dir

    result = get_refs_from_md_directory(current_dir,
                                        filename_ext,
                                        previous_refs=previous_refs,
                                        depth=depth_down)

    return result

###############################################################################
# Include reference to the markdown text
# \warning All the reference must be defined
#
# @param text the markdown text
# @param refs_include the dict with all the references
# @param begin_include_re the regex to match the begin
# @param end_include_re the regex to match the end
# @param error_if_no_key boolean :
#                        throw Exception if the key is not found
# @return the markdown text with the include
###############################################################################
def include_refs_to_md_text(text, refs_include,
                            begin_include_re=__begin_include_re__,
                            end_include_re=__end_include_re__,
                            error_if_no_key=True):

    # search begin
    match_begin = re.search(begin_include_re, text)

    # finish if no match
    if not match_begin:
        return text

    key = match_begin.group('name')
    logging.debug('Find the key reference %s', key)

    if key not in refs_include:
        if error_if_no_key:
            logging.error(
                'Find a begin-include(%s) and '
                'not finding the reference', key)
            raise Exception(
                'Find a begin-include(%s) and '
                'not finding the reference' % (key))
        return text[0:match_begin.end(0)] + \
            include_refs_to_md_text(text[match_begin.end(0):],
                                    refs_include,
                                    begin_include_re=begin_include_re,
                                    end_include_re=end_include_re,
                                    error_if_no_key=error_if_no_key)

    result = text[0:match_begin.end(0)] + refs_include[key]

    last_part = text[match_begin.end(0):]
    match_end = re.search(end_include_re, last_part)

    if not match_end:
        msg = 'Find a begin-include(%s) and not finding the end-include' % key
        logging.error(msg)
        raise Exception(msg)

    result = result + last_part[match_end.start(0):match_end.end(0)]
    result = result + \
        include_refs_to_md_text(last_part[match_end.end(0):],
                                refs_include,
                                begin_include_re=begin_include_re,
                                end_include_re=end_include_re,
                                error_if_no_key=error_if_no_key)

    return result

###############################################################################
# Include reference to the markdown text
# \warning All the reference must be defined
#
# @param filename The name and path of the file to work with. This file is
#                 supposed to be a markdown file.
# @param refs the dict with all the references
# @param backup_option This parameter is set to true by default.
#                       If the backup option is set,
#                       then a file named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @param begin_include_re the regex to match the begin
# @param end_include_re the regex to match the end
# @param error_if_no_key boolean : throw Exception
#                                         if the key is not found
# @return the filename normalized
###############################################################################
def include_refs_to_md_file(filename,
                            refs,
                            backup_option=True,
                            filename_ext=".md",
                            begin_include_re=__begin_include_re__,
                            end_include_re=__end_include_re__,
                            error_if_no_key=True):

    logging.debug('Include refs to the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename)

    # Create Backup
    if backup_option:
        common.create_backup(filename)

    # Change inside
    text = include_refs_to_md_text(text, refs,
                                   begin_include_re=begin_include_re,
                                   end_include_re=end_include_re,
                                   error_if_no_key=error_if_no_key)

    # Save the file
    os.remove(filename)
    common.set_file_content(filename, text, encoding="utf-8")
    return filename

###############################################################################
# Search and include reference to the markdown text
# \warning All the reference must be defined
#
# Depth down parameter :
# 		- -1-> every subfolder.
# 		-  0-> the current level
# 		-  n-> (with n>0) n subfolder level of the folder
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param backup_option This parameter is set to true by default.
#                       If the backup option is set, then a file
#                          named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @param depth_up the number of upper folder to search for.
# @param depth_down the depth to search for.
# @return the filename normalized
###############################################################################
def search_include_refs_to_md_file(filename,
                                   backup_option=True,
                                   filename_ext=".md",
                                   depth_up=1, depth_down=-1):
    """Search and include reference to the markdown text
        @warning All the reference must be defined

        Depth down parameter :
                        - -1-> every subfolder.
                        -  0-> the current level
                        -  n-> (with n>0) n subfolder level of the folder

        @type filename: string
        @param filename The name and path of the file to work with.
                        This file is supposed to be a markdown file.

        @type backup_option: boolean
        @param backup_option This parameter is set to true by default.
                                If the backup option is set, then a file
                                named filename.bak will be created.

        @type filename_ext: string
        @param filename_ext This parameter the markdown extension
                            for the filename.

        @type depth_up: integer
        @param depth_up the number of upper folder to search for.

        @type depth_down: integer
        @param depth_down the depth to search for.

    """
    refs = get_refs_around_md_file(filename, filename_ext=filename_ext,
                                   depth_up=depth_up, depth_down=depth_down)
    return include_refs_to_md_file(filename, refs,
                                   backup_option=backup_option,
                                   filename_ext=filename_ext)

###############################################################################
# Find vars in a markdown test
#
# @param text the markdown text
# @param previous_vars the previous vars dict for a recursive call
# @return the dict with the refs found key-> value
###############################################################################
def get_vars_from_md_text(text, previous_vars=None):
    # search begin
    match_var = re.search(__var_re__, text)

    result = {}
    if previous_vars is not None:
        result = previous_vars

    # finish if no match
    if not match_var:
        return result

    # There is a match
    key = match_var.group('name')
    logging.debug('Find the variable %s', key)
    value = match_var.group('string')
    logging.debug('Find the value %s', value)

    if key in result:
        logging.error(
            'Find a new var(%s), there is a double reference', key)
        raise Exception(
            'Find a new var(%s), there is a double reference' % (key))

    result[key] = value

    new_text = text[match_var.end(0):]

    result = get_vars_from_md_text(new_text, result)

    return result

def test_get_vars_from_md_text():
    assert(get_vars_from_md_text('<!-- var(essai) = "tes\\t" -->')
           ['essai'] == "tes\\t")
    assert(get_vars_from_md_text('<!-- var(essai) = "tes\"t" -->')
           ['essai'] == "tes\"t")
    assert(get_vars_from_md_text(
        '<!-- var(essai)="test" -->'
        '<!-- var(essai2)="test" -->')['essai'] == "test")

###############################################################################
# set a var in the markdown text
#
# @param text the markdown text
# @param var_name the variable name
# @param value the value to set
# @return the dict with the refs found key-> value
###############################################################################
def set_var_to_md_text(text, var_name, value):

    result = ""
    current_text = text
    var_is_set = False
    var_text = '<!-- var(%s)="%s" -->' % (var_name, value)

    # search the var
    match_var = re.search(__var_re__, current_text)

    while match_var is not None:
        key = match_var.group('name')
        logging.debug('Find the variable %s', key)
        if key == var_name:
            result += current_text[0:match_var.start(0)]
            result += var_text
            var_is_set = True
        else:
            result += current_text[0:match_var.end(0)]

        current_text = current_text[match_var.end(0):]
        match_var = re.search(__var_re__, current_text)

    if not var_is_set:
        if len(result) > 0:
            result += '\n'
        result += var_text
        if len(current_text) > 0 and current_text[0] != '\n':
            result += '\n\n'

    result += current_text
    return result

def test_set_var_to_md_text():
    assert(set_var_to_md_text('<!-- var(essai) = "tes\\t" -->text',
                              "test",
                              "good") == '<!-- var(essai) = "tes\\t" -->\n'
           '<!-- var(test)="good" -->\n\ntext')
    assert(set_var_to_md_text('<!-- var(essai) = "tes\\t" -->text',
                              "essai", "good") ==
           '<!-- var(essai)="good" -->text')

###############################################################################
# del a var in the markdown text
#
# @param text the markdown text
# @param var_name the variable name
# @return the dict with the refs found key-> value
###############################################################################
def del_var_to_md_text(text, var_name):

    result = ""
    current_text = text

    # search the var
    match_var = re.search(__var_re__, current_text)

    while match_var is not None:
        key = match_var.group('name')
        logging.debug('Find the variable %s', key)
        if key == var_name:
            result += current_text[0:match_var.start(0)]
        else:
            result += current_text[0:match_var.end(0)]

        current_text = current_text[match_var.end(0):]
        match_var = re.search(__var_re__, current_text)

    result += current_text
    return result

def test_del_var_to_md_text():
    assert(del_var_to_md_text('<!-- var(essai) = "tes\\t" -->',
                              "test") ==
           '<!-- var(essai) = "tes\\t" -->')
    assert(del_var_to_md_text('x<!-- var(essai) = "tes\\t" -->x',
                              "essai") == 'xx')

###############################################################################
# Get title in md text
# @param text the markdown text
# @return the the title
###############################################################################
def get_title_from_md_text(text):
    local_text = strip_xml_comment(text)
    title_re = r"(\s)*(?P<title>[^\n\r]+)(\n|\r\n)[=]+(\s)*"
    match = re.search(title_re, local_text)
    if not match:
        title2_re = r"(\s)*#(\s)*(?P<title>[^\n\r]+)(\n|\r\n)"
        match = re.search(title2_re, local_text)
        if not match:
            return None

    return match.group('title')

def test_get_title_from_md_text():
    assert get_title_from_md_text("""
DQP002 - ADMINISTRATEUR JUDICIAIRE
==================================

1°. Définition de l'activité
-----------------

L'administrateur judiciaire est un professionnel
""") == "DQP002 - ADMINISTRATEUR JUDICIAIRE"

    assert get_title_from_md_text("""
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

###############################################################################
# Set title in md text
# @param text the markdown text
# @param new_title the new title
# @return the title
###############################################################################
def set_title_in_md_text(text, new_title):
    old_title = get_title_from_md_text(text)
    new_second_line = "=" * len(new_title)

    result = text.replace(old_title, new_title + '\n' + new_second_line)

    line_re = new_second_line + '(\n|\r\n)' + "(=+)(\n|\r\n)"
    result = re.sub(line_re, new_second_line + '\n', result)

    return result

def test_set_title_in_md_text():
    result = """
    DQP015 - Anatomie et cytologie
==============================
===========================

1------------------"""
    new_second_line = "=============================="
    line_re = new_second_line + '(\n|\r\n)' + "(=+)(\n|\r\n)"
    result = re.sub(line_re, new_second_line + '\n', result)
    result = set_title_in_md_text(result, "yitruytr")
    # print(repr(result))

###############################################################################
# Find vars in a markdown file
#
# @param filename the markdown file
# @param filename_ext the extension of the markdown file
# @param previous_vars the previous refs dict for a recursive call
# @return the dict with the vars found: key-> value
###############################################################################
def get_vars_from_md_file(filename, filename_ext=".md", previous_vars=None):
    logging.debug('Find vars in the MD the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename)

    # Analyze
    result = get_vars_from_md_text(text, previous_vars=previous_vars)

    return result

###############################################################################
# Include vars to the markdown text
# \warning All the reference must be defined
#
# @param text the markdown text
# @param vars_include the dict with all the references
# @param begin_var_re the regex to match the begin
# @param end_var_re the regex to match the end
# @param error_if_var_not_found boolean : throw Exception
#                                         if the var is not found
# @return the markdown text with the include
###############################################################################
def include_vars_to_md_text(text, vars_include,
                            begin_var_re=__begin_var_re__,
                            end_var_re=__end_var_re__,
                            error_if_var_not_found=True):
    return include_refs_to_md_text(text, vars_include,
                                   begin_include_re=begin_var_re,
                                   end_include_re=end_var_re,
                                   error_if_no_key=error_if_var_not_found)

###############################################################################
# Include variable to the markdown text
# \warning All the reference must be defined
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param text_vars the dict with all the references
# @param backup_option This parameter is set to true by default.
#                      If the backup option is set, then a file
#                      named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @param begin_var_re the regex to match the begin
# @param end_var_re the regex to match the end
# @param error_if_var_not_found boolean : throw Exception
#                                         if the var is not found
# @return the filename normalized
###############################################################################
def include_vars_to_md_file(filename, text_vars, backup_option=True,
                            filename_ext=".md",
                            begin_var_re=__begin_var_re__,
                            end_var_re=__end_var_re__,
                            error_if_var_not_found=True):
    return include_refs_to_md_file(filename, text_vars,
                                   backup_option=backup_option,
                                   filename_ext=filename_ext,
                                   begin_include_re=begin_var_re,
                                   end_include_re=end_var_re,
                                   error_if_no_key=error_if_var_not_found)

###############################################################################
# Search and include vars to the markdown text
# \warning All the reference must be defined
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param backup_option This parameter is set to true by default.
#                      If the backup option is set, then a file
#                          named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @return the filename normalized
###############################################################################
def search_include_vars_to_md_file(filename, backup_option=True,
                                   filename_ext=".md"):
    text_vars = get_vars_from_md_file(filename, filename_ext=filename_ext)
    return include_vars_to_md_file(filename, text_vars,
                                   backup_option=backup_option,
                                   filename_ext=filename_ext)

###############################################################################
# Search and include vars to the markdown text
# \warning All the reference must be defined
#
# @param text the markdown text
# @return the text completed
###############################################################################
def search_include_vars_to_md_text(text):
    text_vars = get_vars_from_md_text(text)
    return include_vars_to_md_text(text, text_vars)

###############################################################################
# Reteive the content a referenced file
#
# @param filename the filename
# @param search_folder the folder to find all the files
#                      (default: python files/referenced_files/)
# @return the content of the file
###############################################################################
def get_file_content_to_include(filename, search_folder=None):
    local_search_folder = search_folder
    if local_search_folder is None:
        local_search_folder = os.path.join(os.path.split(
            __get_this_filename())[0], "referenced_files")

    local_search_folder = common.check_folder(local_search_folder)

    return common.get_file_content(os.path.join(local_search_folder, filename))

def test_get_file_content_include():
    assert get_file_content_to_include("license.txt")[0:4] == "Copy"
    assert get_file_content_to_include("license.en.txt")[0:4] == "Copy"

###############################################################################
# Include file to the markdown text
# \warning All the reference must be defined
#
# @param text the markdown text
# @param include_file_re the regex to match the begin
# @param error_if_no_file boolean : throw Exception
#                                            if the key is not found
# @return the markdown text with the include
###############################################################################
def include_files_to_md_text(text, include_file_re=__include_file_re__,
                             error_if_no_file=True):
    # search begin
    match_file = re.search(include_file_re, text)

    # finish if no match
    if not match_file:
        return text

    # There is a match
    filename = match_file.group('name')
    logging.debug('Find the file %s', filename)

    text_file = get_file_content_to_include(filename)
    left_side = "| "
    text_file = left_side + text_file.replace('\n', '\n' + left_side)

    replace_text = """<!-- include-file(%(filename)s)
+-----------------------------------------------------------------------------+
%(left_side)s
%(text)s
+--------------------------------------------------------------------------"""\
""" -->""" % {'filename': filename,
              'left_side': left_side,
              'text': text_file}

    result = text[:match_file.start(0)]
    result += replace_text
    result += include_files_to_md_text(text[match_file.end(0):],
                                       include_file_re=include_file_re,
                                       error_if_no_file=error_if_no_file)

    return result

def test_include_files_to_md_text():
    result1 = include_files_to_md_text('<!-- include-file(license.txt) -->')
    result2 = include_files_to_md_text(result1)
    assert result1 == result2

###############################################################################
# Include file to the markdown file
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param backup_option This parameter is set to true by default.
#                      If the backup option is set, then a file named
#                           filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @return the filename normalized
###############################################################################
def include_files_to_md_file(filename, backup_option=True, filename_ext=".md"):
    logging.debug('Include file to the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename)

    # Create Backup
    if backup_option:
        common.create_backup(filename)

    # Change inside
    text = include_files_to_md_text(text)

    # Save the file
    os.remove(filename)
    common.set_file_content(filename, text, encoding="utf-8")
    return filename

###############################################################################
# set a var in the markdown text
#
# @param text the markdown text
# @param filename the filename
# @return the dict with the refs found key-> value
###############################################################################
def set_include_file_to_md_text(text, filename):

    result = ""
    current_text = text
    include_is_set = False
    include_text = '<!-- include-file(%s) -->' % (filename)

    # search the var
    match_var = re.search(__include_file_re__, current_text)

    while match_var is not None:
        key = match_var.group('name')
        logging.debug('Find the include file "%s" compare to "%s"',
                      key, filename)
        if key == filename:
            include_is_set = True

        result += current_text[0:match_var.end(0)]
        current_text = current_text[match_var.end(0):]
        match_var = re.search(__include_file_re__, current_text)

    if not include_is_set:
        if len(result) > 0:
            result += '\n'
        result += include_text
        if len(current_text) > 0 and current_text[0] != '\n':
            result += '\n\n'

    result += current_text
    return result

def test_set_include_file_():
    assert(set_include_file_to_md_text(
        '<!-- include-file(test) -->',
        "test") == '<!-- include-file(test) -->')
    assert(set_include_file_to_md_text(
        '<!-- include-file(essai) -->text',
        "test") == '<!-- include-file(essai) -->\n'
                   '<!-- include-file(test) -->\n\ntext')

###############################################################################
# del a var in the markdown text
#
# @param text the markdown text
# @return the dict with the refs found key-> value
###############################################################################
def get_include_file_list(text):

    result = []
    current_text = text

    # search the var
    match_var = re.search(__include_file_re__, current_text)

    while match_var is not None:
        result.append(match_var.group('name'))
        current_text = current_text[match_var.end(0):]
        match_var = re.search(__include_file_re__, current_text)

    return result

###############################################################################
# del a var in the markdown text
#
# @param text the markdown text
# @param filename the filename
# @return the dict with the refs found key-> value
###############################################################################
def del_include_file_to_md_text(text, filename):

    result = ""
    current_text = text

    # search the var
    match_var = re.search(__include_file_re__, current_text)

    while match_var is not None:
        key = match_var.group('name')
        logging.debug('Find the variable %s', key)
        if key == filename:
            result += current_text[0:match_var.start(0)]
        else:
            result += current_text[0:match_var.end(0)]

        current_text = current_text[match_var.end(0):]
        match_var = re.search(__include_file_re__, current_text)

    result += current_text
    return result

def test_del_include_file_():
    assert(del_include_file_to_md_text(
        '<!-- include-file(test) -->',
        "test") == '')
    assert(del_include_file_to_md_text(
        '<!-- include-file(essai) -->',
        "test") == '<!-- include-file(essai) -->')


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

    test_get_vars_from_md_text()
    test_include_files_to_md_text()
    test_set_var_to_md_text()
    test_del_var_to_md_text()
    test_set_include_file_()
    test_del_include_file_()
    test_set_title_in_md_text()
    test_get_title_from_md_text()

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
