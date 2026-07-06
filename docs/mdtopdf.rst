Markdown To PDF
===============

``pymdtools.mdtopdf`` contains the Markdown to HTML/PDF conversion pipeline.
Markdown is rendered to HTML, injected into a packaged layout, converted to PDF
with ``pdfkit`` and ``wkhtmltopdf``, then optionally post-processed with
metadata, backgrounds, and watermarks.

Pipeline
--------

The high-level path is:

- ``convert_md_to_html`` renders Markdown into a layout-backed HTML file.
- ``convert_html_to_pdf`` renders that HTML file through ``wkhtmltopdf``.
- ``pdf_features`` applies metadata and overlay PDFs.
- ``convert_md_to_pdf`` orchestrates the complete flow.

Common Usage
------------

.. code-block:: python

   from pymdtools.mdtopdf import convert_md_to_pdf

   pdf_path = convert_md_to_pdf("README.md")

The external ``wkhtmltopdf.exe`` executable must be available in one of the
locations scanned by ``find_wk_html_to_pdf``.

Public API
----------

.. automodule:: pymdtools.mdtopdf
   :members:
   :undoc-members:
   :show-inheritance:
