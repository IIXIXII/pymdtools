# Licenses of installed dependencies

Reviewed on 2026-09-27 against `uv.lock` and the installed distributions'
`METADATA` and license files. These packages are installed separately: their
implementations are not copied into the pymdtools wheel. The runtime table
records the versions inspected, not additional version constraints. The
Markdown-it entry was updated to 4.2.0 on 2026-10-03 after the dependency refresh.

The project's MIT license does not replace these licenses. In particular,
redistributing an application using GPL/LGPL components needs a review of that
combined distribution. Declaring a dependency is not evidence that every use
or redistribution is permitted under MIT alone.

## Direct runtime dependencies

| Distribution | Inspected version | Declared terms and primary source |
| --- | --- | --- |
| `chardet` | 7.6.0 | 0BSD, as declared in the distribution metadata and its [shipped license](https://github.com/chardet/chardet/blob/7.6.0/LICENSE). |
| `Markdown` | 3.11 | BSD-3-Clause; [Python-Markdown](https://github.com/Python-Markdown/markdown). |
| `markdown-it-py` | 4.2.0 | MIT; preserves both Python port and original markdown-it notices in `LICENSE` and `LICENSE.markdown-it`; [project](https://github.com/executablebooks/markdown-it-py). |
| `markdownify` | 1.2.3 | MIT; [python-markdownify](https://github.com/matthewwithanm/python-markdownify). |
| `mistune` | 3.3.4 | BSD-3-Clause; [Mistune](https://github.com/lepture/mistune). |
| `python-dateutil` | 2.9.0.post0 | Apache-2.0 and BSD-3-Clause notices, with dual licensing for designated contributions; consult its [LICENSE](https://github.com/dateutil/dateutil/blob/2.9.0.post0/LICENSE) rather than assigning one license to every historical file. |
| `Unidecode` | 1.4.0 | GPL-2.0-or-later; [copyright and license](https://github.com/avian2/unidecode/blob/unidecode-1.4.0/README.rst#copyright). It is not an MIT dependency. |

## Optional PDF dependencies

| Distribution | Inspected version | Declared terms |
| --- | --- | --- |
| `playwright` | 1.63.0 | Apache-2.0; [Playwright Python](https://github.com/microsoft/playwright-python). Its packaged driver includes additional third-party notices. |
| `pypdf` | 6.19.0 | BSD-3-Clause; [pypdf](https://github.com/py-pdf/pypdf). |

Chromium is downloaded separately by Playwright and is not bundled in pymdtools.
It includes its own third-party components and notices; consult the actual
browser build's notices when redistributing that browser. Operating-system
fonts used for PDF rendering also have their own terms.

## Runtime transitive dependencies inspected

| Distribution | Inspected version | Declared terms |
| --- | --- | --- |
| `beautifulsoup4` | 4.15.0 | MIT |
| `soupsieve` | 2.10 | MIT |
| `six` | 1.17.0 | MIT |
| `mdurl` | 0.1.2 | MIT |
| `typing-extensions` | 4.16.0 | PSF-2.0 |
| `greenlet` | 3.5.6 | MIT AND PSF-2.0 |
| `pyee` | 13.0.1 | MIT |

This is the inspected Python 3.14/Windows runtime plus PDF environment. Other
Python versions, platforms or dependency updates can select different packages.
`uv.lock` records that resolution; the installed package's license files supply
its authoritative notices.

## Development, documentation and build tools

These are not runtime features or bundled implementations. Direct tools used
by this project declare the following licenses:

| Tools | Declared terms |
| --- | --- |
| `pyright`, `pytest`, `pytest-cov`, `ruff` | MIT |
| `hypothesis` | MPL-2.0 |
| `pip-audit`, `twine` | Apache-2.0 |
| `myst-parser`, `sphinx-rtd-theme` | MIT |
| `sphinx` | BSD-2-Clause |
| `setuptools` (build backend) | MIT |
| `uv` (environment/build command) | MIT OR Apache-2.0 |
| `actionlint` 1.7.12 (workflow validation) | MIT; [upstream notice](https://github.com/rhysd/actionlint/blob/v1.7.12/LICENSE.txt). |
| `zizmor` 1.30.1 (workflow security audit) | MIT; [upstream notice](https://github.com/zizmorcore/zizmor/blob/v1.30.1/LICENSE). |

This tool table is not an inventory of all of their transitive dependencies,
bundled Node.js/driver binaries or the Python interpreter. If redistributing a
development environment, inventory the complete installed environment and
preserve each distribution's own notices, including Node.js and Python notices.

## Document templates

`src/pymdtools/referenced_files/license.txt` and `license.en.txt` currently contain
historical proprietary document notices bearing Florent Tournois' name. They
are insertion templates, not the license of the Python implementation. Their
wording does not describe the open-source package. Select or author a notice
appropriate to your own document; processing a document does not itself change
its ownership or license.
