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
# standard object to wrap file and access easily to the filename
#
# -----------------------------------------------------------------------------

import logging
import sys
import os
import os.path

from . import common

# -----------------------------------------------------------------------------
# get template
#
# @param filename the filename
# @param start_folder the folder to search the template
# @return the content
# -----------------------------------------------------------------------------
def get_template_file(filename, start_folder=None):
    if start_folder is None:
        start_folder = os.path.split(__get_this_filename())[0]

    local_template_folder = common.check_folder(
        os.path.join(start_folder, "template"))

    result = common.get_file_content(os.path.join(local_template_folder,
                                                  filename))

    return result


# -----------------------------------------------------------------------------
# get template folder file list
#
# @param folder the folder to scan
# @return the list of template files in a subfolder of template
# -----------------------------------------------------------------------------
def get_template_files_in_folder(folder):
    local_template_folder = common.check_folder(os.path.join(os.path.split(
        __get_this_filename())[0], os.path.join("template", folder)))

    result = []
    for filename in os.listdir(local_template_folder):
        if os.path.isfile(os.path.join(local_template_folder, filename)):
            result.append(os.path.join(folder, filename))

    return result


# -----------------------------------------------------------------------------
# Object for file name.
# Provide manipulation on filename
# Can be a object base for other purpose.
# -----------------------------------------------------------------------------
class FileName:

    # -------------------------------------------------------------------------
    # Initialize the object with the filename
    #
    # @param filename the filename to deal with
    # -------------------------------------------------------------------------
    def __init__(self, filename=None):
        # set the first value
        self.__full_filename = None

        # set the filenames
        if filename is not None:
            self.full_filename = filename

    # -------------------------------------------------------------------------
    # the full filename with the complet path
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def full_filename(self):
        return self.__full_filename

    # -------------------------------------------------------------------------
    # the full filename with the complet path
    # @param value The value to set
    # -------------------------------------------------------------------------
    @full_filename.setter
    def full_filename(self, value):
        if value is None:
            self.__full_filename = None
            return

        self.__full_filename = common.set_correct_path(value)

    # -------------------------------------------------------------------------
    # the filename (only the last part of the full filename)
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def filename(self):
        return os.path.split(self.__full_filename)[1]

    # -------------------------------------------------------------------------
    # the filename (only the last part of the full filename)
    # @param value The value to set
    # -------------------------------------------------------------------------
    @filename.setter
    def filename(self, value):
        if value is None:
            self.__full_filename = None
            return

        value = common.get_valid_filename(value)

        if self.__full_filename is None:
            self.__full_filename = value
        else:
            self.__full_filename = os.path.split(self.__full_filename)[0]
            self.__full_filename = os.path.join(self.__full_filename, value)

        self.__full_filename = common.set_correct_path(self.__full_filename)

    # -------------------------------------------------------------------------
    # the path to the filename (only the first part of the full filename)
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def filename_path(self):
        if self.__full_filename is None:
            return None
        return os.path.split(self.__full_filename)[0]

    # -------------------------------------------------------------------------
    # the path to the filename (only the first part of the full filename)
    # @param value The value to set
    # -------------------------------------------------------------------------
    @filename_path.setter
    def filename_path(self, value):
        if value is None:
            logging.error('Can not set an empty path')
            raise Exception('Can not set an empty path')

        value = common.set_correct_path(value)
        self.__full_filename = os.path.join(value,
                                            os.path.split(self.filename)[1])

    # -------------------------------------------------------------------------
    # the extension of the filename
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def filename_ext(self):
        if self.__full_filename is None:
            return None
        return os.path.splitext(self.__full_filename)[1]

    # -------------------------------------------------------------------------
    # the extension of the filename
    # @param value The value to set
    # -------------------------------------------------------------------------
    @filename_ext.setter
    def filename_ext(self, value):
        if value is None:
            logging.error('Can not set an empty extension')
            raise Exception('Can not set an empty extension')

        self.__full_filename = os.path.splitext(self.__full_filename)[0] + \
            value

    # -------------------------------------------------------------------------
    # test if the file exist
    # @return the result of the test
    # -------------------------------------------------------------------------
    def is_file(self):
        return (self.__full_filename is not None) and \
            (os.path.isfile(self.__full_filename))

    # -------------------------------------------------------------------------
    # test if the filename is en directory
    # @return the result of the test
    # -------------------------------------------------------------------------
    def is_dir(self):
        return (self.__full_filename is not None) and \
            (os.path.isdir(self.__full_filename))

    # -------------------------------------------------------------------------
    # __repr__ is a built-in function used to compute the "official"
    # string reputation of an object
    # __repr__ goal is to be unambiguous
    # -------------------------------------------------------------------------
    def __repr__(self):
        return self.__full_filename

    # -------------------------------------------------------------------------
    # __str__ is a built-in function that computes the "informal"
    # string reputation of an object
    # __str__ goal is to be readable
    # -------------------------------------------------------------------------
    def __str__(self):
        result = ""
        result += "          path=%s\n" % self.filename_path
        result += "      filename=%s\n" % self.filename
        result += "file extension=%s\n" % self.filename_ext

        if self.is_dir():
            result += "It is a directory\n"
            return result

        if self.is_file():
            result += "The file exists\n"
            return result

        result += "The file or the directory does not exist\n"
        return result

