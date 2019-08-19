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
# Common functions for the package mdtools. Standard function are here.
#
###############################################################################

import logging
import json
import sys
import os
import re
import copy
from url_normalize import url_normalize

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
else:
    from . import common


###############################################################################
# test for an external internet link
#
# @param url
# @return True if it is an external link
###############################################################################
def is_external_link(url):
    target_url = url.lower().replace(" ", "")
    return len(target_url) > 4 and target_url[0:4] == "http"


###############################################################################
# return the domain name
#
# @param url
# @return the domain name or the url if its not external
###############################################################################
def get_domain_name(url):
    if not is_external_link(url):
        return url

    target_url_norm = url_normalize(url)
    result = target_url_norm.split(
        "://")[1].split("?")[0].split('/')[0].split(':')[0].lower()

    return result

###############################################################################
# An object to rule the web page (only one page)
###############################################################################
class Link(dict):

    ###########################################################################
    # The name of the link
    # @return the value
    ###########################################################################
    @property
    def name(self):
        if 'name' not in self:
            return None
        return self['name']

    ###########################################################################
    # The name of the link
    # @param value The value to set
    ###########################################################################
    @name.setter
    def name(self, value):
        self['name'] = value
        if value is None:
            del self['name']

    ###########################################################################
    # The name of the link
    # @return the value
    ###########################################################################
    @property
    def label(self):
        if 'name' not in self:
            return None
        return self['name']

    ###########################################################################
    # The name of the link
    # @param value The value to set
    ###########################################################################
    @label.setter
    def label(self, value):
        self['name'] = value
        if value is None:
            del self['name']

    ###########################################################################
    # The url of the link
    # @return the value
    ###########################################################################
    @property
    def url(self):
        if 'url' not in self:
            return None
        return self['url']

    ###########################################################################
    # The url of the link
    # @param value The value to set
    ###########################################################################
    @url.setter
    def url(self, value):
        self['url'] = value
        if value is None:
            del self['url']

    ###########################################################################
    # The title of the link
    # @return the value
    ###########################################################################
    @property
    def title(self):
        if 'title' not in self:
            return None
        return self['title']

    ###########################################################################
    # The title of the link
    # @param value The value to set
    ###########################################################################
    @title.setter
    def urtitlel(self, value):
        self['title'] = value
        if value is None:
            del self['title']

    ###########################################################################
    # __str__ is a built-in function that computes the "informal"
    # string reputation of an object
    # __str__ goal is to be readable
    ###########################################################################
    def __str__(self):
        result = "Link name='%s' title='%s'\n" % (self.name, self.title)
        result += "      url=%s\n" % (self.url)

        return result


###############################################################################
# Find the markdown links contained in the text
# This function return a dict with the links.
#
# @param text the text to parse
# @param previous_links the previous links to add to the result
# @return a dict with the links
###############################################################################
def search_link_in_md_text(text, previous_links=None):
    md_link_re = re.compile(
        r"""(\[(?P<name>[^]]*)]\s*"""
        r"""\(\s*(?P<url>([^()]+?))\s*(?:\"(?P<title>[\s\S]*?)\")*\))""")
    md_link_ref_name_re = re.compile(
        r"""\[(?P<name>.*?)\]\s*?\[(?P<id_link>.*?)\]""")
    md_link_ref_url_re = re.compile(
        r"""\[(?P<id_link>\S*?)\]:\s*"""
        r"""(?P<url>\S+)\s*(?:\"(?P<title>[\s\S]*?)\")?""")
    # md_link_ref_re = re.compile(r"""\[(?P<name>.*?)\].*\[(.*?)\]"""
    # r"""[\s\S]*?\[(.*)\][\s\S]*?:\s*?(?P<url>.*?)\"(?P<title>[\s\S]*?)\"""")
    # <-- global RE but broken with Python

    result = []
    if previous_links is not None:
        result = previous_links

    for match in re.finditer(md_link_re, text):
        result.append({'name': match.group('name'),
                       'url': match.group('url'),
                       'title': match.group('title')})

    links_by_ref = {}
    for match in re.finditer(md_link_ref_name_re, text):
        links_by_ref[match.group('id_link')] = {
            'name': match.group('name'), 'url': None}

    for match in re.finditer(md_link_ref_url_re, text):
        id_link = match.group('id_link')
        if links_by_ref.get(id_link) is not None:
            links_by_ref[id_link]['url'] = match.group('url')
            links_by_ref[id_link]['title'] = match.group('title')
            result.append(links_by_ref[id_link])

    return result

