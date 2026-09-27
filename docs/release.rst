Release process
===============

Releases are deliberately split into local validation and remote publication.
No build command pushes Git objects or uploads a package.

Before releasing
----------------

Install the environment, then validate a clean checkout. See :doc:`contributing`
for browser integration, workflow validators and platform-specific setup::

   uv sync --locked --extra dev --extra docs --extra pdf
   uv run --no-sync pytest
   uv run --no-sync pyright
   uv run --no-sync ruff check .
   uv run --no-sync ruff format --check .
   uv run --no-sync python scripts/update_license_notices.py
   uv run --no-sync pip-audit --skip-editable
   uv run --no-sync python examples/run_all.py
   uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b html docs docs/_build/html
   uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b doctest docs docs/_build/doctest
   uv run --no-sync python scripts/release.py build
   uv run --no-sync python scripts/check_distribution.py dist

Version and tag
---------------

The release helper updates both version files and creates an annotated local
tag only when the worktree is clean::

   uv run --no-sync python scripts/release.py bump patch
   git diff -- src/pymdtools/version.py src/pymdtools/version.bat
   git add src/pymdtools/version.py src/pymdtools/version.bat
   git commit -m "Release version bump"
   uv run --no-sync python scripts/release.py check
   uv run --no-sync python scripts/release.py tag
   uv run --no-sync python scripts/release.py verify-tag

The helper prints the actual new version and tag; do not copy a version number
from an older example. ``bump`` starts from a clean tree and edits both version
files. ``tag`` requires those edits to have been committed. Update release notes
for the version before tagging, and validate the final release commit.

Inspect the printed tag before pushing that single tag. Historical mismatches can be
reported, without changing them, with::

   uv run --no-sync python scripts/release.py audit-tags

``build`` rebuilds the repository's ``dist/`` directory and checks both archives
with Twine. It requires a clean tree unless ``--allow-dirty`` is explicitly used
for local validation. The installed-wheel checker creates a separate environment
and requires network access for dependencies. Neither command publishes anything.

Publication
-----------

Create a GitHub release from the verified annotated version tag. The publication
workflow checks that the tag points at the release commit and that both version
files agree. A job without publishing credentials tests and builds the
distributions; a separate protected job receives only those artifacts and
publishes them through PyPI trusted publishing. It has no long-lived PyPI
password.

The build checks out the event's immutable commit and verifies the annotated
tag against it. It reruns workflow validation, lint, types, dependency auditing,
license-notice checks, documentation and its offline examples, tests and the
installed-wheel checks.
Shared dependency caches are disabled for release jobs. The publishing job
downloads the artifact by the build job's artifact ID, fails on a digest
mismatch, and enables PyPI's PEP 740 attestations.

Configure the GitHub ``pypi`` environment with required reviewers and permitted
release tags. On PyPI, configure the trusted publisher for repository
``IIXIXII/pymdtools``, workflow ``publish.yml`` and environment ``pypi``.
These service settings must exist separately from the workflow files.

For branch protection, require ``CI success``, ``CodeQL (python)`` and
``CodeQL (actions)``. The aggregate CI result includes the reusable workflow
validator and fails on unsuccessful or skipped required jobs. CodeQL uses
advanced setup; an existing default setup must first be disabled to avoid
conflicting analysis configurations.
