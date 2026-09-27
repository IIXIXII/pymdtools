# Usage examples

This directory contains **25 focused examples** and the existing complete
[`workflows.py`](./workflows.py) scenario. Each script calls the public pymdtools
API, creates inspectable output files, and checks the result where appropriate.
All examples use local sample data. The translation examples inject a small
local transport; they never call a translation service.

## Install and start

Use a checkout or the source archive: the wheel does not install these scripts.
From its root, install the package into your Python environment before running:

```bash
python -m pip install -e .
python examples/run_all.py --list
python examples/01_normalize_text.py
python examples/run_all.py
```

If the project's uv environment is already installed, use
`uv run --no-sync python` instead of `python`:

```bash
uv run --no-sync python examples/22_report_pipeline.py
uv run --no-sync python examples/run_all.py --output examples/output
```

The default batch runs **23 examples**: examples 01–22 and `workflows.py`.
It needs only the core dependencies. Scripts find their sample data relative
to their own location, so they also work when launched from another directory
using an absolute script path.

## Choose an example

| Script | What it demonstrates | Main outputs |
| --- | --- | --- |
| [01_normalize_text.py](./01_normalize_text.py) | Normalize a string; verify that repeated normalization is stable. | `before.md`, `after.md` |
| [02_normalize_file.py](./02_normalize_file.py) | Normalize a copied file while preserving a dated backup. | `guide.md`, `guide.md.*.bak` |
| [03_edit_document.py](./03_edit_document.py) | Edit `MarkdownContent`, title, variables and save state. | `document.md` |
| [04_variables.py](./04_variables.py) | Declare/read variables and fill `begin-var` blocks. | `declared.md`, `rendered.md`, `injected.md` |
| [05_include_files.py](./05_include_files.py) | Include a fragment in raw or boxed mode; leave fenced examples unchanged. | `raw.md`, `box.md` |
| [06_shared_references.py](./06_shared_references.py) | Refresh named `begin-ref` / `begin-include` sections. | `handbook.md` |
| [07_discovery_options.py](./07_discovery_options.py) | Limit reference discovery depth and exclude generated folders. | `library/`, `handbook.md` |
| [08_titles_and_toc.py](./08_titles_and_toc.py) | Preserve or change heading style; obtain an HTML table of contents. | `setext.md`, `atx.md`, `toc.html` |
| [09_inspect_links.py](./09_inspect_links.py) | Inspect inline/reference links and classify external URLs. | `links.json` |
| [10_update_links.py](./10_update_links.py) | Apply sequential renames without changing unselected reference users. | `updated.md` |
| [11_rebase_links.py](./11_rebase_links.py) | Rebase local links, preserving URL queries, anchors, spaces and accents. | `rebased.md` |
| [12_html_to_markdown.py](./12_html_to_markdown.py) | Convert HTML with ATX headings and explicit list bullets. | `article.md` |
| [13_markdown_to_html.py](./13_markdown_to_html.py) | Generate a complete page with local layout assets and notices. | `guide.html`, `_pymdtools_assets/` |
| [14_layout_gallery.py](./14_layout_gallery.py) | Compare GitHub, Bootstrap and Solarized layouts. | `index.html`, one directory per layout |
| [15_files_and_templates.py](./15_files_and_templates.py) | Load a local template and edit it through `FileContent`. | `welcome.md`, a dated backup |
| [16_batch_processing.py](./16_batch_processing.py) | Process a file tree and collect an intentional empty-file error. | `documents/`, `batch-report.json` |
| [17_paths_and_encoding.py](./17_paths_and_encoding.py) | Convert CP1252 to UTF-8; distinguish path encoding and slug creation. | `legacy.txt`, `utf8.txt`, `paths.json` |
| [18_translation_cache.py](./18_translation_cache.py) | Inject an offline transport, reuse cached translations and clear the cache. | `transport-calls.json` |
| [19_translate_markdown.py](./19_translate_markdown.py) | Translate paragraph text while preserving formatting, link targets and code. | `source.md`, `translated.md` |
| [20_translation_errors.py](./20_translation_errors.py) | Retry a simulated timeout, keep fallback text and reject damaged markers. | `error-handling.txt` |
| [21_custom_renderer.py](./21_custom_renderer.py) | Extend the Mistune renderer using the `close()` hook. | `custom.html` |
| [22_report_pipeline.py](./22_report_pipeline.py) | Combine JSON, variables and reusable sections into a report. | `report.md`, `report.html`, assets |
| [23_pdf_render.py](./23_pdf_render.py) | Render Markdown to Letter-size PDF with metadata. **PDF setup required.** | `guide.pdf` |
| [24_pdf_local_assets.py](./24_pdf_local_assets.py) | Render local HTML/SVG, accents, a table and a page break. **PDF setup required.** | `print.pdf` with two pages |
| [25_pdf_postprocess.py](./25_pdf_postprocess.py) | Balance pages, add stationery/watermarks and set final metadata. **PDF setup required.** | `document.pdf`, overlay PDFs, a backup |
| [workflows.py](./workflows.py) | Run the original assembly, link editing, translation and HTML workflow. | `document.md`, `translated.md`, `document.html` |

For a first tour, run **03 → 05 → 09 → 13 → 22**. Open the generated Markdown,
JSON or HTML after each script, then read its implementation to see the API calls.

## Output directories

Each numbered script defaults to `examples/output/<script-name>/`. Override it
with a dedicated directory:

```bash
python examples/10_update_links.py --output examples/output/my-link-demo
python examples/run_all.py --output examples/output/full-tour
```

The runner gives each script its own subdirectory and stops if a script fails.
Example outputs may be replaced when you rerun a script; backup examples create
additional dated backups. Use a directory reserved for these generated files.
The supplied `data/` fixtures are only read. Default outputs are ignored by Git
and excluded from source distributions.

For `workflows.py`, pass `--output` explicitly when running it on its own:

```bash
python examples/workflows.py --output examples/output/workflows
```

## Optional PDF examples

Install the PDF extra and Chromium once:

```bash
python -m pip install -e ".[pdf]"
python -m playwright install --with-deps --only-shell chromium
python examples/23_pdf_render.py
python examples/run_all.py --only-pdf
```

With the uv development environment:

```bash
uv sync --locked --extra dev --extra docs --extra pdf
uv run --no-sync playwright install --with-deps --only-shell chromium
uv run --no-sync python examples/run_all.py --pdf
```

`--pdf` runs all **26 scenarios**; `--only-pdf` runs just examples 23–25.
Browser installation downloads Chromium. Once installed, the PDF examples render
local content with network access disabled. They use `pypdf` to check the generated
pages and metadata. Keep the generated stationery and watermark PDFs if you want
to inspect the intermediate steps in example 25.

## Details to keep when adapting the code

- **Inclusions:** put the plain filename in `include-file(introduction.md)` and
  pass its containing folder through `search_folders`. `render_mode="raw"`
  inserts visible Markdown; `"box"` retains the fragment inside an HTML comment.
- **Reference discovery:** `IncludeOptions(refs_depth=0)` scans only each root.
  Use `1` for one nested level, or `-1` for unlimited recursion. The standalone
  directory discovery helper has its own default; the examples pass depth explicitly.
- **Rebasing:** `encode_path_url` preserves existing path names. Slugification
  creates new names and does not rename files on disk.
- **HTML exports:** share the HTML together with its `_pymdtools_assets/` tree,
  including `LICENSES.txt`. Layout licenses are described in
  [the resource inventory](https://github.com/IIXIXII/pymdtools/blob/master/LICENSES-3rd-party.md).
- **Translation:** the replacement dictionaries demonstrate the client API,
  not translation quality. A client with no custom transport uses MyMemory and
  sends text to that service. Example 20 deliberately logs one simulated failure.
- **PDF processing:** `check_odd_pages` appends a blank page when needed to obtain
  an even count. Set final metadata after this operation; example 25 then applies
  its overlays to both pages.

The Python examples and the original sample Markdown, JSON, HTML and SVG are
covered by the project's [MIT license](https://github.com/IIXIXII/pymdtools/blob/master/LICENSE.md). Generated layout assets
retain their own notices.
