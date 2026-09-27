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
   git add src/pymdtools/version.py src/pymdtools/version.bat CHANGELOG.md
   git commit -m "Release version bump"
   uv run --no-sync python scripts/release.py check
   uv run --no-sync python scripts/release.py tag
   uv run --no-sync python scripts/release.py verify-tag

The helper prints the actual new version and tag; do not copy a version number
from an older example. ``bump`` starts from a clean tree and edits both version
files. ``tag`` requires those edits to have been committed. Update release notes
for the version before tagging, and validate the final release commit.

Use ``bump minor`` for a feature release and ``bump major`` when adopting a new
major version. If the version files and dated changelog section are already
prepared, skip ``bump``: running it again would create another version. Check
``git status --short`` before tagging; other modified, deleted or untracked files
must also be committed or set aside deliberately. Never force-update an existing
published version tag.

Inspect the printed tag before pushing that single tag. Historical mismatches can be
reported, without changing them, with::

   uv run --no-sync python scripts/release.py audit-tags

``build`` rebuilds the repository's ``dist/`` directory and checks both archives
with Twine. It requires a clean tree unless ``--allow-dirty`` is explicitly used
for local validation. The installed-wheel checker creates a separate environment
and requires network access for dependencies. Neither command publishes anything.

Publication
-----------

One-time service configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the repository's **Settings > Environments**, configure the ``pypi``
environment. Add release-tag deployment rules (for example, tags matching
``v*``) and required reviewers when available for the repository. A rule allowing
only the ``master`` branch will not permit a job triggered from a version tag.

On PyPI, open the project's **Manage > Publishing** page and register a GitHub
Trusted Publisher with these exact values:

.. list-table:: Trusted Publisher configuration
   :header-rows: 1

   * - Field
     - Value
   * - Owner
     - ``IIXIXII``
   * - Repository
     - ``pymdtools``
   * - Workflow filename
     - ``publish.yml`` (without ``.github/workflows/``)
   * - Environment
     - ``pypi``

An account with project management permissions must configure this association.
The workflow uses GitHub's OIDC identity, with no stored PyPI password or API
token. See the official PyPI instructions for `adding a Trusted Publisher
<https://docs.pypi.org/trusted-publishers/adding-a-publisher/>`_ and
`publishing through it
<https://docs.pypi.org/trusted-publishers/using-a-publisher/>`_. These service
settings are separate from the repository and must be checked in the services.

Publish a validated version
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Push the release commit through the normal branch/PR process and wait for
   ``CI success`` and both CodeQL checks on that commit. If a PR is squash-merged
   or rebased, update your local checkout to the resulting release commit before
   creating its tag.
2. From a clean checkout of that commit, run ``scripts/release.py tag`` and
   ``scripts/release.py verify-tag``. Inspect the annotated tag, then push only
   that tag with ``git push origin vX.Y.Z``, replacing the version with the
   helper's printed value. If you already created it on this exact commit in
   the previous section, verify and push it without creating it again.
3. In GitHub **Releases > Draft a new release**, select the existing tag. Use
   ``pymdtools X.Y.Z`` as the title and copy the matching dated changelog section,
   including its migration notes. Publish the release when ready.
4. Follow **Actions > Publish release**. Approve the ``pypi`` environment if it
   requires a review. Confirm both validation and publication jobs succeed.
5. Check the new version on PyPI and install that exact version in a fresh
   environment. For example, for version 2.1.0:

   .. code-block:: console

      python -m venv .venv-release-check

   In PowerShell:

   .. code-block:: powershell

      .venv-release-check\Scripts\python.exe -m pip install "pymdtools==2.1.0"
      .venv-release-check\Scripts\python.exe -c "import pymdtools; print(pymdtools.__version__)"

   In a POSIX shell:

   .. code-block:: console

      .venv-release-check/bin/python -m pip install "pymdtools==2.1.0"
      .venv-release-check/bin/python -c "import pymdtools; print(pymdtools.__version__)"

Pushing a tag alone does not publish to PyPI: this workflow listens for the
GitHub Release ``published`` event. Saving a draft does not trigger it. Use a
normal stable release for this version; the current workflow does not filter out
published GitHub prereleases, and marking a release as a prerelease does not
change the version embedded in its distributions.

Workflow guarantees
~~~~~~~~~~~~~~~~~~~

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

For branch protection, require ``CI success``, ``CodeQL (python)`` and
``CodeQL (actions)``. The aggregate CI result includes the reusable workflow
validator and fails on unsuccessful or skipped required jobs. CodeQL uses
advanced setup; an existing default setup must first be disabled to avoid
conflicting analysis configurations.

If publication fails
~~~~~~~~~~~~~~~~~~~~

An OIDC/``invalid-publisher`` failure usually requires checking the four PyPI
fields against the workflow and the GitHub environment. A job waiting for an
environment approval has not yet uploaded anything. Inspect the failing job's
log before retrying.

PyPI does not permit replacing a previously used distribution filename. If no
file has been uploaded, correct the service configuration and rerun the workflow
on the same release. If files were already uploaded, check the release contents
before retrying; do not delete and try to re-upload an altered build under the
same version. A code or packaging correction after publication needs a new
version. The build helper never uploads the local ``dist/`` directory: GitHub
builds and validates its own artifacts from the tagged commit.
