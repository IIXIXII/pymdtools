<!--
===============================================================================
                    Author: Florent TOURNOIS | License: MIT
===============================================================================
-->

# pymdtools

[![PyPI version](https://img.shields.io/pypi/v/pymdtools.svg?style=flat)](https://pypi.org/project/pymdtools/)
[![Documentation](https://img.shields.io/readthedocs/pymdtools.svg?style=flat)](https://pymdtools.readthedocs.io/)
[![CI](https://github.com/IIXIXII/pymdtools/actions/workflows/ci.yml/badge.svg)](https://github.com/IIXIXII/pymdtools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](https://github.com/IIXIXII/pymdtools/blob/master/LICENSE.md)

`pymdtools` is a Python library for inspecting, transforming and publishing
Markdown documents. Assemble reusable sections, edit links, normalize formatting,
generate HTML or PDF, and translate text through an injectable client.

Python **3.11–3.14** is tested in CI on Linux and Windows, with additional macOS
checks. Core Markdown and HTML features work without a browser or PDF dependencies.

## Installation

Install into your Python environment:

```bash
python -m pip install pymdtools
```

For PDF output, install the extra and the browser in the same environment:

```bash
python -m pip install "pymdtools[pdf]"
python -m playwright install chromium
```

On Linux, use `python -m playwright install --with-deps chromium` to install
browser system libraries as well. See the
[installation guide](https://pymdtools.readthedocs.io/en/latest/getting_started.html)
for virtual environments and source installations. The examples and developer
scripts below belong to the repository or source archive; they are not installed
as commands by the wheel.

## First document

This example creates `build/hello.md` and `build/hello.html`, together with the
HTML layout's assets. Running it again replaces the generated files; Markdown
writes keep a dated backup by default.

```python
from pathlib import Path

from pymdtools.mdfile import MarkdownContent
from pymdtools.mdtopdf import convert_md_to_html

output = Path("build")
output.mkdir(exist_ok=True)
document = MarkdownContent(
    content="# Welcome\n\nProject: <!-- begin-var(project) --><!-- end-var -->\n"
)
document["project"] = "pymdtools"
document.process_tags()
document.write(output / "hello.md")
html_path = convert_md_to_html(output / "hello.md", layout="github")
print(html_path)
```

Open the HTML file in a browser. Keep its adjacent `_pymdtools_assets/` directory
when copying or publishing the page. To also produce `build/hello.pdf`, after
installing PDF support:

```python
from pymdtools.mdtopdf import convert_md_to_pdf
from pymdtools.options import PdfFeatures
from pymdtools.pdf_backend import PdfOptions

pdf_path = convert_md_to_pdf(
    "build/hello.md",
    options=PdfOptions(page_format="A4", timeout=60),
    features=PdfFeatures(metadata={"title": "Welcome", "author": "Example team"}),
)
```

## Choose a workflow

| Task | Public entry point | Guide |
| --- | --- | --- |
| Edit documents, titles and variables | `pymdtools.mdfile.MarkdownContent` | [Documents](https://pymdtools.readthedocs.io/en/latest/mdfile.html) |
| Resolve snippets and shared sections | `pymdtools.instruction` | [Directives](https://pymdtools.readthedocs.io/en/latest/instruction.html) |
| Find, rename and rebase links | `pymdtools.mdcommon` | [Links](https://pymdtools.readthedocs.io/en/latest/mdcommon.html) |
| Normalize Markdown | `pymdtools.normalize` | [Normalization](https://pymdtools.readthedocs.io/en/latest/normalize.html) |
| Generate HTML, PDF and overlays | `pymdtools.mdtopdf` | [Conversion](https://pymdtools.readthedocs.io/en/latest/mdtopdf.html) |
| Convert HTML to Markdown | `pymdtools.markdownify_integration` | [HTML input](https://pymdtools.readthedocs.io/en/latest/markdownify_integration.html) |
| Translate text and Markdown | `pymdtools.translate` | [Translation](https://pymdtools.readthedocs.io/en/latest/translate.html) |
| Read files, process trees and load templates | `pymdtools.common`, `pymdtools.filetools` | [File tools](https://pymdtools.readthedocs.io/en/latest/filetools.html) |

The [example catalogue](https://github.com/IIXIXII/pymdtools/blob/master/examples/README.md)
contains **25 focused scripts and one complete workflow**, with local sample
data and expected outputs. From a checkout, after installing the package:

```bash
python -m pip install -e .
python examples/run_all.py --list
python examples/run_all.py
python examples/22_report_pipeline.py
```

The default runner executes 23 scenarios with core dependencies. Results go to
`examples/output/<example>/`. Install `.[pdf]` and Chromium before using
`--only-pdf` for the three PDF scenarios, or `--pdf` for all 26.

## Behavior to know

- Link inspection and edits use CommonMark source positions. Duplicate link
  occurrences are preserved, reference identifiers are case-insensitive, and
  images and code are excluded from ordinary link discovery.
- Normalization returns the input unchanged if the candidate changes CommonMark
  rendering or fails its idempotence check. Extensions used by other Markdown
  dialects need validation against representative documents.
- `MarkdownContent.process_tags()` changes the in-memory buffer; call `write()`
  to save it. `include-file` accepts a filename, with directories supplied through
  `IncludeOptions(search_folders=...)`. Reference discovery scans each root only
  by default; set `refs_depth=-1` explicitly for recursion.
- HTML conversion uses an escaping Mistune renderer by default. The explicit
  `converter="markdown"` alternative preserves raw HTML and needs trusted input.
  File inclusions also need trusted documents and deliberate search roots.
- PDF rendering disables JavaScript and remote resources by default. Local
  assets are confined to the HTML directory and permitted source asset root.
  `PdfOptions.timeout` limits the Chromium worker lifetime, including startup;
  it does not cover separate Markdown conversion or PDF post-processing.
- Translation uses the external MyMemory service unless a custom transport is
  supplied. The repository's translation examples run entirely offline.

See the [options reference](https://pymdtools.readthedocs.io/en/latest/options.html),
[troubleshooting guide](https://pymdtools.readthedocs.io/en/latest/troubleshooting.html)
and [changelog](https://github.com/IIXIXII/pymdtools/blob/master/CHANGELOG.md)
for defaults, errors and migration details.

## Development and documentation

From the repository root, create the locked development environment:

```bash
python -m pip install uv==0.12.19
uv sync --locked --group dev --group docs --extra pdf
uv run --no-sync pytest
uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b html docs docs/_build/html
uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b doctest docs docs/_build/doctest
```

Open `docs/_build/html/index.html`. Chromium is only required for the optional
PDF examples and integration test. See
[CONTRIBUTING.md](https://github.com/IIXIXII/pymdtools/blob/master/CONTRIBUTING.md)
for lint, types, VS Code, distributions and CI, and the
[release guide](https://pymdtools.readthedocs.io/en/latest/release.html)
for versioning and publication. Maintainers can prepare versions and changelog
notes with `scripts/release.py prepare patch`; pushing the resulting version tag
automates validation, PyPI publication and the GitHub release.
The library lives in `src/pymdtools`.

## Project links and licenses

- [Documentation](https://pymdtools.readthedocs.io/)
- [PyPI package](https://pypi.org/project/pymdtools/)
- [Source and issues](https://github.com/IIXIXII/pymdtools)

Original Python code and sample data use the
[MIT license](https://github.com/IIXIXII/pymdtools/blob/master/LICENSE.md).
Bundled layouts retain their own terms and attribution; the
[resource inventory](https://github.com/IIXIXII/pymdtools/blob/master/LICENSES-3rd-party.md)
records the terms of the bundled resources and the replacement of historical themes. Installed
dependencies have separate licenses, including GPL/LGPL components; see the
[dependency inventory](https://github.com/IIXIXII/pymdtools/blob/master/LICENSES-dependencies.md).
