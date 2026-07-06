<!--
===============================================================================
                    Author: Florent TOURNOIS | License: MIT
===============================================================================
-->

# pymdtools

[![PyPI version](https://img.shields.io/pypi/v/pymdtools.svg?style=flat)](https://pypi.python.org/pypi/pymdtools/)
[![Wheel](https://img.shields.io/pypi/wheel/pymdtools.svg?style=flat)](https://pypi.python.org/pypi/pymdtools/)
[![Documentation](https://img.shields.io/readthedocs/pymdtools.svg?style=flat)](https://pymdtools.readthedocs.io/)
[![License](https://img.shields.io/github/license/IIXIXII/pymdtools.svg?style=flat)](https://github.com/IIXIXII/pymdtools/blob/master/LICENSE.md)

`pymdtools` is a Python toolkit for working with Markdown documents. It provides
small, composable helpers to read, normalize, enrich, inspect, convert, and
translate Markdown content.

The project is designed for practical documentation workflows: maintaining
Markdown files, resolving reusable snippets, updating links, converting Markdown
to HTML or PDF, and integrating with modern Markdown libraries such as Mistune
and markdownify.

## Features

- Read and write text files with encoding-aware helpers.
- Normalize Markdown content and Markdown files.
- Manage reusable Markdown instructions stored in HTML comments:
  - variables;
  - include-file directives;
  - shared reference blocks;
  - generated include blocks.
- Inspect and rewrite Markdown links.
- Work with Markdown files through a high-level `MarkdownContent` wrapper.
- Convert Markdown to HTML with Python-Markdown or Mistune.
- Convert Markdown or HTML to PDF through `pdfkit` and `wkhtmltopdf`.
- Apply PDF metadata, backgrounds, watermarks, and blank-page balancing.
- Convert HTML fragments to Markdown through the external `markdownify` package.
- Translate plain text and Markdown with the MyMemory API.

## Installation

Install the published package from PyPI:

```bash
pip install pymdtools
```

For development, clone the repository and install the project dependencies:

```bash
git clone https://github.com/IIXIXII/pymdtools.git
cd pymdtools
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

`pymdtools` supports Python 3.7 and newer.

## Optional System Dependency

PDF generation uses `pdfkit`, which requires the external `wkhtmltopdf`
executable. Install `wkhtmltopdf` separately if you need Markdown-to-PDF or
HTML-to-PDF conversion.

On Windows, `pymdtools` searches common installation locations such as:

- `C:\Program Files\wkhtmltopdf`
- `D:\Program Files\wkhtmltopdf`
- local `wkhtmltopdf` / `software` / `third_party_software` folders

## Quick Start

Normalize Markdown text:

```python
from pymdtools.normalize import md_beautifier

markdown = md_beautifier("# Title\n\nBody\n")
```

Work with a Markdown file:

```python
from pymdtools.mdfile import MarkdownContent

doc = MarkdownContent("README.md")
doc["project"] = "pymdtools"
doc.title = "Project README"
doc.process_tags()
doc.write()
```

Resolve include references in a Markdown file:

```python
from pymdtools.instruction import search_include_refs_to_md_file

search_include_refs_to_md_file("docs/page.md", backup_option=True)
```

Convert Markdown to PDF:

```python
from pymdtools.mdtopdf import convert_md_to_pdf

pdf_path = convert_md_to_pdf("README.md")
```

Convert HTML to Markdown:

```python
from pymdtools.markdownify_integration import markdownify

markdown = markdownify("<h1>Title</h1>")
```

## Main Modules

- `pymdtools.common`: shared path, filesystem, text, datetime, and validation helpers.
- `pymdtools.filetools`: file-oriented wrappers such as `FileName` and `FileContent`.
- `pymdtools.instruction`: Markdown comment directives, variables, refs, and includes.
- `pymdtools.mdcommon`: Markdown link discovery and rewriting helpers.
- `pymdtools.mdfile`: high-level `MarkdownContent` wrapper for editable Markdown files.
- `pymdtools.mdtopdf`: Markdown, HTML, and PDF conversion pipeline.
- `pymdtools.mistune_integration`: Mistune 3 compatibility layer.
- `pymdtools.markdownify_integration`: wrapper around the external `markdownify` package.
- `pymdtools.normalize`: Markdown normalization helpers.
- `pymdtools.translate`: plain-text and Markdown translation helpers.

## Documentation

The documentation is available on Read the Docs:

<https://pymdtools.readthedocs.io/>

To build it locally:

```bash
python -m pip install -r requirements-docs.txt
python -m sphinx.cmd.build -b html docs docs/_build/html
```

## Development

Run the test suite:

```bash
python -m pytest
```

Run static type checking:

```bash
python -m pyright
```

Build the documentation in strict mode:

```bash
python -m sphinx.cmd.build -b html -W --keep-going docs docs/_build/html
```

## Project Links

- Documentation: <https://pymdtools.readthedocs.io/>
- Package: <https://pypi.python.org/pypi/pymdtools/>
- Source code: <https://github.com/IIXIXII/pymdtools>
- Issue tracker: <https://github.com/IIXIXII/pymdtools/issues>

## License

`pymdtools` is distributed under the MIT license. See [LICENSE.md](LICENSE.md)
for details.
