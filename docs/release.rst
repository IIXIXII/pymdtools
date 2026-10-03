Release process
===============

Pushing an annotated ``vX.Y.Z`` tag starts the whole publication process:
GitHub Actions validates the release, publishes to PyPI, then creates the GitHub
release with changelog notes and both distribution archives attached. There is
no GitHub release to create manually and no local PyPI upload command.

Prepare and publish
-------------------

First commit your changes, including their notes under ``## Unreleased`` in
``CHANGELOG.md``. From a clean checkout, prepare the next version::

   uv run --no-sync python scripts/release.py prepare patch

Use ``minor`` for a feature release or ``major`` for a breaking release. The
command updates both version files, dates the release, moves the Unreleased
notes under the new version, and leaves an empty Unreleased section for future
changes. It refuses an empty or duplicate section and mismatched version files.
It does not commit, tag, push or upload anything.

Review the resulting version and notes, then commit the three files::

   git diff -- src/pymdtools/version.py src/pymdtools/version.bat CHANGELOG.md
   git add src/pymdtools/version.py src/pymdtools/version.bat CHANGELOG.md
   git commit -m "chore(release): prepare X.Y.Z"

Replace ``X.Y.Z`` with the printed version. Push this commit through the normal
branch/PR process and wait for ``CI success``, ``CodeQL (python)`` and
``CodeQL (actions)``. If a PR is squash-merged or rebased, update your local
checkout to the resulting commit before tagging it.

From that clean checkout, create the annotated tag::

   uv run --no-sync python scripts/release.py tag

The helper prints the exact push command. Run it when ready to publish::

   git push origin vX.Y.Z

Follow **Actions > Publish release** and approve the ``pypi`` environment if it
requires a reviewer. After the workflow succeeds, check the version on PyPI and
its GitHub release, then install ``pymdtools==X.Y.Z`` in a fresh virtual
environment and confirm ``pymdtools.__version__``.

If the version and dated notes are already prepared, skip ``prepare``. If the
tag already exists on this exact commit, use ``scripts/release.py verify-tag``
and push it without creating it again. Never force-update a published tag or
push every local tag with ``--tags``.

.. important::

   The tagged commit must contain the new workflow. Existing tags retain their
   original workflow: pushing an already-remote tag does not start a new run.
   For a tag made before this change, follow its original process (publish a
   GitHub release to trigger publication), or include this automation in the
   next version. Do not move an existing release tag onto a newer commit.

One-time service configuration
------------------------------

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

Workflow guarantees
-------------------

The workflow only listens for version tag pushes, so creating the GitHub
release cannot trigger a second PyPI publication. It checks that the tag is
annotated, points at the event commit and matches both version files. It also
requires nonempty dated notes for that version in ``CHANGELOG.md``.
Before building, it refuses commits outside ``origin/master`` and requires the
latest CI and CodeQL **push** runs on ``master`` for that exact commit to have
completed successfully. Pull-request, scheduled and older successful runs do
not substitute for a missing, failed or still-running push run. Wait for both
workflows before pushing the tag; an early tag can be retried after they finish.
The helper currently supports stable ``major.minor.patch`` versions only.

A job without publishing credentials tests and builds the distributions; a
separate protected job receives only those artifacts and publishes them through
PyPI trusted publishing. A third job creates the GitHub release only after PyPI
publication succeeds. Its repository write permission is confined to that job;
it does not check out or execute package code.

The build checks out the event's immutable commit and verifies the annotated
tag against it. It reruns workflow validation, lint, types, dependency auditing,
license-notice checks, documentation and its offline examples, tests and the
installed-wheel checks.
Shared dependency caches are disabled for release jobs. The publishing job
downloads the artifact by the build job's artifact ID, fails on a digest
mismatch, and enables PyPI's PEP 740 attestations. The GitHub release receives
the same wheel and source archive, plus validated notes from a separate
artifact, also retrieved by ID with a digest check. The notes include migration
instructions and fenced examples from the matching changelog section.

For branch protection, require ``CI success``, ``CodeQL (python)`` and
``CodeQL (actions)``. The aggregate CI result includes the reusable workflow
validator and fails on unsuccessful or skipped required jobs. CodeQL uses
advanced setup; an existing default setup must first be disabled to avoid
conflicting analysis configurations.

Repository protections
----------------------

The versioned definitions in ``.github/rulesets/master.json`` and
``.github/rulesets/release-tags.json`` are the reference for repository settings.
The master rules require a pull request, resolved conversations, an up-to-date
branch and ``CI success``, ``CodeQL (python)`` and ``CodeQL (actions)`` from GitHub
Actions. No approval count is imposed on this single-maintainer project, so the
maintainer can merge their own PR after the checks pass. Force pushes and
branch deletion are blocked. Existing ``v*`` tags cannot be updated or deleted.
There is no ruleset bypass actor.

These rulesets, release immutability and private vulnerability reporting were
activated on 2026-10-03. Review the live settings when administering the repository.

Enable **Settings > General > Releases > Enable release immutability** for
future GitHub releases. Existing published releases are not retroactively
changed. The GitHub CLI creates a draft, attaches the archives, then publishes
it; immutable releases prevent later replacement of assets or movement of the
release tag. See `GitHub's release protection documentation
<https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes>`_.

A repository administrator can import these JSON definitions through
**Settings > Rules > Rulesets > Import a ruleset**. Check for existing rulesets
first to avoid duplicating them. Local JSON files describe the policy; GitHub
settings enforce it. Enable private vulnerability reporting under
**Settings > Code security** and follow the repository's ``SECURITY.md`` policy.

If publication fails
--------------------

An OIDC/``invalid-publisher`` failure usually requires checking the four PyPI
fields against the workflow and the GitHub environment. A job waiting for an
environment approval has not yet uploaded anything. Inspect the failing job's
log before retrying. Prefer **Re-run failed jobs** on the original workflow run:
this preserves successful jobs and their artifacts.

If only the GitHub release job failed, PyPI publication has already succeeded.
Retry only failed jobs; do not rerun the successful publishing job. If the CLI
left a partial draft, inspect its assets and finish that draft manually. If a
release already exists, inspect it instead of replacing its notes or assets.

PyPI does not permit replacing a previously used distribution filename. If no
file has been uploaded, correct the service configuration and rerun failed jobs
on the same tag. If files were already uploaded, check the release contents
before retrying; do not delete and try to re-upload an altered build under the
same version. A code or packaging correction after publication needs a new
version. The build helper never uploads the local ``dist/`` directory: GitHub
builds and validates its own artifacts from the tagged commit.

Local validation and advanced helpers
-------------------------------------

The publication workflow reruns validation. For local checks before sending a
release commit, see :doc:`contributing`. To inspect release notes or archives::

   uv run --no-sync python scripts/release.py check
   uv run --no-sync python scripts/release.py notes
   uv run --no-sync python scripts/release.py build
   uv run --no-sync python scripts/check_distribution.py dist

``build`` rebuilds ``dist/`` and checks both archives with Twine. It requires a
clean tree unless ``--allow-dirty`` is explicitly used for local validation.
The isolated build uses uv from the locked development group and pins setuptools
with ``build-constraints.txt``. Update this constraint deliberately alongside
packaging changes and validate both archives. The wheel is built from the sdist.
The installed-wheel checker needs network access for dependencies. Neither
command publishes anything.

``bump patch|minor|major`` remains available for updating version files alone;
maintainers must then date and edit their changelog section themselves.
``audit-tags`` reports historical tag/version mismatches without changing them.
