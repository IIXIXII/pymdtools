#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# @copyright Copyright (C) Guichet Entreprises - All Rights Reserved
# 	All Rights Reserved.
# 	Unauthorized copying of this file, via any medium is strictly prohibited
# 	Dissemination of this information or reproduction of this material
# 	is strictly forbidden unless prior written permission is obtained
# 	from Guichet Entreprises.
###############################################################################

###############################################################################
# All functions To normalize a markdown file.
#
###############################################################################

import logging
import sys
import os
import os.path
import re

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
    import mistunege as mistune
    import mdrender
else:
    from . import common
    from . import mistunege as mistune
    from . import mdrender


###############################################################################
# Normalize a markdown text.
# with a double conversion, the markdown text is normalized
#
# @param text The markdown text
# @return the normalized markdown text
###############################################################################
def md_beautifier(text):
    logging.debug('Beautify a md content')

    the_renderer = mdrender.MdRenderer()
    markdown = mistune.Markdown(renderer=the_renderer)

    result = markdown(text)

    return result

###############################################################################
# Normalize a markdown text.
# with a double conversion, the markdown text is normalized
# This function take a file, load the content, create a backup (if needed)
# and do some change in the file which is supposed to be a markdown file.
# Then saved the new file with the same filename. The goal is to
# beautify the markdown file.
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param backup_option This parameter is set to true by default.
#                      If the backup option is set,
#                             then a file named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @return the filename normalized
###############################################################################
def md_file_beautifier(filename, backup_option=True, filename_ext=".md"):
    """
    This function take a file, load the content, create a backup (if needed)
    and do some change in the file which is supposed to be a markdown file.
    Then saved the new file with the same filename. The goal is to beautify
    the markdown file.

    @type filename: string
    @param filename: The name and path of the file to work with. This file is
                     supposed to be a markdown file.

    @type backup_option: boolean
    @param backup_option: This parameter is set to true by default.
                          If the backup option is set,
                          then a file named filename.bak will be created.

    @type filename_ext: string
    @param filename_ext: This parameter the markdown extension
                         for the filename.

    @return nothing
    """
    logging.debug('Beautify the file %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename)
    if len(text) == 0:
        logging.error('The fielname %s seem empty', filename)
        raise Exception('The fielname %s seem empty' % filename)

    # Create Backup
    if backup_option:
        common.create_backup(filename)

    # Change inside
    text = md_beautifier(text)

    # Save the file
    os.remove(filename)
    common.set_file_content(filename, text, encoding="utf-8")

###############################################################################
# Correct a markdown text.
#
# @param text The markdown text
# @return the normalized markdown text
###############################################################################
def __correct_markdown_text_repl2(text):
    (text, unused_) = re.subn(r"\r\n(\s*)-\s(.*)\r\n",
                              r"\r\n - \2", text)
    (text, unused_) = re.subn(r":(\s*)\r\n - ",
                              r":\r\n\r\n - ", text)
    (text, unused_) = re.subn(r"\r\n - (.*)\.\r\n",
                              r"\r\n - \1.\r\n\r\n", text)
    (text, unused_) = re.subn(r"##\s*1°(.*)\r\n(-+)\r\n",
                              r"1°\1\r\n\2\r\n", text)
    (text, unused_) = re.subn(r"##\s*2°(.*)\r\n(-+)\r\n",
                              r"2°\1\r\n\2\r\n", text)
    (text, unused_) = re.subn(r"##\s*3°(.*)\r\n(-+)\r\n",
                              r"3°\1\r\n\2\r\n", text)
    (text, unused_) = re.subn(r"##\s*4°(.*)\r\n(-+)\r\n",
                              r"4°\1\r\n\2\r\n", text)
    (text, unused_) = re.subn(r"##\s*5°(.*)\r\n(-+)\r\n",
                              r"5°\1\r\n\2\r\n", text)
    (text, unused_) = re.subn(r"##\s*6°(.*)\r\n(-+)\r\n",
                              r"6°\1\r\n\2\r\n", text)
    (text, unused_) = re.subn(r"##\s*7°(.*)\r\n(-+)\r\n",
                              r"7°\1\r\n\2\r\n", text)

    (text, unused_) = re.subn(
        r"\r\n#(#*)(.*)[*][*]\s*\r\n", r"\r\n#\1\2\r\n\r\n", text)

    text = text.replace(u" :  * ", u" :\r\n  * ")
    text = text.replace(u"\r\n  * ", u"\r\n    + ")
    (text, unused_) = re.subn(r"\r\n[*] ([^*\r]*)\r\n", r"\r\n - \1\r\n", text)
    text = text.replace("""[35\r\nheures](https://www.legifrance.gouv.fr/"""
                        """affichTexteArticle.do;jsessionid="""
                        """426183422AEAB5864A868A3038C21D37.tplgfr22s_2?"""
                        """idArticle=JORFARTI000034104623&cidTexte="""
                        """JORFTEXT000034104616&dateTexte="""
                        """29990101&categorieLien=id)""", "35 heures")

    (text, unused_) = re.subn(
        r"\r\n - ([^\r]*)\.\s*\r\n([^\r])",
        r"\r\n - \1.\r\n\r\n\2", text)

    text = text.replace(u" ;  - ", u" ;\r\n - ")

    (text, unused_) = re.subn(
        r"\r\n[*][*]([^*\r]*)\s*:\s*\r\n", r"\r\n**\1** :\r\n", text)

    (text, unused_) = re.subn(
        r"#\s*([1-9])°(.*)\r\n(-+)\r\n", r"\1°\2\r\n\3\r\n", text)
    (text, unused_) = re.subn(
        r"#\s*([1-9])°(.*)\r\n\r\n",
        r"\1°\2\r\n-----------------\r\n\r\n", text)
    (text, unused_) = re.subn(
        r"\r\n#\s*([1-9])°(.*)\r\n(-+)\r\n", r"\r\n\1°\2\r\n\3\r\n", text)
    (text, unused_) = re.subn(
        r"([a-z])\.(.*)\r\n(-+)\r\n", r"### \1.\2\r\n\r\n", text)

    text = text.replace(u"\r\nBon à savoir :", u"\r\n**Bon à savoir** :")
    text = text.replace(u" **Bon à savoir** :", u"**Bon à savoir** :")

    text = text.replace(u"## Définition de l'activité\r\n\r\n",
                        u'1°. Définition de l’activité'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u"# Définition de l'activité\r\n\r\n",
                        u'1°. Définition de l’activité'
                        '\r\n------------------------\r\n\r\n')

    text = text.replace(u"**Coûts associés à la qualification",
                        u"**Coûts associés à la qualification**")
    text = text.replace(u"**Coûts associés à la qualification",
                        u"**Coûts associés à la qualification**")
    text = text.replace(u"**Centre d’assistance Français",
                        u"**Centre d’assistance Français**")
    text = text.replace(u"**Diplôme de géomètre-expert foncier délivré "
                        "par le gouvernement (DPLG)",
                        u"**Diplôme de géomètre-expert foncier délivré "
                        "par le gouvernement (DPLG)**")

    def change_special(match):
        return "\r\n###### " + match.group(2) + "\r\n" +\
            match.group(3).upper() + match.group(4) + "\r\n"

    (text, unused_) = re.subn(
        r"(\r\n|\n)\*\*([^\r\*]*)\*\*\s:\s([^\r])"
        r"([^\r\*]*)([\*]*)[ ]*(\r\n|\n)",
        change_special, text)

    (text, unused_) = re.subn(
        r"\.[ ]*(\r\n|\n)",
        r".\r\n", text)
    (text, unused_) = re.subn(
        r"\s([:;])[ ]*(\r\n|\n)",
        u"\u00A0\\1\r\n", text)
    (text, unused_) = re.subn(
        r"\s([:;])",
        u"\u00A0\\1", text)

    return text


###############################################################################
# Correct a markdown text.
#
# @param text The markdown text
# @return the normalized markdown text
###############################################################################
def __correct_markdown_text_repl(text):
    text = text.replace(u"****", u"**")
    text = text.replace(u"#### **", u"#### ")
    text = text.replace(u"### **", u"### ")
    text = text.replace(u"## **", u"## ")
    text = text.replace(u"# **", u"# ")
    text = text.replace(u"**Coût :", u"**Coût** :")
    text = text.replace(u"**Coût* :", u"**Coût** :")
    text = text.replace(u"\r\n*Coût :", u"\r\n**Coût** :")
    text = text.replace(u"\r\nCoût :", u"\r\n**Coût** :")
    text = text.replace(u"\r\nDélais :", u"\r\n**Délais** :")
    text = text.replace(u"\r\n**Délai**:", u"\r\n**Délai** :")
    text = text.replace(u"\r\n**Délais\r\n", u"\r\n**Délais** :\r\n")

    text = text.replace(u"#### ###", u"#### ")
    text = text.replace(u"#### ##", u"#### ")
    text = text.replace(u"#### #", u"#### ")
    text = text.replace(u"#### #", u"#### ")
    text = text.replace(u"### Pour aller plus loin",
                        u"*Pour aller plus loin*")
    text = text.replace(u"Pour aller plus loin",
                        u"*Pour aller plus loin*")
    text = text.replace(u"**Pour aller plus loin**",
                        u"*Pour aller plus loin*")
    text = text.replace(u"*Pour aller plus loin*",
                        u"\r\n*Pour aller plus loin*")
    text = text.replace(u"\r\n\r\n\r\n*Pour aller plus loin*",
                        u"\r\n\r\n*Pour aller plus loin*")
    text = text.replace(u"\\>", u"")
    text = text.replace(u"**À savoir :", u"**À savoir** :")
    text = text.replace(u"**À savoir* :", u"**À savoir** :")
    text = text.replace(u"fr)*.\r\n", u"fr).\r\n")

    text = text.replace(u"\r\nBon à savoir :", u"**Bon à savoir** :")
    text = text.replace(u"**Bon à savoir :", u"**Bon à savoir** :")
    text = text.replace(u"**Bon à savoir :", u"**Bon à savoir** :")
    text = text.replace(u"** Bon à savoir :", u"**Bon à savoir** :")
    text = text.replace(u"**Bon à savoir* :", u"**Bon à savoir** :")
    text = text.replace(u"**Bon à savoir** :**", u"**Bon à savoir** :")
    text = text.replace(u"** Bon à savoir :", u"**Bon à savoir** :")

    text = text.replace(u"1°. Définition de l’activité\r\n\r\n",
                        u'1°. Définition de l’activité'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u"2°. Qualifications professionnelles\r\n\r\n",
                        u'2°. Qualifications professionnelles'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u"2°. Qualification professionnelle\r\n\r\n",
                        u'2°. Qualification professionnelle'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u"3°. Conditions d’honorabilité\r\n\r\n",
                        u'3°. Conditions d’honorabilité'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u'5°. Démarches et formalités de reconnaissance '
                        'de qualifications\r\n\r\n',
                        u'5°. Démarches et formalités de reconnaissance '
                        'de qualifications'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u'5°. Démarche et formalités de reconnaissance '
                        'de qualification\r\n\r\n',
                        u'5°. Démarche et formalités de reconnaissance '
                        'de qualification'
                        '\r\n------------------------\r\n\r\n')
    text = text.replace(u'5°. Démarche et formalités de reconnaissance '
                        'de qualifications\r\n\r\n',
                        u'5°. Démarche et formalités de reconnaissance '
                        'de qualifications'
                        '\r\n------------------------\r\n\r\n')

    text = text.replace("--------------------------\r\n---", "---")

    text = text.replace(u"**Prérogatives\r\n", u"**Prérogatives\r\n")

    text = text.replace(u"•", u"    -")
    text = text.replace(u"~~,~~", u",")

    text = text.replace(u"**Prérogatives", u"**Prérogatives**")
    text = text.replace(u"**Stage de recyclage\r\n",
                        u"**Stage de recyclage**\r\n")
    text = text.replace(u"**Pièces justificatives : \r\n",
                        u"**Pièces justificatives** : \r\n")
    text = text.replace(u"**Autorité compétente\r\n",
                        u"**Autorité compétente**\r\n")

    return text

###############################################################################
# Correct a markdown text.
# List the actions done on the markdown file :
# 		- remove all backslach "\\"
# 		- replace "### ###" with "###"
# 		- replace "#### ####" with "####"
# 		- replace "**#" with "**"
# 		- replace "![" with "["
#
# @param text The markdown text
# @return the normalized markdown text
###############################################################################
def correct_markdown_text(text):
    if text.startswith(u'\ufeff'):
        text = text[1:]
    text = text.replace(u"•  ", u" - ")
    text = text.replace(u"\\", u"")
    text = text.replace(u"****", u"**")
    text = text.replace(u"***", u"**")
    text = text.replace(u"### ###", u"### ")
    text = text.replace(u"#### ####", u"#### ")
    text = text.replace(u"#### ###", u"#### ")
    text = text.replace(u"#### ##", u"#### ")
    text = text.replace(u"#### #", u"#### ")
    text = text.replace(u"**#", u"**")
    text = text.replace(u"![", u"[")

    list_filters_regs = [
        [True, r'- Contrôle des guillemets ...: ', r'"(.*)"', r"«\1»"],
        [False, r'- Contrôle structure traitée ...: ', r"\\\\\#", r"#"],
        [True, r'- Backslash traités ............: ', r"\\\\", r""],
        [True, r'- Liens ![ traités .............: ', r"\!\s?\[", r"["],
        [True, r'- Balises **#...* traitées .....: ',
         r"\*\*\#\s*\**\r\n", "\r\n\r\n"],
        [True, r'- Balises #* traitées ..........: ', r"\#\*+", r"#"],
        [True, r'- Balises *# traitées ..........: ', r"\*+\#", r"#"],
        [True, r'- Balises (* traitées ..........: ', r"\(\s?\*", r"("],
        [True, r'- Balises *) traitées ..........: ', r"\*\s?\)", r")"],
        [True, r'- Balises **=** traitées .......: ',
         r"\r\n\*+\=\*+\r\n", "\r\n"],
        [False, r'- Balises #...* traitées .......: ', r"\*+\r\n", r"\r\n"],
        [True, r'- Balises ----- traitées .......: ',
         r"4°. Obligation de déclaration \((.*)\)\r\n",
         r'4°. Obligation de déclaration (\1)'
         r'\r\n--------------------------\r\n']
    ]

    for list_regex in list_filters_regs:
        if list_regex[0]:
            obj_line = re.subn(list_regex[2], list_regex[3], text)
            text = obj_line[0]
            logging.debug(str(list_regex[1]) + str(obj_line[1]))

    text = text.replace(u"&gt;", u"\\>")
    text = text.replace(u"\r\n=\r\n", u"==================\r\n")

    if text[0:2] == "**":
        text = text[2:]

    text = __correct_markdown_text_repl(text)

    for num_title in range(0, 10):
        text = text.replace(u"##%d°" % num_title, u"%d°" % num_title)
        text = text.replace(u"#%d°" % num_title, u"%d°" % num_title)
        text = text.replace(u"**%d°" % num_title, u"%d°" % num_title)
        text = text.replace(u"*%d°" % num_title, u"%d°" % num_title)

    for num in [chr(x) for x in range(ord('a'), ord('z'))]:
        text = text.replace(u"# **%s." % num, u"# %s." % num)
        text = text.replace(u"\r\n##%s." % num, u"\r\n### %s." % num)
        text = text.replace(u"\r\n## %s." % num, u"\r\n### %s." % num)

    (text, unused_) = re.subn(r"\r\n#([A-Za-z])", r"\r\n# \1", text)
    (text, unused_) = re.subn(r"\r\n##([A-Za-z])", r"\r\n## \1", text)
    (text, unused_) = re.subn(r"\r\n###([A-Za-z])", r"\r\n### \1", text)
    (text, unused_) = re.subn(r"\r\n####([A-Za-z])", r"\r\n#### \1", text)
    (text, unused_) = re.subn(r"\r\n#####([A-Za-z])", r"\r\n##### \1", text)
    (text, unused_) = re.subn(r"\r\n######([A-Za-z])", r"\r\n###### \1", text)
    (text, unused_) = re.subn(
        r"\r\n([#]+)([^*\n\r]*)\*\*\r\n", r"\r\n\1\2\r\n", text)

    md_link_re = re.compile(
        r'(\[(?P<name>[^]]+)]\(\s*\[\*(?P<name2>[^]]+)]'
        r'\(\s*(?P<link>([^()]+))\s*\)\))')

    for match in re.findall(md_link_re, text):
        # Change text like this
        #  [plus de précisions](
        #        [*http://foromes.calendrier.sports.gouv.fr/#/formation*]
        #        (http://foromes.calendrier.sports.gouv.fr/#/formation))
        #  ---> [plus de précisions]
        #            (http://foromes.calendrier.sports.gouv.fr/#/formation)
        text = text.replace(match[0], "[%s](%s)" % (match[1], match[3]))
        #  print(m[0])

    (text, unused_) = re.subn(r"([^\n\r])[ ]+", r"\1 ", text)
    text = text.replace(u"\n  -", u"\n    -")

    text = text.replace(u"### 2°. Conditions d'installation\r\n\r\n",
                        u"2°. Conditions d'installation"
                        "\r\n------------------------\r\n\r\n")

    text = text.replace(u"À savoir :",
                        u"**À savoir** :")
    text = text.replace(u"À noter :",
                        u"**À noter** :")

    text = text.replace(u"**Conditions d'exercice des activités "
                        "d'entremise et de gestion immobilières",
                        u"**Conditions d'exercice des activités "
                        "d'entremise et de gestion immobilières**")

    text = text.replace(u"**Obligation de respecter les règles "
                        "déontologiques de la profession",
                        u"**Obligation de respecter les règles "
                        "déontologiques de la profession**")

    text = text.replace(u"**Obligation de souscrire une assurance "
                        "de responsabilité civile",
                        u"**Obligation de souscrire une assurance "
                        "de responsabilité civile**")

    text = __correct_markdown_text_repl2(text)
    return text

###############################################################################
# Correct a markdown text.
# List the actions done on the markdown file :
# 		- remove all backslach "\\"
# 		- replace "### ###" with "###"
# 		- replace "#### ####" with "####"
# 		- replace "**#" with "**"
# 		- replace "![" with "["
#
# @param filename The name and path of the file to work with.
#                 This file is supposed to be a markdown file.
# @param backup_option This parameter is set to true by default.
#                      If the backup option is set, then a file
#                      named filename.bak will be created.
# @param filename_ext This parameter the markdown extension for the filename.
# @param encoding the encoding of the file
# @return the normalized markdown text
###############################################################################
def correct_markdown_file(filename,
                          backup_option=True,
                          filename_ext=".md",
                          encoding="utf-8"):
    """
    This function take a file, load the content, create a backup (if needed)
    and do some change in the file which is supposed to be a markdown file.
    Then saved the new file with the same filename. The main goal is
    to correct the markdown file.

    List the actions done on the markdown file :
            - remove all backslach "\\"
            - replace "### ###" with "###"
            - replace "#### ####" with "####"
            - replace "**#" with "**"
            - replace "![" with "["


    @type filename: string
    @param filename: The name and path of the file to work with.
                     This file is supposed to be a markdown file.

    @type backup_option: boolean
    @param backup_option: This parameter is set to true by default.
                          If the backup option is set, then a file
                          named filename.bak will be created.

    @type filename_ext: string
    @param filename_ext: This parameter the markdown
                         extension for the filename.

    @return nothing
    """
    logging.info('Try to correct the file %s', (filename))
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    # Read the file
    text = common.get_file_content(filename, encoding=encoding)

    # Create Backup
    if backup_option:
        common.create_backup(filename)
    os.remove(filename)

    # Change inside
    text = correct_markdown_text(text)

    # Save the file
    common.set_file_content(filename, text, encoding="utf-8")

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

    #  __launch_test()

    test_folder = os.path.join(get_local_folder(), "test-md/md_beautifier/")
    the_file = 'test-004'
    the_file = 'DS004 Boucher'
    the_file = 'DS018 Restaurant traditionnel'

    import shutil
    shutil.copyfile(os.path.join(test_folder, the_file) + ".md",
                    os.path.join(test_folder, the_file) + "__B.md")
    md_file_beautifier(
        os.path.join(test_folder, the_file) + "__B.md", backup_option=False)
    shutil.copyfile(os.path.join(test_folder, the_file) + "__B.md",
                    os.path.join(test_folder, the_file) + "__C.md")
    md_file_beautifier(
        os.path.join(test_folder, the_file) + "__C.md", backup_option=False)

    # shutil.copyfile("./test-md/md_correct/QP 001.md", "./test-md/test.md")
    # correct_markdown_file("./test-md/test.md", backup_option = True)
    # ~ correct_markdown_file("./test-md/test.md", backup_option = True)
    # ~ correct_markdown_file("./test-md/test.md", backup_option = True)
    # ~ correct_markdown_file("./test-md/test.md", backup_option = True)

    #  correct_markdown_file("./test-md/test.md", backup_option = False)
    #  md_file_beautifier("./test-md/test.md", backup_option = False)
    #  md_file_beautifier("./test-md/test.md", backup_option = False)
    #  md_file_beautifier("./test-md/test.md", backup_option = False)
    #  md_file_beautifier("./test-md/test.md", backup_option = False)

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