#  def create_test_search_link_in_md_text():
    #  test_list=[]
    #  test_list.append("""[label]    (#metadonneelabel) cqsc qsc qs""")
    #  test_list.append("""[Professeur de danse](www.guichet.fr)""")
    #  test_list.append("""[Professeur de danse]"""
    #                   """(www.guichet.fr "avec un title")""")
    #  test_list.append("""[ref1][id1] reference-style link.
#  [id1]: http://example.com/id1
#  "un title
#  sur
#  plusieurs lignes" """)

    #  key_list = ["name", "url", "title"]

    #  for t in test_list:
    #  result = search_link_in_md_text(t)
    #  print('\t# ------')
    #  print('\tresult = search_link_in_md_text("""%s""")'%(t))
    #  print('\tassert(len(result)==%d)'%(len(result)))
    #  for i in range(0,len(result)):
    #  for k in key_list:
    #  print('\tassert(result[%d]["%s"]==%s)'%(i,
    #        k,'"""%s"""'%result[i][k] if result[i][k]  else "None"))


def test_search_link_in_md_text_1():
    # ------
    result = search_link_in_md_text(
        """[label]    (#metadonneelabel) cqsc qsc qs""")
    assert len(result) == 1
    assert result[0]["name"] == """label"""
    assert result[0]["url"] == """#metadonneelabel"""
    assert result[0]["title"] is None
    # ------
    result = search_link_in_md_text(
        """[Professeur de danse](www.guichet.fr)""")
    assert len(result) == 1
    assert result[0]["name"] == """Professeur de danse"""
    assert result[0]["url"] == """www.guichet.fr"""
    assert result[0]["title"] is None
    # ------
    result = search_link_in_md_text(
        """[Professeur de danse](www.guichet.fr "avec un title")""")
    assert len(result) == 1
    assert result[0]["name"] == """Professeur de danse"""
    assert result[0]["url"] == """www.guichet.fr"""
    assert result[0]["title"] == """avec un title"""
    # ------
    result = search_link_in_md_text("""[ref1][id1] reference-style link.
[id1]: http://example.com/id1  "un title sur
 plusieurs lignes" """)
    assert len(result) == 1
    assert result[0]["name"] == """ref1"""
    assert result[0]["url"] == """http://example.com/id1"""
    assert result[0]["title"] == """un title sur
 plusieurs lignes"""

###############################################################################
# create a json
###############################################################################
def search_link_in_md_text_json(text_md):
    links = search_link_in_md_text(text_md)
    return json.dumps(links, sort_keys=True, indent=2)

###############################################################################
# Find the markdown links contained in the file
# This function return a dict with the links.
#
# @param filename the filename of the file to parse
# @param filename_ext the new extension with a dot (ext = '.md')
# @param encoding the encoding of the file
# @param previous_links all previous links
# @return a dict with the links
###############################################################################
def search_link_in_md_file(filename, filename_ext=".md",
                           encoding="utf-8", previous_links=None):
    logging.debug('Search link in the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename, encoding=encoding)

    # Analyze
    result = search_link_in_md_text(text, previous_links=previous_links)

    return result

###############################################################################
# Replace the links in an MD text.
#
# A link is a dict caracterized by 3 entries :
#    a_link_example = {'name' : 'my_name',
#                      'name_to_replace' : 'my_old_name',  <-- option
#                       'url' : 'www.my_url.fr',
#                       'title' : 'my title'}              <-- option
#
# @param text_md the markdown text
# @param links the new links (or a single link)
# @return the string
###############################################################################
def update_links_in_md_text(text_md, links):
    links_to_update = links
    if not isinstance(links, list):
        links_to_update = [links]

    result = text_md
    for link in links_to_update:
        name_to_replace = link['name']
        if 'name_to_replace' in link:
            name_to_replace = link['name_to_replace']

        result = update_link_in_md_text(result, name_to_replace, link)

    return result

###############################################################################
# Change the base path for the relative path link
#
# @param text_md the markdown text
# @param mv_base_path
# @return the md text
###############################################################################
def move_base_path_in_md_text(text_md, mv_base_path):
    links = search_link_in_md_text(text_md)
    links_replace = []
    for link in links:
        if not is_external_link(link['url']):
            new_link = copy.deepcopy(link)
            new_link['url'] = os.path.join(mv_base_path, new_link['url'])
            new_link['url'] = os.path.normpath(new_link['url'])
            links_replace.append((link, new_link))

    return update_links_from_old_link(text_md, links_replace)


###############################################################################
# Replace the link with the name as a pivot
#
# A link is a dict caracterized by 3 entries :
#    a_link_example = {'name' : 'my_name',
#                       'url' : 'www.my_url.fr',
#                       'title' : 'my title'}
#
# @param text_md the markdown text
# @param name the name of the link
# @param new_link the new link
# @return the string
###############################################################################
def update_link_in_md_text(text_md, name, new_link):

    # replace simple link
    result = re.sub(
        r"""(\[%s]\s*\(\s*(?P<url>([^()]+?))"""
        r"""\s*(?:\"(?P<title>[\s\S]*?)\")*\))""" % (re.escape(name)),
        lambda m: sub_string_link_md(m.group(), new_link), text_md)

    # replace reference
    match_var = re.search(
        r"""\[(%s)\]\s*?\[(?P<id_link>.*?)\]""" % (re.escape(name)), text_md)

    if not match_var:
        return result

    id_link = match_var.group('id_link')
    new_link['id_link'] = id_link

    # sub le nom
    result = re.sub(
        r"""\[(%s)\]\s*?\[(?P<id_link>.*?)\]""" % (re.escape(name)),
        lambda m: sub_string_name_by_ref_md(m.group(), new_link), result)

    result = re.sub(
        r"""\[%s]:\s*(?P<url>\S+)\s*(?:\"(?P<title>[\s\S]*?)\")?""" %
        (re.escape(id_link)),
        lambda m: sub_string_link_by_ref_md(m.group(), new_link), result)

    return result

###############################################################################
# Replace the oldlink with the new one
#
# A link is a dict caracterized by 3 entries :
#    a_link_example = {'name' : 'my_name',
#                       'url' : 'www.my_url.fr',
#                       'title' : 'my title'}
#
# @param text_md the markdown text
# @param old_link the old link
# @param new_link the new link
# @return the string
###############################################################################
def update_link_from_old_link(text_md, old_link, new_link):

    name = old_link['name']
    url = old_link['url']
    new_text_md = re.sub(
        r"""(\[%s]\s*\(\s*(%s([^()]*?))\s*(?:\"(?P<title>[\s\S]*?)\")*\))""" %
        (re.escape(name), re.escape(url)), lambda m: sub_string_link_md(
            m.group(), new_link), text_md)
    if new_text_md == text_md:
        match_var = re.search(
            r"""\[(%s)\]\s*?\[(?P<id_link>.*?)\]""" % (re.escape(name)),
            text_md)
        if not match_var:
            return new_text_md
        id_link = match_var.group('id_link')
        new_link['id_link'] = id_link
        # sub le nom
        new_text_md = re.sub(r"""\[(%s)\]\s*?\[(?P<id_link>.*?)\]"""
                             % (re.escape(name)),
                             lambda m: sub_string_name_by_ref_md(m.group(),
                                                                 new_link),
                             new_text_md)
        new_text_md = re.sub(r"""\[%s]:\s*(%s)\s*(?:\""""
                             r"""(?P<title>[\s\S]*?)\")?"""
                             % (re.escape(id_link), re.escape(url)), lambda m:
                             sub_string_link_by_ref_md(m.group(), new_link),
                             new_text_md)
    return new_text_md

###############################################################################
# Replace the oldlink with the new one
#
# A link is a dict caracterized by 3 entries :
#    a_link_example = {'name' : 'my_name',
#                       'url' : 'www.my_url.fr',
#                       'title' : 'my title'}
#
# @param text_md the markdown text
# @param links_couple the old link, the new link couple
# @return the string
###############################################################################
def update_links_from_old_link(text_md, links_couple):
    result = text_md
    for link_couple in links_couple:
        result = update_link_from_old_link(result,
                                           link_couple[0], link_couple[1])

    return result

###############################################################################
# Create a string link
#
# @param unused_dummy unused paramter
# @param link the link with key 'url', 'title' and 'name'
# @return the string
###############################################################################
def sub_string_link_md(unused_dummy, link):
    name = link['name']
    new_url = link['url']
    new_title = ""

    if 'title' in link and link['title'] is not None:
        new_title = ' \"%s\"' % link['title']

    return "[%s](%s%s)" % (name, new_url, new_title)


###############################################################################
# Create a string with a reference link
#
# @param unused_dummy unused paramter
# @param link the link with key 'url', 'title' and 'id_link'
# @return the string
###############################################################################
def sub_string_link_by_ref_md(unused_dummy, link):
    id_link = ""
    new_title = ""
    new_url = link['url']

    if 'id_link' in link and link['id_link'] is not None:
        id_link = link['id_link']
    if 'title' in link and link['title'] is not None:
        new_title = ' \"%s\"' % link['title']

    return "[%s]: %s%s\n" % (id_link, new_url, new_title)


###############################################################################
# Create a sub string with a reference
#
# @param unused_dummy unused paramter
# @param link the link with key 'name' and 'id_link'
# @return the string
###############################################################################
def sub_string_name_by_ref_md(unused_dummy, link):
    return "[%s][%s]" % (link['name'], link['id_link'])


###############################################################################
# Test the link method
###############################################################################
def test_replace_link_in_md_text():
    # ------
    new_link = {'name': 'scnge', 'url': 'www.guichet-entreprises.fr',
                'title': 'le site du guichet'}

    result = update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec un """
        """title à remplacer également") la fin du texte""",
        new_link)
    assert result == """du texte et un lien : [scnge](""" \
        """www.guichet-entreprises.fr "le site """ \
        """du guichet") la fin du texte""" \

    list_new_link = [new_link]

    result = update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec un """
        """title à remplacer également") la fin du texte""",
        list_new_link)
    assert result == """du texte et un lien : [scnge](""" \
        """www.guichet-entreprises.fr "le site """ \
        """du guichet") la fin du texte""" \

    new_link = {'name': 'scnge', 'url': 'www.guichet-entreprises.fr'}
    result = update_links_in_md_text(
        """du texte et un lien : [scnge](mon_lien_à_remplacer "avec un """
        """title à remplacer également") la fin du texte""", new_link)
    assert result == """du texte et un lien : [scnge]""" \
        """(www.guichet-entreprises.fr) la fin du texte"""

    new_link = {'name_to_replace': 'scnge',
                'name': 'Guichet',
                'url': 'www.guichet-entreprises.fr',
                'title': 'le site du guichet'}
    result = update_links_in_md_text(
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
    result = update_links_in_md_text(
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
    result = update_links_in_md_text(
        """du texte et un lien : [ref1][id1] reference-style link. """
        """[id1]: http://example.com/id1
la fin du texte""", new_link)

    assert result == """du texte et un lien : [ref1][id1] """ \
        """reference-style link. [id1]: www.guichet-entreprises.fr "un title"
la fin du texte"""

    new_link = {'name_to_replace': 'scnge',
                'name': 'le guichet',
                'url': 'www.guichet-entreprises.fr', 'title': "un title"}
    result = update_links_in_md_text(
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
    result = update_links_from_old_link(
        """du texte et un lien : [le gip guichet?]"""
        """(www.gip-entreprises.fr "le """
        """GIP") la fin du texte[au autre lien](www.gle.fr)""",
        [(old_link1, new_link1), (old_link2, new_link2)])
    assert result == """du texte et un lien : """ \
        """[le guichet nouveau et arrivé](""" \
        """www.guichet-entreprises.fr "le site """ \
        """du guichet") la fin du texte[GOOGLE!](www.google.fr)""" \

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

    __launch_test()
    # create_test_search_link_in_md_text()
    # test_search_link_in_md_text_1()
    test_replace_link_in_md_text()
    # links = search_link_in_md_file("./test-md/SearchLinks/testLinks.md")
    # for link in links:
    #   print(link)
    #   create_test_set_correct_path()
    #   create_test_check_folder()
    #   create_test_get_valid_filename()
    #   create_test_get_flat_filename()

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
