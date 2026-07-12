Release process
===============

Releases are deliberately split into local validation and remote publication.
No build command pushes Git objects or uploads a package.

Before releasing
----------------

Run the complete validation suite from a clean checkout::

   python -m pytest
   pyright pymdtools scripts/release.py
   sphinx-build -W --keep-going -b html docs docs/_build/html
   python scripts/release.py build

Version and tag
---------------

The release helper updates both version files and creates an annotated local
tag only when the worktree is clean::

   python scripts/release.py bump patch
   git diff -- pymdtools/version.py pymdtools/version.bat
   git add pymdtools/version.py pymdtools/version.bat
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
