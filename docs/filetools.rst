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

   template_path = get_template_file("emails/welcome.html", start_folder=".")

This returns a path to an existing template, not its content. Read it with
``common.get_file_content(template_path)``. The example expects a file at
``template/emails/welcome.html`` under the chosen start folder. Example 15 in
:doc:`workflows` supplies a complete template directory.

Template paths are intentionally constrained:

- paths must be relative;
- parent traversal with ``..`` is rejected;
- resolved files must remain inside the ``template/`` directory.

FileName
--------

``FileName`` stores one normalized path and exposes convenient properties for
the complete path, basename, parent directory, and suffix.

.. testcode::

   from pymdtools.filetools import FileName

   name = FileName("docs/readme.txt")
   name.filename = "README.md"
   name.filename_ext = ".rst"

``FileName`` only manipulates the stored path value. It does not create, move,
or rename files on disk.

FileContent
-----------

``FileContent`` extends ``FileName`` with an in-memory text buffer.

.. testcode::

   from pymdtools.filetools import FileContent

   content = FileContent(content="Welcome to the old guide.\n")
   content.write("build/welcome.txt")
   content.content = (content.content or "").replace("old", "new")
   assert content.save_needed
   content.write()
   assert not content.save_needed
   assert FileContent("build/welcome.txt").content == "Welcome to the new guide.\n"

``backup=True`` is the default: writing over an existing file creates a dated
backup first. Reads use encoding detection unless ``encoding`` is supplied;
writes default to UTF-8 and create parent directories. ``content=None`` means
unloaded content and cannot be written. Assign ``""`` for an intentionally empty
file. ``write(filename)`` changes the stored path only after a successful write.

Public API
----------

.. automodule:: pymdtools.filetools
   :members:
   :undoc-members:
   :show-inheritance:
