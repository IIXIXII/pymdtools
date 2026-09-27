Release process
===============

Releases are deliberately split into local validation and remote publication.
No build command pushes Git objects or uploads a package.

Before releasing
----------------

Run the complete validation suite from a clean checkout::

   uv sync --locked --extra dev --extra docs --extra pdf
   uv run --no-sync pytest
   uv run --no-sync pyright
   uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
   uv run --no-sync python scripts/release.py build
   uv run --no-sync python scripts/check_distribution.py dist

Version and tag
---------------

The release helper updates both version files and creates an annotated local
tag only when the worktree is clean::

   python scripts/release.py bump patch
   git diff -- src/pymdtools/version.py src/pymdtools/version.bat
   git add src/pymdtools/version.py src/pymdtools/version.bat
   git commit -m "Release 1.2.3"
   python scripts/release.py tag

Inspect the tag before pushing that single tag. Historical mismatches can be
reported, without changing them, with::

   python scripts/release.py audit-tags

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
license-notice checks, documentation, tests and the installed-wheel checks.
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
