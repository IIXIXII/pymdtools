# Contributing

Use Python 3.10 or newer. The lock includes platform and Python-version markers.
The importable package is under `src/pymdtools`; an editable installation is
required for local scripts and tests.

```bash
python -m pip install uv==0.12.19
uv sync --locked --extra dev --extra docs --extra pdf
uv run --no-sync pytest
uv run --no-sync pyright
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b html docs docs/_build/html
```

Run `uv run --no-sync ruff format .` before submitting a change. Keep new behavior
covered by contract tests: preservation of literal Markdown, idempotence,
restricted file access, valid PDF output and preservation of existing targets
when a conversion fails. The coverage gate remains 100%; it complements these
behavioral checks.

In VS Code, select `.venv` with **Python: Select Interpreter**, then refresh the
Testing view. On Windows the interpreter is `.venv\Scripts\python.exe`; on
Linux/macOS it is `.venv/bin/python`. The workspace settings use `tests/` and
automatically load pytest configuration from `pyproject.toml`. VS Code can retain
a previously selected interpreter, so changing `python.defaultInterpreterPath`
alone may not switch an existing workspace. Test Explorer overrides only the
coverage failure threshold to allow discovery and individual test runs; the
terminal and CI retain the 100% full-suite coverage requirement.

Install the workspace's recommended Python, Pylance, Python Debugger and Ruff
extensions. Ruff uses the selected environment and gives priority to
`pyproject.toml`; saving a Python file formats it, applies safe fixes and sorts
imports. The **Python: debug tests** launch configuration is used by Test Explorer
and disables coverage only during debugging, so breakpoints work reliably.
It also ignores only `pytest_cov.CovDisabledWarning` for that debug session:
other warnings remain errors, as configured in `pyproject.toml`.

Use **Tasks: Run Task** to run **Install locked development environment** first.
On Windows, it uses `make.bat install_editable` to bootstrap the pinned uv version;
on Linux/macOS, install uv as shown above before running the task. Then select
`.venv` as the interpreter. All check tasks run from the repository root with that
interpreter. **Check project** runs lint, formatting, types, tests and documentation
in sequence, stopping on the first failure. Ruff and Pyright task diagnostics
appear in the Problems panel. **Run tests** remains the default test task and
**Build distributions** remains the default build task (`Ctrl+Shift+B`).
The Pyright task also passes the selected interpreter via `--pythonpath`, so it
resolves dependencies correctly even when the task terminal has no active venv.

Pytest uses its default per-user temporary directory. When running checks under
a separate automation or sandbox account, use a separate cache as well, for
example `pytest -o cache_dir=.pytest_cache_agent`. Do not reuse another account's
temporary directory or pytest cache: Windows can restrict access to their owner.

To exercise the real PDF backend, install Chromium with
`uv run --no-sync playwright install --with-deps chromium`, set
`PYMDTOOLS_PDF_TESTS=1`, and run
`uv run --no-sync pytest -m pdf_integration --no-cov`.
Use `$env:PYMDTOOLS_PDF_TESTS = '1'` in PowerShell or
`export PYMDTOOLS_PDF_TESTS=1` in a POSIX shell.
The integration test creates a two-page document with accents, a table, a local
SVG, and a link. Review rendering when changing the browser, CSS or layouts.

```bash
uv run --no-sync python scripts/benchmark_markdown.py --max-seconds 3
uv run --no-sync python scripts/release.py build --allow-dirty
uv run --no-sync python scripts/check_distribution.py dist
```

The distribution check installs the wheel with its core dependencies in a new
environment outside the repository, exercises Markdown and HTML operations,
checks distributed types and validates source archive contents. It requires
network access to install dependencies. Release builds require a clean tree;
`--allow-dirty` is for local validation only.

Dependency metadata lives in `pyproject.toml`; the requirements files are
compatibility entry points. Update constraints intentionally, run `uv lock
--upgrade`, then run all checks and `uv run --no-sync pip-audit --skip-editable`
after syncing the new lock. The scheduled CI job also tests current compatible
releases independently of the lock. Verify the GitHub `pypi` environment's
reviewers and trusted publisher configuration before publishing.

Keep existing public imports compatible when moving implementations. The
CommonMark source adapter lives in `src/pymdtools/_markdown.py`; rendering process
and resource policy live in `src/pymdtools/_rendering/pdf_backend.py`. Use package loggers,
explicit options and documented exceptions for new API boundaries.

Add semantic regression documents to `tests/fixtures/markdown/`. The same corpus
is checked through inspection, rewriting, normalization and offline translation.
Run `python examples/workflows.py --output examples/output` for the complete
example. The architecture and workflow guides are maintained under `docs/`.

Windows `make.bat` installation shortcuts use the pinned uv version and
`uv sync --locked`. They pass `--inexact` to retain the uv bootstrap tool and
previously installed extras; all requested dependencies still follow the lock.
VS Code tasks use the selected interpreter and the current Ruff/debugpy tools.

When changing bundled layouts, review `LICENSES-3rd-party.md` and the original
authors' notices. Update `THIRD_PARTY_LICENSES/` and the component mapping in
`scripts/update_license_notices.py`, then run that script with `--write`.
Running it without arguments checks that every layout's exported `LICENSES.txt`
is up to date; CI runs this check. Keep unresolved permissions visible until
they are backed by the authors' terms. Review `LICENSES-dependencies.md` when
updating dependencies. The MIT-header helper always excludes third-party
resources, license documents and generated environments, even with
`--include-hidden`.
