File Tools
==========

``pymdtools.filetools`` provides high-level helpers for text files and local
template folders. It builds on ``pymdtools.common`` for path normalization,
file checks, encoding detection, backups, and writes.

Template Helpers
----------------

Template helpers resolve files under a ``template/`` directory next to the
current module or next to a caller-provided ``start_folder``.

.. code-block:: python

   from pymdtools.filetools import get_template_file

   html = get_template_file("emails/welcome.html", start_folder=".")

Template paths are intentionally constrained:

- paths must be relative;
- parent traversal with ``..`` is rejected;
- resolved files must remain inside the ``template/`` directory.

FileName
--------

``FileName`` stores one normalized path and exposes convenient properties for
the complete path, basename, parent directory, and suffix.

.. code-block:: python

   from pymdtools.filetools import FileName

   name = FileName("docs/readme.txt")
   name.filename = "README.md"
   name.filename_ext = ".rst"

``FileName`` only manipulates the stored path value. It does not create, move,
or rename files on disk.

FileContent
-----------

``FileContent`` extends ``FileName`` with an in-memory text buffer.

.. code-block:: python

   from pymdtools.filetools import FileContent

   content = FileContent("README.md")
   text = content.content or ""
   content.content = text.replace("old", "new")
   content.write()

When ``backup`` is enabled, writing over an existing file creates a backup first.

Public API
----------

.. automodule:: pymdtools.filetools
   :members:
   :undoc-members:
   :show-inheritance:
