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
# Standard function are here. Common function and object.
###############################################################################

import logging
import sys
import os
import os.path
import shutil
import codecs
import tempfile
import time
import re


###############################################################################
# A Constant class object simple to contain a const value
###############################################################################
class Constant:
    ###########################################################################
    # Create the constant
    # @param value the constant value
    ###########################################################################
    def __init__(self, value=None):
        self.value = value

    ###########################################################################
    # Obtain the value
    ###########################################################################
    def get_value(self):
        return self.value

    ###########################################################################
    # Obtain the value
    ###########################################################################
    def get(self):
        return self.value

    ###########################################################################
    # Obtain the value
    ###########################################################################
    def __get__(self, _ignore_instance, _ignore_owner):
        return self.value

    ###########################################################################
    # Protection for changed
    ###########################################################################
    def __set__(self, _ignore_instance, _ignore_value):
        raise ValueError("You can't change a constant value")


###############################################################################
# This decorator can be used to turn simple functions
#     into well-behaved decorators, so long as the decorators
#     are fairly simple. If a decorator expects a function and
#     returns a function (no descriptors), and if it doesn't
#     modify function attributes or docstring, then it is
#     eligible to use this. Simply apply @simple_decorator to
#     your decorator and it will automatically preserve the
#     docstring and function attributes of functions to which
#     it is applied.
###############################################################################
def simple_decorator(decorator):
    def new_decorator(the_function):
        result = decorator(the_function)
        result.__name__ = the_function.__name__
        result.__doc__ = the_function.__doc__
        result.__dict__.update(the_function.__dict__)
        return result

    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

###############################################################################
# define a static decorator for function
#
# @code{.py}
# 	(at)static(__folder_md_test__=None)
# 	def get_test_folder():
#     		if get_test_folder.__folder_md_test__ is None:
#         	get_test_folder.__folder_md_test__ = check_folder(os.path.join(
#             		os.path.split(__get_this_filename())[0], "test-md"))
#     		return get_test_folder.__folder_md_test__
# @endcode
#
# @param kwargs list of arguments
# @return the wrap function
###############################################################################
def static(**kwargs):
    def wrap(the_decorated_function):
        for key, value in kwargs.items():
            setattr(the_decorated_function, key, value)
        return the_decorated_function
    return wrap


###############################################################################
# Convert string to the output
#
# @param text the text
# @param coding_in initial coding of the string
# @param coding_out final coding of the string
# @return the text converted
###############################################################################
def print_conv(text, coding_in='utf-8', coding_out=None):
    if (coding_out is None) and (sys.stdout is not None):
        coding_out = sys.stdout.encoding
    else:
        coding_out = 'utf-8'

    return text.encode(coding_in).decode(coding_out, 'ignore')


###############################################################################
# Remove all whitespace from the beginning and the end of the text
#
# @param text the text
# @return the text without the whitespace at the beginning and at the end
###############################################################################
def strip_first_and_last_space(text):
    whitespace_list = [' ', '\t', '\r', '\n']
    result = text
    while (len(result) > 0) and (result[0] in whitespace_list):
        result = result[1:]

    while (len(result) > 0) and (result[-1] in whitespace_list):
        result = result[:-1]
    return result


###############################################################################
# Retrive the correct complet path
# This function return a folder or filename with a standard way of writing.
#
# @param folder_or_file_name the folder or file name
# @return the folder or filename normalized.
###############################################################################
def set_correct_path(folder_or_file_name):
    return os.path.abspath(folder_or_file_name)


###############################################################################
# Test a folder
# Test if the folder exist.
#
# @exception RuntimeError if the name is a file or not a folder
#
# @param folder the folder name
# @return the folder normalized.
###############################################################################
def check_folder(folder):
    if os.path.isfile(folder):
        logging.error('%s can not be a folder (it is a file)', folder)
        raise RuntimeError('%s can not be a folder (it is a file)' % folder)

    if not os.path.isdir(folder):
        logging.error('%s is not a folder', folder)
        raise RuntimeError('%s is not a folder' % folder)

    return set_correct_path(folder)


###############################################################################
# Test a folder
# test if the folder exist and create it if possible and necessary.
#
# @exception RuntimeError if the name is a file
#
# @param folder the folder name
# @return the folder normalized.
###############################################################################
def check_create_folder(folder):
    if os.path.isfile(folder):
        logging.error('%s can not be a folder (it is a file)', folder)
        raise RuntimeError('%s can not be a folder (it is a file)' % folder)

    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)

    return set_correct_path(folder)

###############################################################################
# test if this is a file and correct the path
#
# @exception RuntimeError if the name is not a file or if the extension
#                         is not correct
#
# @param filename the file name
# @param filename_ext the file name extension like ".ext" or ".md"
# @return the filename normalized.
###############################################################################
def check_is_file_and_correct_path(filename, filename_ext=None):
    filename = set_correct_path(filename)

    if not os.path.isfile(filename):
        logging.error('"%s" is not a file', (filename))
        raise Exception('"%s" is not a file' % (filename))

    current_ext = os.path.splitext(filename)[1]
    if (filename_ext is not None) and (current_ext != filename_ext):

        raise Exception('The extension of the file %s '
                        'is %s and not %s as expected.' % (
                            filename, current_ext, filename_ext))

    return filename


###############################################################################
# get the number of subfolder in an path
#
# @param filename the filename
# @return the value
###############################################################################
def number_of_subfolder(filename):
    name = os.path.normpath(filename)

    counter = -1
    counter_max = 100
    while (name != os.path.split(name)[0]) and (counter < counter_max):
        name = os.path.split(name)[0]
        counter += 1

    if counter >= counter_max:
        logging.error('Can not count the number of subfolder '
                      'in the filename %s.', filename)
        raise RuntimeError('Can not count the number of subfolder '
                           'in the filename %s.' % filename)

    return max(counter, 0)

###############################################################################
# Create a backup of a file in the same folder with an extension .xxx.bak
#
#
# @exception RuntimeError a new filename for the backup cannot be found
#
# @param filename the file name
# @param backup_ext the backup file name extension like ".bak"
# @return the backup filename normalized.
###############################################################################
def create_backup(filename, backup_ext=".bak"):
    logging.info('Create the backup file for %s', filename)

    filename = check_is_file_and_correct_path(filename)

    count = 0
    nb_max = 100

    today = get_today()
    new_filename = "%s.%s-%03d%s" % (filename, today, count, backup_ext)

    while (os.path.isfile(new_filename)) and (count < nb_max):
        count = count + 1
        new_filename = "%s.%s-%03d%s" % (filename, today, count, backup_ext)

    if count >= nb_max:
        logging.error('Can not find a backup filename for %s', (filename))
        raise Exception('Can not find a backup filename for %s' % (filename))

    logging.info('Backup filename %s to %s', filename, new_filename)
    shutil.copyfile(filename, new_filename)

    return new_filename

###############################################################################
# Get the encoding of a file
#
# @param filename the file name
# @return the encoding detect
###############################################################################
def get_file_encoding(filename):
    logging.debug('Get encoding of the filename %s', (filename))

    import chardet.universaldetector
    detector = chardet.universaldetector.UniversalDetector()

    with open(filename, 'rb') as file:
        for line in file:
            detector.feed(line)
            if detector.done:
                break
    detector.close()
    return detector.result['encoding']


###############################################################################
# Get the content of a file. This function delete the BOM.
#
# @param filename the file name
# @param encoding the encoding of the file
# @return the content
###############################################################################
def get_file_content(filename, encoding="utf-8"):
    logging.debug('Get content of the filename %s', (filename))
    filename = check_is_file_and_correct_path(filename)

    local_encoding = encoding
    if local_encoding.upper() == "UNKNOWN":
        local_encoding = get_file_encoding(filename)

    # Read the file
    input_file = codecs.open(filename, mode="r", encoding=local_encoding)
    try:
        content = input_file.read()
    except UnicodeDecodeError as err:
        raise IOError("%s\nCannot read the file %s" % (str(err),
                                                       filename))
    input_file.close()

    if content.startswith(u'\ufeff'):
        content = content[1:]

    return content

###############################################################################
# Set the content of a file. This function create a BOM in the UTF-8 encoding.
# This function create the file or overwrite the file.
#
# @param filename the file name
# @param content the content
# @param encoding the encoding of the file
# @param bom the bit order mark at the beginning of the file
# @return filename corrected
###############################################################################
def set_file_content(filename, content, encoding="utf-8", bom=True):
    logging.debug('Ser content of the filename %s', (filename))
    filename = set_correct_path(filename)

    output_file = codecs.open(filename, "w", encoding=encoding)

    if (not content.startswith(u'\ufeff')) and \
            (encoding == "utf-8") and bom:
        output_file.write(u'\ufeff')

    output_file.write(content)
    output_file.close()

    return filename


###############################################################################
# Transform a string to be a good filename for windows
#
# @param filename the file name
# @param char_to_replace the special char to replace
# @param replacement the replacement char ("_" for example)
# @return the right filename
###############################################################################
def get_valid_filename(filename,
                       char_to_replace=r'[\\/*?:"<>|()]', replacement="_"):
    name = re.sub(char_to_replace, replacement, filename)
    return name


###############################################################################
# cut string with words
#
# @param value the phrase to simplify
# @param limit the limit of the string
# @param char_split the character to split the string
# @param min_last_word the number of cher minimum for the last word
# @return the simplified phrase
###############################################################################
def limit_str(value, limit, char_split, min_last_word=2):
    words = value.split(char_split)
    result = ""
    for word in words:
        if (len(result) < limit) and \
            ((len(result) + len(word) + len(char_split) < limit) or
             (len(word) > min_last_word)):
            if len(result) > 0:
                result += char_split
            result += word
    return result


###############################################################################
# Convert to ascii char
#
# @param value the phrase to simplify
# @return the simplified phrase
###############################################################################
def str_to_ascii(value):
    import unidecode
    return unidecode.unidecode(value)


###############################################################################
# simplify name or phrase
# Normalizes string, converts to lowercase, removes non-alpha characters,
# and converts spaces to hyphens.
# Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
#    Remove characters that aren't alphanumerics, underscores, or hyphens.
#    Convert to lowercase. Also strip leading and trailing whitespace.
#
# @param value the phrase to simplify
# @param allow_unicode unicode possibility
# @return the simplified phrase
###############################################################################
def slugify(value, allow_unicode=False):
    value = str(value)

    import unicodedata

    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).\
            encode('ascii', 'ignore').decode('ascii')

    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


###############################################################################
# Transform a string to be a good filename for windows
#
# @param filename the file name
# @param replacement the replacement char
# @return the right filename
###############################################################################
def get_flat_filename(filename, replacement="_"):
    return get_valid_filename(filename,
                              char_to_replace=r'[\.\\/*?:"<>|() \'’,]',
                              replacement=replacement)

###############################################################################
# Create a temproray folder in an appropriate temp area
#
# @return A empty folder located in a temp area
###############################################################################
def get_new_temp_dir():
    tmp_start = os.path.join(tempfile.gettempdir(),
                             get_valid_filename(
                                 '.{}'.format(hash(os.times()))))

    count = 0
    nb_max = 100

    new_tmp = "%s.%03d" % (tmp_start, count)

    while (os.path.isdir(new_tmp)) and (count < nb_max):
        count = count + 1
        new_tmp = "%s.%03d" % (tmp_start, count)

    if count >= nb_max:
        logging.error('Can not find a temp dir')
        raise Exception('Can not find a temp dir')

    logging.info('Create temp dir %s', new_tmp)
    os.makedirs(new_tmp)

    return new_tmp

###############################################################################
# Change the filename extension
#
# @param filename the filename
# @param ext the new extension with a dot (ext = '.txt')
# @return the filename with the new extension
###############################################################################
def filename_ext_to(filename, ext):
    return os.path.splitext(filename)[0] + ext


###############################################################################
# Change the filename extension to html
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_html(filename):
    return filename_ext_to(filename, ".html")


###############################################################################
# Change the filename extension to md
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_md(filename):
    return filename_ext_to(filename, ".md")


###############################################################################
# Change the filename extension to pdf
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_pdf(filename):
    return filename_ext_to(filename, ".pdf")


###############################################################################
# Change the filename extension to hhp
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_hhp(filename):
    return filename_ext_to(filename, ".hhp")


###############################################################################
# Change the filename extension to hhc
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_hhc(filename):
    return filename_ext_to(filename, ".hhc")


###############################################################################
# Change the filename extension to hhk
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_hhk(filename):
    return filename_ext_to(filename, ".hhk")


###############################################################################
# Change the filename extension to chm
#
# @param filename the filename
# @return the filename with the new extension
###############################################################################
def filename_ext_to_chm(filename):
    return filename_ext_to(filename, ".chm")


###############################################################################
# Get today date
#
# @return a string "YYYY-MM-DD"
###############################################################################
def get_today():
    return time.strftime("%Y-%m-%d", time.gmtime())


###############################################################################
# Apply function to every files in folder
#
# @param folder	The folder to scan
# @param process The function to pally to each file the function take one
#                parameter (the filename)
# @param filename_ext The file extension (markdown for the default)
###############################################################################
def apply_function_in_folder(folder, process, filename_ext=".md"):
    for root, unused_dirs, files in os.walk(folder):
        for filename in files:
            if os.path.join(root, filename).endswith(filename_ext):
                process(os.path.join(root, filename))

###############################################################################
# Check the length of an object
#
# @param obj the object.
# @param length the object length (default = 1).
# @return the object.
###############################################################################
def check_len(obj, length=1):
    if not len(obj) == length:
        logging.error('The list is supposed to have a '
                      'length equal to %s and it is %d ',
                      length, len(obj))
        raise RuntimeError(
            'The list is supposed to have a length equal '
            'to %s and it is %d ' % (length, len(obj)))
    return obj


###############################################################################
# Find a file with a deep search
# the search is like this
# 	for begin_path in start_points:
# 		for number_of_parent_path in [0; nb_up_path]:
# 			for relative_path in relative_paths:
#    			Search in begin_path/((../)*number_of_parent_path)/relative_paths
# return the first file found
#
# @param file_wanted the filename we are looking for.
# @param start_points the absolute path to some potential
#                     beginning of the search.
# @param relative_paths potential relative path to search for
# @param nb_up_path up path to search
# @return full path to the seached file
###############################################################################
def search_for_file(file_wanted, start_points, relative_paths, nb_up_path=4):
    logging.info('Search for the file %s', file_wanted)

    result = []

    for begin_path in start_points:
        for num_up in range(0, nb_up_path):
            for relative_path in relative_paths:
                file_to_test = set_correct_path(os.path.join(
                    begin_path, "../" * num_up, relative_path, file_wanted))
                if os.path.isfile(file_to_test):
                    logging.info('Found the file %s', (file_to_test))
                    result.append(file_to_test)

    if len(result) == 0:
        raise Exception('Not able to find the file %s' % file_wanted)

    return result[0]

def test_search_for_file():
    start_point = os.path.split(__get_this_filename())[0]
    assert(search_for_file("common.py", ["./", start_point],
                           ["./", "python"]) is not None)


###############################################################################
# convert a path to url
#
# @param path the path to convert
# @param remove_accent remove the accents of the path and convert them
#                      in the base letters
# @return string cleaned
###############################################################################
def path_to_url(path, remove_accent=True):
    result = path.lower()
    result = re.sub(r"\s+", '-', result)
    if remove_accent:
        result = str_to_ascii(result)

    import urllib.request
    result = urllib.request.pathname2url(result)

    result = result.replace("/-", "/").replace("-/", "/")
    return result


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

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
