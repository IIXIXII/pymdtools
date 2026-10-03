# Changelog

## Unreleased

## 3.0.0 - 2026-10-03

### Changed

- Require Python 3.11 or newer. Python 3.10 users must stay on 2.1.1 until they
  upgrade Python. This major release drops Python 3.10 support.
- Move contributor and documentation tools to PEP 735 dependency groups.
  Replace `pip install -r requirements-dev.txt` / `.[dev,pdf]` with
  `uv sync --locked --group dev --extra pdf`; use `--group docs` for documentation.
  The public `pdf` extra remains available. With pip 25.1+, use
  `python -m pip install --group dev --group docs -e ".[pdf]"` from the repository.
- Upgrade MyST to 5.1 and allow Markdown-it 4.2 in the locked documentation environment.
- Require pypdf 6.19 or newer within the 6.x series.
- Require Mistune 3.3.4 or newer: minimum-dependency tests exposed changes to
  entities and balanced-parenthesis links when translating with Mistune 3.0.
- Remove four historical themes lacking established redistribution permission.
  `jasonm23-dark` now aliases `thomasf-solarizedcssdark`; `jasonm23-foghorn`,
  `jasonm23-markdown` and `markedapp-byword` alias `github`. Their appearance and
  exported asset directory names change. Original theme files are no longer bundled.

### Fixed

- Honor explicit `nb_up_path` include searches while preserving default containment
  and rejecting symlink escapes. Add filesystem and generated Unicode contract tests.
- Make the Windows `increase_version` shortcut prepare both version files and release notes.

### Maintenance

- Test minimum runtime/PDF dependencies and latest compatible dependencies in required CI.
- Require successful CI and CodeQL push runs for the exact merged master commit before release.
- Pin the isolated build backend with `build-constraints.txt` and use the pinned uv frontend.
- Add repository ruleset definitions, security reporting instructions and release immutability guidance.
- Enable Ruff bugbear and unused-suppression checks; remove obsolete files and references.

## 2.1.1 - 2026-09-27

- Upgrade chardet to 7.6 and inspect the complete requested encoding sample,
  preserving UTF-8 auto-detection when non-ASCII text appears after its default
  200,000-byte limit. Update the dependency inventory for its declared 0BSD license.
- Upgrade the locked Twine version to 7.0 for distribution validation and
  publishing, and allow Twine 7 in the development dependencies.
- Simplify releases: prepare version files and dated changelog notes with one
  local command. A version tag push now runs validation, publishes to PyPI and
  creates the GitHub release with matching notes and distribution archives.

## 2.1.0 - 2026-09-27

This release updates document assembly, Markdown preservation, optional PDF
rendering, translation, examples and the development toolchain. Public module
imports remain available. Review the migration notes below before upgrading.

### Changes

- Reorganize the documentation into installation, user guides and project
  maintenance. Document typed options, persistence, discovery, rendering and
  migration behavior; publish the example and license inventories as rendered
  pages. Execute offline documentation snippets in CI and release validation.
- Add 25 focused, executable usage examples, local sample data, a catalogue and
  a batch runner with optional PDF scenarios. Exercise examples in CI and include
  their source fixtures in source distributions while excluding generated output.
  Correct the documented filename syntax for include-file directives.
- Modernize GitHub Actions with verified action pins, uv caching, test reports
  and a required-check aggregate compatible with merge queues. Add CodeQL,
  reusable workflow lint/security checks and scheduled dependency compatibility
  tests. Correct the PDF test invocation and move Dependabot to the uv ecosystem.
  Harden release validation and artifact handoff, disable release caches and
  explicitly enable PyPI attestations.
- Separate original-code, bundled-resource and dependency licensing. Add missing
  component notices and Subtle Patterns CC-BY-SA-3.0 attribution; record unresolved
  historical theme permissions. Export per-layout notices with generated HTML
  assets, verify them in CI, and protect third-party files from MIT header insertion.
- Remove the legacy Doxygen configuration and assets, unused console logo helper,
  disabled local-upload shortcut and an empty test placeholder. Documentation
  is built with Sphinx; releases are published by the GitHub workflow.
- Move the package to `src/pymdtools`, preserving public module imports. Split
  directive handling, HTML/layout/PDF operations, filesystem helpers and
  translation transport into internal modules. Reinstall editable checkouts
  after updating (`uv sync --locked --extra dev --extra docs --extra pdf`).
- Preserve link destinations containing escaped or unbalanced parentheses and
  literal entities during editing and translation.
- Parse batched label replacements once while preserving sequential renames;
  index matches and serialize shared reference definitions once.
- Only discover references when needed by `MarkdownContent.process_tags`.
  Its default reference depth is now zero for every search root. Set
  `refs_depth=-1` to request the previous recursive behavior. Discovery excludes
  generated directories and skips symbolic links and directory alias cycles.
- Add `IncludeOptions` and `PdfFeatures`; supported legacy keyword arguments
  remain available. Unknown include/PDF feature options now raise an error.
- Add a shared Markdown regression corpus, executable offline workflow example,
  architecture documentation, batch benchmarks and modern VS Code tasks.
- Make Windows development installation shortcuts use the locked environment.

- Add an optional reusable translation client with an injectable transport,
  bounded retries and an in-memory LRU cache. Opt-in paragraph segmentation
  groups text with validated formatting markers; token mode remains the default.
- Protect code fences nested in lists and blockquotes from directive processing.
- Recognize balanced parentheses, escaped labels and case-insensitive references;
  retain every link occurrence and preserve untouched source bytes during edits.
- Reject normalization candidates that change CommonMark rendering or are not
  idempotent. Literal escaped links remain literal text.
- Index code intervals with binary search and batch link replacements.
- Preserve real directory spelling when rebasing links. Use `legacy_slug=True`
  for the old behavior; `common.path_to_url` itself is unchanged.
- Replace pdfkit/wkhtmltopdf with optional Playwright/Chromium. Install the `pdf`
  extra and Chromium separately. Existing conversion entry points remain, with
  typed `PdfOptions` for timeouts, page format and resource access. PDF metadata,
  backgrounds and watermarks continue to use pypdf. PyPDF2 fallback is removed.
- Keep Markdown and HTML operations available without PDF dependencies.
- Publish `py.typed`, centralize metadata in pyproject.toml, and include the
  validation suite and documentation in source distributions.
- Add locked development environments, Ruff, dependency auditing, pinned actions,
  installed-wheel validation, benchmarks and real PDF integration tests.

### Migration from 2.0.47

- Install `pymdtools[pdf]` and run `python -m playwright install chromium` for
  PDF conversion. The core package no longer installs PDF dependencies.
- Reinstall editable checkouts after the move to `src/pymdtools`.
- Set `IncludeOptions(refs_depth=-1)` when `MarkdownContent` should discover
  references recursively; its default now scans each root only.
- Use `legacy_slug=True` for the historical link-rebasing spelling. The default
  preserves existing directory names and percent-encodes spaces and Unicode.
- Replace unknown include or PDF feature keywords with the documented options;
  unsupported names now raise an error.

Rendering can differ from wkhtmltopdf, especially pagination and fonts. The
default network policy is now offline, JavaScript is disabled, and the Chromium
worker is limited to 30 seconds unless configured otherwise. Markdown conversion
and separate PDF post-processing are outside that timeout. Review PDFs
from representative documents when migrating.

The Python code remains MIT-licensed. Distribution metadata now describes the
combined licenses of the code and bundled layouts listed in LICENSES-3rd-party.md.
