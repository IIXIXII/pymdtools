#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================

"""All functions about translation.
"""

import logging
import sys
import os
import gettext

# from googletrans import Translator as GTranslator
# from goslate import Goslate as GoTranslator
from translate import Translator
import upref

from . import common
from . import mistunege as mistune
from . import mdrender


# -----------------------------------------------------------------------------
# function of the module
# -----------------------------------------------------------------------------
__all__ = ["N_", "translate", "translate_txt", "translate_md"]


# -----------------------------------------------------------------------------
# Neutral translation
#
# @param message the message to translate
# @return the message
# -----------------------------------------------------------------------------
def N_(message):
    return message

# -----------------------------------------------------------------------------
# get the locale dir
# Search for the french translation to find the folder
#
# @return the locale directory
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# gettext translation object for a language
#
# @param lang the language
# @return the translation object
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# translation function
#
# @param obj the object to translate
# @param lang the language
# @param domain_name the domain
# @return the object translated
# -----------------------------------------------------------------------------
def translate(obj, lang, domain_name):
    if isinstance(obj, dict):
        return translate_dict(obj, lang, domain_name)
    if isinstance(obj, list):
        return translate_list(obj, lang, domain_name)
    return translate_str(obj, lang, domain_name)


# -----------------------------------------------------------------------------
# translation function
#
# @param message the message to translate
# @param lang the language
# @param domain_name the domain
# @return the message translated
# -----------------------------------------------------------------------------
def translate_str(message, lang, domain_name):
    lang_translation = get_translation(lang, domain_name)
    lang_translation.install()
    return lang_translation.gettext(message)


# -----------------------------------------------------------------------------
# translation function
#
# @param obj the object to translate
# @param lang the language
# @param domain_name the domain
# @return the message translated
# -----------------------------------------------------------------------------
def translate_dict(obj, lang, domain_name):
    result = {}
    for key in obj:
        result[key] = translate(obj[key], lang, domain_name)
    return result


# -----------------------------------------------------------------------------
# translation function
#
# @param obj the object to translate
# @param lang the language
# @param domain_name the domain
# @return the message translated
# -----------------------------------------------------------------------------
def translate_list(obj, lang, domain_name):
    result = []
    for key in obj:
        result.append(translate(key, lang, domain_name))
    return result

# -----------------------------------------------------------------------------
# The european language list to manage
#
# @return the language list
# -----------------------------------------------------------------------------
def eu_lang_list():
    return [
        'bg', 'cs', 'da', 'de', 'et', 'el', 'en', 'es', 'fr', 'ga', 'hr',
        'it', 'lv', 'lt', 'hu', 'mt', 'nl', 'pl', 'pt', 'ro', 'sk', 'sl',
        'fi', 'sv', 'tr', 'ru',
    ]

# -----------------------------------------------------------------------------
# Translation parameters
#
# @return the parameter
# -----------------------------------------------------------------------------
def _translation_parameter():
    data_conf = {
        'provider': {
            'label': "Provider for the translation",
            'description': "There is two provider : microsoft or mymemory",
            'value': 'mymemory',
        },
        'secret_access_key': {
            'label': "Secret key ",
            'description': "Secrect key to access the service",
            'value': '',
        },
    }
    parameter = upref.get_pref(data_conf, name="translation")

    secret_key = parameter['secret_access_key']
    if secret_key is None or len(secret_key) < 1:
        del parameter['secret_access_key']

    parameter['provider'] = parameter['provider'].lower()

    return parameter

# -----------------------------------------------------------------------------
# Translate a phrase with google
#
# @param text the text to translate
# @param src the source language
# @param dest the destination language
# -----------------------------------------------------------------------------
def translate_txt(text, src="fr", dest="en"):
    if text and not text.isspace():
        # option 1
        # trans = GTranslator()
        # result_trans = trans.translate(text, src=src, dest=dest)
        # return result_trans.text

        # option 2
        # trans = GoTranslator()
        # result_trans = trans.translate(text, dest, source_language=src)
        # return result_trans

        translator = Translator(from_lang=src, to_lang=dest,
                                **_translation_parameter())
        try:
            return translator.translate(text)
        except BaseException as err:
            logging.error("Error in translation '%s' for '%s'", text, err)
            return ""

    return text


# -----------------------------------------------------------------------------
# Translate a markdown with google
#
# @param md_text the md text to translate
# @param src the source language
# @param dest the destination language
# -----------------------------------------------------------------------------
def translate_md(md_text, src="fr", dest="en"):

    class LocalRender(mdrender.MdRenderer):
        def text(self, text):
            return translate_txt(text, src=src, dest=dest)

    my_renderer = LocalRender()
    markdown = mistune.Markdown(renderer=my_renderer)

    result = markdown(md_text)
    return result

# def translate_md2(md_text, src="fr", dest="en"):
#     from . import mdtopdf
#     from . import instruction
#     from . import markdownify
#     md_pure_text = instruction.strip_xml_comment(md_text)
#     html_text = mdtopdf.get_md_to_html_converter('mistune')(md_pure_text)
#     result_html = translate_txt(html_text, src=src, dest=dest)
#     return markdownify.markdownify(result_html)

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
