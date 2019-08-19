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
# All functions To convert markdown file to pdf
#
###############################################################################

import logging
import sys
import os
import os.path
import re
import time
import shutil
import codecs
import pdfkit
import markdown as mkd
import PyPDF2

if (__package__ in [None, '']) and ('.' not in __name__):
    import common
    import instruction
    import mistunege as mistune
else:
    from . import common
    from . import instruction
    from . import mistunege as mistune


###############################################################################
# Add blank pages to the pdf to have
###############################################################################
def check_odd_pages(filename):
    filename = common.check_is_file_and_correct_path(filename,
                                                     filename_ext=".pdf")

    input_pdf = open(filename, 'rb')
    pdf = PyPDF2.PdfFileReader(input_pdf)
    num_pages = pdf.getNumPages()
    input_pdf.close()

    if num_pages % 2 == 0:
        return filename

    # add a page from the backup
    backup_filename = common.create_backup(filename)
    in_pdf = open(backup_filename, 'rb')
    pdf_init = PyPDF2.PdfFileReader(in_pdf)

    out_pdf = PyPDF2.PdfFileWriter()
    out_pdf.appendPagesFromReader(pdf_init)
    out_pdf.addBlankPage()

    out_stream = open(filename, 'wb')
    out_pdf.write(out_stream)
    out_stream.close()

    return filename

###############################################################################
# Convert md text to html
#
# @param text the markdown text
# @return the html fragment
###############################################################################
def converter_md_to_html_markdown(text):
    return mkd.markdown(text, output_format="xhtml5")


###############################################################################
# Convert md text to html
#
# @param text the markdown text
# @return the html fragment
###############################################################################
def converter_md_to_html_mistune(text):
    renderer = mistune.Renderer(use_xhtml=True)
    # use this renderer instance
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(text)


###############################################################################
# get the markdown to html converter
###############################################################################
@common.static(__converters__=None)
def get_md_to_html_converter(converter_name):

    if get_md_to_html_converter.__converters__ is None:
        get_md_to_html_converter.__converters__ = {}
        get_md_to_html_converter.__converters__['mistune'] = \
            converter_md_to_html_mistune
        get_md_to_html_converter.__converters__['markdown'] = \
            converter_md_to_html_markdown

    if converter_name not in get_md_to_html_converter.__converters__:
        logging.info('Converter %s does not exist', converter_name)
        logging.info('Converter change to classique markdown')
        converter_name = 'markdown'

    return get_md_to_html_converter.__converters__[converter_name]


###############################################################################
# Convert md file to html with a layout
#
# @param filename the filename of the markdon file
# @param layout the layout chosen
# @param filename_ext This parameter the markdown extension for the filename.
# @param encoding Encoding of the html output file.
# @param converter the html converter. a string with the name of the converter
# @param path_dest the destination folder for the html
# @return the html filename
###############################################################################
def convert_md_to_html(filename, layout="jasonm23-swiss",
                       filename_ext=".md", encoding="utf-8",
                       path_dest=None, converter=None):
    logging.info('Convert md -> html %s', filename)

    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    if path_dest is None:
        path_dest = os.path.split(os.path.abspath(filename))[0]
    path_dest = common.check_folder(path_dest)

    # Read the file
    content = common.get_file_content(filename)
    title = instruction.get_title_from_md_text(content)
    if title is None:
        title = ""

    if len(content) == 0:
        logging.error('The filename %s seem empty', filename)
        raise Exception('The filename %s seem empty' % filename)

    content = get_md_to_html_converter(converter)(content)

    # find the layout
    first_path = \
        os.path.join(os.path.dirname(os.path.realpath(__get_this_filename())))

    page_html_filename = \
        common.search_for_file("page.html",
                               [first_path, os.path.join(
                                   first_path, "lib", "pymdtools")],
                               [os.path.join("layouts", layout)], 1)

    layout_path = common.check_folder(os.path.dirname(page_html_filename))

    # Get the content
    page_html = common.get_file_content(page_html_filename)

    # parse instruction
    # list_inst = re.findall(r"{{.+}}", page_html)

    for inst in re.findall(r"{{.+}}", page_html):
        logging.debug('instruction %s', inst)
        if inst == '{{title}}':
            page_html = page_html.replace(inst, title)
        if inst == '{{~> content}}':
            page_html = page_html.replace(inst, content)
        if inst[0:7] == '{{asset':
            file_objet = inst[9:-3]
            if file_objet[0] == '/':
                file_objet = file_objet[1:]

            dst_file = common.set_correct_path(
                os.path.join(path_dest, file_objet))
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy(common.set_correct_path(os.path.join(layout_path,
                                                             "assets",
                                                             file_objet)),
                        dst_file)
            page_html = page_html.replace(inst, file_objet)

    html_filename = common.set_correct_path(os.path.join(
        path_dest, os.path.splitext(os.path.split(filename)[1])[0] + ".html"))
    logging.info('        -> html %s', html_filename)

    # save the html file
    output_file = codecs.open(html_filename, "w",
                              encoding=encoding, errors="xmlcharrefreplace")
    output_file.write(page_html)
    output_file.close()

    return html_filename

###############################################################################
# Find the wkhtmltopdf tool
#
# @return full path to the file "wkhtmltopdf.exe"
###############################################################################
def find_wk_html_to_pdf():
    logging.info('Search wkhtmltopdf')

    start_points = ["C:\\Program Files\\wkhtmltopdf",
                    "./",
                    __get_this_filename(),
                    "D:\\Program Files\\wkhtmltopdf"]

    relative_paths = ['bin',
                      'wkhtmltopdf',
                      'wkhtmltopdf/bin',
                      'software/wkhtmltopdf/bin',
                      'software/wkhtmltopdf',
                      'software/bin',
                      'software',
                      'third_party_software/wkhtmltopdf/bin',
                      'third_party_software/wkhtmltopdf',
                      'third_party_software/bin',
                      'third_party_software']

    return common.search_for_file("wkhtmltopdf.exe", start_points,
                                  relative_paths, nb_up_path=4)

###############################################################################
# Convert html file to a pdf file at the same location
#
# @return full path to the pdf file
###############################################################################
def convert_html_to_pdf(filename, filename_ext=".html"):
    logging.info('Convert html -> pdf %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    config = pdfkit.configuration(wkhtmltopdf=find_wk_html_to_pdf())

    header_text = '%s' % (os.path.splitext(os.path.basename(filename))[0])

    date_print = time.strftime("%d/%m/%Y", time.gmtime())
    options = {'header-center': header_text,
               'footer-center': 'page [page] sur [toPage]',
               'footer-font-size': '8',
               'footer-right': date_print,
               'margin-top': '20mm',
               'margin-bottom': '20mm',
               'footer-spacing': '10',
               'header-spacing': '10',
               'header-font-size': '8'}

    pdf_filename = os.path.splitext(filename)[0] + ".pdf"
    pdfkit.from_file(filename, pdf_filename,
                     options=options, configuration=config)
    logging.info('Conversion finished for %s', filename)

    return pdf_filename

###############################################################################
# Convert md file to pdf
#
# @param filename the filename of the markdon file
# @param filename_ext This parameter the markdown extension for the filename.
# @return the pdf filename
###############################################################################
def convert_md_to_pdf(filename, filename_ext=".md"):
    """
    This function take a file, load the content, create a pdf
    with the same name.

    @type filename: string
    @param filename: The name and path of the file to work with.
                     This file is supposed to be a markdown file.

    @type filename_ext: string
    @param filename_ext: This parameter the markdown extension
                         for the filename.

    @return nothing
    """
    logging.info('Convert md -> pdf %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    temp_dir = common.get_new_temp_dir()
    temp_md_filename = os.path.join(temp_dir, os.path.basename(filename))
    temp_html_filename = os.path.splitext(temp_md_filename)[0] + ".html"
    temp_pdf_filename = os.path.splitext(temp_md_filename)[0] + ".pdf"

    logging.info('Copy file to temp')
    shutil.copy(filename, temp_md_filename)
    logging.info('Convert md to html')
    convert_md_to_html(temp_md_filename, converter='mistune')
    logging.info('Convert html to pdf')
    convert_html_to_pdf(temp_html_filename)

    logging.info('Copy file from temp')
    pdf_filename = os.path.splitext(filename)[0] + ".pdf"
    shutil.copy(temp_pdf_filename, os.path.splitext(filename)[0] + ".pdf")

    # remove the temp dir
    logging.info('Remove the temp dir')
    shutil.rmtree(temp_dir)

    return pdf_filename

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