# -----------------------------------------------------------------------------
# Object for file content.
# Provide manipulation on file to get the content and handle the backup.
# Can be a object base for other purpose.
# -----------------------------------------------------------------------------
class FileContent(FileName):

    # -------------------------------------------------------------------------
    # Initialize the object from a content a filename or other
    #
    # @param filename the filename of the file
    # @param content the content of the file if needed
    # @param backup the backup option (if true each save generate a backup)
    # @param encoding the encoding to read the file
    # -------------------------------------------------------------------------
    def __init__(self, filename=None,
                 content=None,
                 backup=True,
                 encoding="utf-8"):

        # init the base class
        FileName.__init__(self, filename=filename)

        # set the first value
        self.__content = None
        self.__backup = None
        self.__save_needed = False

        # fill the data
        self.backup = backup

        # read the file if needed
        if (self.is_file()) and (content is None):
            self.__content = common.get_file_content(self.full_filename,
                                                     encoding=encoding)

        # set the content if needed
        if content is not None:
            self.content = content

    # -------------------------------------------------------------------------
    # Acces to the content
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def content(self):
        return self.__content

    # -------------------------------------------------------------------------
    # Acces to the content
    # @param value The value to set
    # -------------------------------------------------------------------------
    @content.setter
    def content(self, value):
        self.__save_needed = True
        self.__content = value

    # -------------------------------------------------------------------------
    # Acces to the backup status
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def backup(self):
        return self.__backup

    # -------------------------------------------------------------------------
    # Acces to the backup status
    # @param value The value to set
    # -------------------------------------------------------------------------
    @backup.setter
    def backup(self, value):
        self.__backup = bool(value)

    # -------------------------------------------------------------------------
    # Acces to the save needed status
    # @return the value
    # -------------------------------------------------------------------------
    @property
    def save_needed(self):
        return self.__save_needed

    # -------------------------------------------------------------------------
    # Acces to the save needed status
    # @param value The value to set
    # -------------------------------------------------------------------------
    @save_needed.setter
    def save_needed(self, value):
        self.__save_needed = bool(value)

    # -------------------------------------------------------------------------
    # Read the content of the filename
    # @param filename The filename if needed (this opion set the filename)
    # @param encoding The encoding of the file
    # -------------------------------------------------------------------------
    def read(self, filename=None, encoding="utf-8"):
        if filename is not None:
            self.full_filename = filename

        if self.full_filename is None:
            logging.error('Can not read the content without filename')
            raise Exception('Can not read the content without filename')

        self.content = common.get_file_content(self.full_filename,
                                               encoding=encoding)
        self.__save_needed = False

    # -------------------------------------------------------------------------
    # Write the content of the filename
    # @param filename The filename if needed (this opion set the filename)
    # @param encoding The encoding of the file
    # @param backup_ext The backup extension if needed
    # -------------------------------------------------------------------------
    def write(self, filename=None, backup_ext=".bak", encoding="utf-8"):
        if self.content is None:
            logging.error('Ther is no content to save to %s', self.filename)
            return

        if filename is not None:
            self.full_filename = filename

        if os.path.isfile(self.full_filename) and self.backup:
            common.create_backup(self.full_filename, backup_ext=backup_ext)

        if self.full_filename is None:
            logging.error('Can not save the content without filename')
            raise Exception('Can not save the content without filename')

        common.set_file_content(self.full_filename, self.content,
                                encoding=encoding)
        self.__save_needed = False

    # -------------------------------------------------------------------------
    # __repr__ is a built-in function used to compute the "official"
    # string reputation of an object
    # __repr__ goal is to be unambiguous
    # -------------------------------------------------------------------------
    def __repr__(self):
        return FileName.__repr__(self) + ":" + repr(self.__content)

    # -------------------------------------------------------------------------
    # __str__ is a built-in function that computes the "informal"
    # string reputation of an object
    # __str__ goal is to be readable
    # -------------------------------------------------------------------------
    def __str__(self):
        result = FileName.__str__(self)
        result += "backup option=%s\n" % self.backup
        result += "save needed=%s\n" % self.__save_needed

        if self.content is None:
            result += "Content is None"
            return result

        result += "Content char number=%6d\n" % len(self.content)

        return result


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
