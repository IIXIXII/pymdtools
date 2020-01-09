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
# standard object to wrap file and access easily to the filename
#
###############################################################################

import logging
import sys
import os
import os.path
import markdown

if (__package__ in [None, '']) and ('.' not in __name__):
    import filetools
    import instruction
    import normalize
else:
    from . import filetools
    from . import instruction
    from . import normalize


###############################################################################
# Object for markdown content.
# Provide manipulation on file to get the content and handle the backup.
# Can be a object base for other purpose.
###############################################################################
class MarkdownContent(filetools.FileContent):

    ###########################################################################
    # Initialize the object from a content a filename or other
    #
    # @param filename the filename of the file
    # @param content the content of the file if needed
    # @param backup the backup option (if true each save generate a backup)
    # @param encoding the encoding to read the file
    ###########################################################################
    def __init__(self, filename=None,
                 content=None,
                 backup=True,
                 encoding="unknown", **kwargs):

        # init the base class
        filetools.FileContent.__init__(self,
                                       content=content,
                                       filename=filename,
                                       backup=backup,
                                       encoding=encoding)

        # set the first value
        self.__var_dict = {}
        self.__var_dict_text = None
        self.__kwargs = kwargs

    ###########################################################################
    # Update the dict of variable
    ###########################################################################
    def __update_dict(self):
        if self.__var_dict_text != self.content:
            self.__var_dict = instruction.get_vars_from_md_text(self.content)
            self.__var_dict_text = self.content

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def __setitem__(self, key, item):
        self.content = instruction.set_var_to_md_text(self.content,
                                                      key, item)
        self.__update_dict()

    ###########################################################################
    # Access to members by identifier
    # @return the value
    ###########################################################################
    def __getitem__(self, key):
        self.__update_dict()
        return self.__var_dict[key]

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def __delitem__(self, key):
        self.content = instruction.del_var_to_md_text(self.content,
                                                      key)
        self.__update_dict()

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def has_key(self, k):
        self.__update_dict()
        return k in self.__var_dict

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def keys(self):
        self.__update_dict()
        return self.__var_dict.keys()

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def values(self):
        self.__update_dict()
        return self.__var_dict.values()

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def items(self):
        self.__update_dict()
        return self.__var_dict.items()

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def __contains__(self, item):
        self.__update_dict()
        return item in self.__var_dict

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def __iter__(self):
        self.__update_dict()
        return iter(self.__var_dict)

    ###########################################################################
    # the title from the content
    # @return the value
    ###########################################################################
    @property
    def title(self):
        return instruction.get_title_from_md_text(self.content)

    ###########################################################################
    # the filename (only the last part of the full filename)
    # @param value The value to set
    ###########################################################################
    @title.setter
    def title(self, value):
        self.content = instruction.set_title_in_md_text(self.content,
                                                        value)

    ###########################################################################
    # get the toc from the content
    # @return the table of content
    ###########################################################################
    @property
    def toc(self):
        md_reader = markdown.Markdown(extensions=['toc'])
        md_reader.convert(self.content)
        return md_reader.toc

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def set_include_file(self, filename):
        self.content = instruction.set_include_file_to_md_text(self.content,
                                                               filename)
        self.__update_dict()

    ###########################################################################
    # Access to members by identifier
    ###########################################################################
    def del_include_file(self, filename):
        self.content = instruction.del_include_file_to_md_text(self.content,
                                                               filename)
        self.__update_dict()

    ###########################################################################
    # Beautify teh content
    # @return the content
    ###########################################################################
    def beautify(self):
        self.content = normalize.md_beautifier(self.content)
        return self.content

    ###########################################################################
    # Proccess the tags
    # @return the content
    ###########################################################################
    def process_tags(self):
        self.content = instruction.include_files_to_md_text(self.content,
                                                            **self.__kwargs)
        self.content = instruction.search_include_vars_to_md_text(self.content)

        refs = instruction.get_refs_around_md_file(
            self.full_filename,
            filename_ext=self.filename_ext,
            depth_up=0, depth_down=-1)
        refs = instruction.get_refs_other(refs, **self.__kwargs)
        self.content = instruction.include_refs_to_md_text(self.content, refs)
        self.__update_dict()

        return self.content

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

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
