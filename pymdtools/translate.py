#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# @copyright Copyright (C) Guichet Entreprises - All Rights Reserved
#     All Rights Reserved.
#     Unauthorized copying of this file, via any medium is strictly prohibited
#     Dissemination of this information or reproduction of this material
#     is strictly forbidden unless prior written permission is obtained
#     from Guichet Entreprises.
###############################################################################

###############################################################################
# Some functions to process xml and html
#
###############################################################################

import logging
import sys
import os
import gettext

from googletrans import Translator as GTranslator

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
    import mistunege as mistune
    import mdrender
else:
    from . import common
    from . import mistunege as mistune
    from . import mdrender


###############################################################################
# function of the module
###############################################################################
__all__ = ["N_", "translate", "translate_txt", "translate_md"]


###############################################################################
# Neutral translation
#
# @param message the message to translate
# @return the message
###############################################################################
def N_(message):
    return message

###############################################################################
# get the locale dir
# Search for the french translation to find the folder
#
# @return the locale directory
###############################################################################
@common.static(__folder__=None)
def get_localedir(domain_name=None, folder=None):
    if get_localedir.__folder__ is None:
        search_folder = [__get_this_folder()]
        if folder is not None:
            search_folder.append(folder)
        search_path = ["locale/fr/LC_MESSAGES", "fr/LC_MESSAGES"]
        if domain_name is None:
            logging.error('Need a domain name to find the translation')
            raise RuntimeError('Need a domain name to find the translation')

        the_file = common.search_for_file(domain_name + '.mo',
                                          start_points=search_folder,
                                          relative_paths=search_path,
                                          nb_up_path=3)
        the_folder = os.path.split(the_file)[0]

        # go two folder up
        the_folder = os.path.split(the_folder)[0]
        the_folder = os.path.split(the_folder)[0]

        get_localedir.__folder__ = the_folder

    return get_localedir.__folder__


###############################################################################
# gettext translation object for a language
#
# @param lang the language
# @return the translation object
###############################################################################
@common.static(__trans__=None)
def get_translation(lang, domain_name, folder=None):
    if get_translation.__trans__ is None:
        get_translation.__trans__ = {}

    if domain_name not in get_translation.__trans__:
        get_translation.__trans__[domain_name] = {}

    if lang in get_translation.__trans__[domain_name]:
        return get_translation.__trans__[domain_name][lang]

    trans = gettext.translation(domain_name,
                                languages=[lang],
                                localedir=get_localedir(domain_name, folder))
    get_translation.__trans__[domain_name][lang] = trans

    return trans

###############################################################################
# translation function
#
# @param obj the object to translate
# @param lang the language
# @param domain_name the domain
# @return the object translated
###############################################################################
def translate(obj, lang, domain_name):
    if isinstance(obj, dict):
        return translate_dict(obj, lang, domain_name)
    if isinstance(obj, list):
        return translate_list(obj, lang, domain_name)
    return translate_str(obj, lang, domain_name)


###############################################################################
# translation function
#
# @param message the message to translate
# @param lang the language
# @param domain_name the domain
# @return the message translated
###############################################################################
def translate_str(message, lang, domain_name):
    lang_translation = get_translation(lang, domain_name)
    lang_translation.install()
    return lang_translation.gettext(message)


###############################################################################
# translation function
#
# @param obj the object to translate
# @param lang the language
# @param domain_name the domain
# @return the message translated
###############################################################################
def translate_dict(obj, lang, domain_name):
    result = {}
    for key in obj:
        result[key] = translate(obj[key], lang, domain_name)
    return result


###############################################################################
# translation function
#
# @param obj the object to translate
# @param lang the language
# @param domain_name the domain
# @return the message translated
###############################################################################
def translate_list(obj, lang, domain_name):
    result = []
    for key in obj:
        result.append(translate(key, lang, domain_name))
    return result

###############################################################################
# The european language list to manage
#
# @return the language list
###############################################################################
def eu_lang_list():
    return [
        'bg', 'cs', 'da', 'de', 'et', 'el', 'en', 'es', 'fr', 'ga', 'hr',
        'it', 'lv', 'lt', 'hu', 'mt', 'nl', 'pl', 'pt', 'ro', 'sk', 'sl',
        'fi', 'sv', 'tr', 'ru',
    ]


###############################################################################
# Translate a phrase with google
#
# @param text the text to translate
# @param src the source language
# @param dest the destination language
###############################################################################
def translate_txt(text, src="fr", dest="en"):
    trans = GTranslator()
    result_trans = trans.translate(text, src=src, dest=dest)
    return result_trans.text


###############################################################################
# Translate a markdown with google
#
# @param md_text the md text to translate
# @param src the source language
# @param dest the destination language
###############################################################################
def translate_md(md_text, src="fr", dest="en"):

    class LocalRender(mdrender.MdRenderer):
        def text(self, text):
            return translate_txt(text, src=src, dest=dest)

    my_renderer = LocalRender()
    markdown = mistune.Markdown(renderer=my_renderer)

    result = markdown(md_text)
    return result


###############################################################################
# Get the local folder of this script
#
# @return the local folder.
###############################################################################
def get_local_folder():
    return os.path.split(os.path.abspath(os.path.realpath(
        __get_this_filename())))[0]


###############################################################################
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return the folder of THIS script.
###############################################################################
def __get_this_folder():
    return os.path.split(os.path.abspath(os.path.realpath(
        __get_this_filename())))[0]


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

    print(translate_txt("Guichet Entreprises", src="fr", dest="bg"))

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
