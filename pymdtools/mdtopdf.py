#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================


# -----------------------------------------------------------------------------
# All functions To convert markdown file to pdf
#
# -----------------------------------------------------------------------------

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

from . import common
from . import instruction
from . import mistunege as mistune


# -----------------------------------------------------------------------------
# Add blank pages to the pdf to have
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Convert md text to html
#
# @param text the markdown text
# @return the html fragment
# -----------------------------------------------------------------------------
def converter_md_to_html_markdown(text):
    return mkd.markdown(text, output_format="xhtml5")


# -----------------------------------------------------------------------------
# Convert md text to html
#
# @param text the markdown text
# @return the html fragment
# -----------------------------------------------------------------------------
def converter_md_to_html_mistune(text):
    renderer = mistune.Renderer(use_xhtml=True)
    # use this renderer instance
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(text)


# -----------------------------------------------------------------------------
# get the markdown to html converter
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Convert md file to html with a layout
#
# @param filename the filename of the markdon file
# @param layout the layout chosen
# @param filename_ext This parameter the markdown extension for the filename.
# @param encoding Encoding of the html output file.
# @param converter the html converter. a string with the name of the converter
# @param path_dest the destination folder for the html
# @return the html filename
# -----------------------------------------------------------------------------
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
    content_vars = instruction.get_vars_from_md_text(content)
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
        elif inst == '{{~> content}}':
            page_html = page_html.replace(inst, content)
        elif len(inst) > 6 and inst[0:7] == '{{asset':
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
        elif inst[2:-2] in content_vars:
            page_html = page_html.replace(inst, content_vars[inst[2:-2]])

    html_filename = common.set_correct_path(os.path.join(
        path_dest, os.path.splitext(os.path.split(filename)[1])[0] + ".html"))
    logging.info('        -> html %s', html_filename)

    # save the html file
    output_file = codecs.open(html_filename, "w",
                              encoding=encoding, errors="xmlcharrefreplace")
    output_file.write(page_html)
    output_file.close()

    return html_filename

# -----------------------------------------------------------------------------
# Find the wkhtmltopdf tool
#
# @return full path to the file "wkhtmltopdf.exe"
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Convert html file to a pdf file at the same location
#
# @return full path to the pdf file
# -----------------------------------------------------------------------------
def convert_html_to_pdf(filename, filename_ext=".html", **kwargs):
    logging.info('Convert html -> pdf %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    config = pdfkit.configuration(wkhtmltopdf=find_wk_html_to_pdf())

    if 'title' in kwargs and kwargs['title'] is not None:
        header_text = kwargs['title']
    else:
        header_text = '%s' % (os.path.splitext(os.path.basename(filename))[0])

    date_print = time.strftime("%d/%m/%Y", time.gmtime())
    options = {
        'header-center': header_text,
        'footer-center': 'page [page] sur [toPage]',
        'footer-font-size': '8',
        'footer-right': date_print,
        'margin-top': '20mm',
        'margin-bottom': '20mm',
        'footer-spacing': '10',
        'header-spacing': '10',
        'header-font-size': '8',
        'quiet': '',
    }

    pdf_filename = os.path.splitext(filename)[0] + ".pdf"
    pdfkit.from_file(filename, pdf_filename,
                     options=options, configuration=config)
    logging.info('Conversion finished for %s', filename)

    return pdf_filename

# -----------------------------------------------------------------------------
# Add features to the pdf
#
# @param filename the filename of the pdf
# @param filename_ext This parameter the pdf extension for the filename.
# @param kwargs all the options.
# @return the pdf filename
# -----------------------------------------------------------------------------
def pdf_features(filename, filename_ext=".pdf", **kwargs):
    logging.info('pdf features %s', filename)
    filename = common.check_is_file_and_correct_path(filename, filename_ext)

    temp_dir = common.get_new_temp_dir()
    temp_pdf_filename = os.path.join(temp_dir, os.path.basename(filename))
    shutil.copy(filename, temp_pdf_filename)

    file_in = open(temp_pdf_filename, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(file_in)
    pdf_metadata = pdf_reader.getDocumentInfo()

    metadata = {}
    for key in pdf_metadata:
        metadata[key] = ''
    if 'metadata' in kwargs:
        for key in kwargs['metadata']:
            metadata['/' + key[0].upper() + key[1:]] = kwargs['metadata'][key]

    pdf_args = {}
    for key in kwargs:
        if len(key) < 4:
            continue
        if key[:4] == 'pdf_':
            local_name = kwargs[key]
            if 'path' in kwargs:
                local_name = os.path.join(kwargs['path'], local_name)
            local_name = common.check_is_file_and_correct_path(local_name)
            pdf_args[key[4:]] = PyPDF2.PdfFileReader(open(local_name, "rb"))

    num_pages = pdf_reader.getNumPages()
    pdf_writer = PyPDF2.PdfFileWriter()

    for page_number in range(num_pages):
        page = pdf_reader.getPage(page_number)
        if page_number == 0:
            if 'background_first_page' in pdf_args:
                page.mergePage(pdf_args['background_first_page'].getPage(0))
            elif 'background' in pdf_args:
                page.mergePage(pdf_args['background'].getPage(0))
        else:
            if 'background' in pdf_args:
                page.mergePage(pdf_args['background'].getPage(0))
        if 'watermark' in pdf_args:
            page.mergePage(pdf_args['watermark'].getPage(0))
        pdf_writer.addPage(page)

    pdf_writer.addMetadata(metadata)

    file_out = open(filename, 'wb')
    pdf_writer.write(file_out)

    file_out.close()
    file_in.close()
    shutil.rmtree(temp_dir)
    return filename

# -----------------------------------------------------------------------------
# Convert md file to pdf
#
# @param filename the filename of the markdon file
# @param filename_ext This parameter the markdown extension for the filename.
# @return the pdf filename
# -----------------------------------------------------------------------------
def convert_md_to_pdf(filename, filename_ext=".md", **kwargs):
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
    md_metadata = instruction.get_vars_from_md_file(filename)

    temp_dir = common.get_new_temp_dir()
    temp_md_filename = os.path.join(temp_dir, os.path.basename(filename))

    logging.info('Copy file to temp')
    shutil.copy(filename, temp_md_filename)
    logging.info('Convert md to html')
    temp_html_filename = convert_md_to_html(
        temp_md_filename, converter='mistune')

    title = None
    if 'title' in md_metadata:
        title = md_metadata['title']
    if 'page:title' in md_metadata:
        title = md_metadata['page:title']

    logging.info('Convert html to pdf title=%s', title)
    temp_pdf_filename = convert_html_to_pdf(temp_html_filename, title=title)

    logging.info('Copy file from temp')
    pdf_filename = os.path.splitext(filename)[0] + ".pdf"
    shutil.copy(temp_pdf_filename, pdf_filename)

    # remove the temp dir
    logging.info('Remove the temp dir')
    shutil.rmtree(temp_dir)

    # add features
    pdf_features(pdf_filename, filename_ext=".pdf",
                 metadata=md_metadata, **kwargs)

    return pdf_filename

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
