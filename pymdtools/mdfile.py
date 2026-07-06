#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
"""
pymdtools.mdfile
================

High-level wrapper for editable Markdown files.

This module provides :class:`MarkdownContent`, a convenience object that combines
the generic text-file behavior from :class:`pymdtools.filetools.FileContent` with
Markdown-specific helpers from :mod:`pymdtools.instruction` and
:mod:`pymdtools.normalize`.

The wrapper is intentionally stateful. Methods operate on the inherited
in-memory ``content`` buffer, and ``FileContent.write()`` persists that buffer to
disk. Any method that assigns to ``content`` also marks the object as needing a
save through the inherited dirty-flag behavior.

----------------------------------------------------------------------
Public API
----------------------------------------------------------------------

MarkdownContent
    File-backed Markdown buffer with helpers for variables, titles, table of
    contents, include-file directives, beautification, and include processing.

----------------------------------------------------------------------
Supported Markdown helpers
----------------------------------------------------------------------

Variables:
    Mapping-style access to ``<!-- var(NAME)="value" -->`` declarations via
    ``md["NAME"]``, ``md["NAME"] = value``, ``del md["NAME"]``, ``keys()``,
    ``values()`` and ``items()``.

Title:
    ``title`` reads, replaces, or inserts the first level-1 Markdown heading.
    Both ATX and Setext heading styles are handled by
    :mod:`pymdtools.instruction`.

Table of contents:
    ``toc`` renders the current Markdown through Python-Markdown's ``toc``
    extension and returns the generated HTML fragment.

Include files:
    ``set_include_file`` and ``del_include_file`` manage
    ``<!-- include-file(...) -->`` directives.

Processing:
    ``process_tags`` resolves include files, include variables, and include refs
    back into the current buffer.

----------------------------------------------------------------------
Design notes
----------------------------------------------------------------------

- Filesystem behavior, backups, text validation, and encoding detection are
  delegated to :class:`pymdtools.filetools.FileContent`.
- Markdown parsing and marker manipulation are delegated to
  :mod:`pymdtools.instruction`.
- Formatting normalization is delegated to :mod:`pymdtools.normalize`.
- ``content=None`` is treated as an empty Markdown document for convenience
  methods, while preserving the inherited unloaded-buffer representation.

----------------------------------------------------------------------
Usage example
----------------------------------------------------------------------

.. code-block:: python

    from pymdtools.mdfile import MarkdownContent

    md = MarkdownContent("README.md")
    md["author"] = "Ada"
    md.title = "Project README"
    md.process_tags()
    md.write()
"""

from collections.abc import ItemsView, Iterator, KeysView, ValuesView
from typing import Any, cast

import markdown

from . import common
from . import filetools
from . import instruction
from . import normalize

class MarkdownContent(filetools.FileContent):
    """
    Text-file wrapper specialized for Markdown content.

    ``MarkdownContent`` inherits path, read, write, backup, and dirty-flag
    behavior from :class:`pymdtools.filetools.FileContent`. It adds Markdown
    helpers while keeping all edits in the inherited ``content`` buffer.

    Variables declared in the Markdown text can be accessed like a mapping::

        md = MarkdownContent(content='<!-- var(author)="Ada" -->\\n# Doc')
        assert md["author"] == "Ada"
        md["author"] = "Grace"

    ``content=None`` is treated as an empty Markdown document by convenience
    methods. This makes ``MarkdownContent()`` usable as an initially empty
    buffer while still preserving the inherited ``FileContent`` representation
    of unloaded content.

    Keyword arguments are stored and reused by :meth:`process_tags`. They are
    primarily forwarded to :func:`pymdtools.instruction.include_files_to_md_text`
    and related include-file lookup helpers. Two options are interpreted by this
    class:

    - ``search_folders``: optional iterable of folders scanned for refs in
      addition to refs found around ``full_filename``;
    - ``refs_depth``: recursion depth used when scanning ``search_folders``.

    Args:
        filename: Optional file path. If it points to an existing file and
            ``content`` is ``None``, the file is read immediately.
        content: Optional Markdown text to use as the initial buffer. Passing a
            string marks the inherited object as needing a save.
        backup: Whether inherited writes should create backups before
            overwriting existing files.
        encoding: Encoding used when reading an existing file. ``None`` keeps
            the automatic detection behavior provided by ``FileContent``.
        **kwargs: Options reused by include processing, such as
            ``search_folders``, ``relative_paths``, ``include_cwd``,
            ``nb_up_path``, ``error_if_no_file``, ``render_mode`` and
            ``refs_depth``.

    Raises:
        OSError: Propagated from file reading when ``filename`` points to a file.
        ValueError: Propagated from lower-level path or text validation helpers.
        TypeError: If ``content`` is not ``str`` or ``None``.
    """

    def __init__(self, filename: common.PathInput | None = None,
                 content: str | None = None,
                 backup: bool = True,
                 encoding: str | None = None, **kwargs: Any) -> None:
        """
        Initialize a Markdown content wrapper.

        The constructor delegates file/path setup to ``FileContent`` and then
        initializes the cached variable mapping used by mapping-style access.
        The cache is refreshed lazily whenever the Markdown text changes.
        """

        filetools.FileContent.__init__(self,
                                       content=content,
                                       filename=filename,
                                       backup=backup,
                                       encoding=encoding)

        self.__var_dict = {}
        self.__var_dict_text = None
        self.__kwargs = kwargs

    def __content_or_empty(self) -> str:
        """
        Return the current Markdown text, using ``""`` for unloaded content.

        ``FileContent`` allows ``content`` to be ``None``. Markdown text helpers
        expect strings, so this method centralizes the compatibility choice made
        by ``MarkdownContent``: an unloaded buffer behaves like an empty document
        for Markdown operations.
        """
        return self.content if self.content is not None else ""

    def __include_kwargs(self) -> dict[str, Any]:
        """
        Return keyword arguments forwarded to include-file processing.

        ``refs_depth`` is consumed by :meth:`__collect_refs` and is not accepted
        by :func:`pymdtools.instruction.include_files_to_md_text`, so it is
        removed from the forwarded options.
        """
        return {
            key: value
            for key, value in self.__kwargs.items()
            if key not in ("refs_depth",)
        }

    def __update_dict(self) -> None:
        """
        Refresh the cached Markdown variable dictionary when content changed.

        The cache stores values returned by
        :func:`pymdtools.instruction.get_vars_from_md_text`. Duplicate variables
        or malformed values raise the same exceptions as that helper.
        """
        content = self.__content_or_empty()
        if self.__var_dict_text != content:
            self.__var_dict = instruction.get_vars_from_md_text(content)
            self.__var_dict_text = content

    def __setitem__(self, key: str, item: str) -> None:
        """
        Set or insert a Markdown variable declaration.

        Args:
            key: Variable name used in ``<!-- var(KEY)="..." -->``.
            item: Interpreted string value. The value is escaped before being
                written back into the Markdown text.

        Raises:
            TypeError: If ``key`` or ``item`` is not a string.
            ValueError: If ``key`` is not a valid variable name.
        """
        self.content = instruction.set_var_to_md_text(self.__content_or_empty(),
                                                      key, item)
        self.__update_dict()

    def __getitem__(self, key: str) -> str:
        """
        Return the value of a Markdown variable.

        Args:
            key: Variable name to look up.

        Raises:
            KeyError: If the variable is not declared in the current content.
            ValueError: If duplicate variable declarations are found.
        """
        self.__update_dict()
        return self.__var_dict[key]

    def __delitem__(self, key: str) -> None:
        """
        Remove Markdown variable declarations for ``key``.

        Args:
            key: Variable name to remove.

        Raises:
            TypeError: If ``key`` is not a string.
            ValueError: If ``key`` is not a valid variable name.
        """
        self.content = instruction.del_var_to_md_text(self.__content_or_empty(),
                                                      key)
        self.__update_dict()

    def has_key(self, k: str) -> bool:
        """
        Return whether a Markdown variable exists.

        This method is kept for backward compatibility with older callers.
        Prefer ``key in markdown_content`` in new code.

        Args:
            k: Variable name to test.
        """
        self.__update_dict()
        return k in self.__var_dict

    def keys(self) -> KeysView[str]:
        """
        Return a dynamic view of declared variable names.

        The variable cache is refreshed before the view is returned.
        """
        self.__update_dict()
        return self.__var_dict.keys()

    def values(self) -> ValuesView[str]:
        """
        Return a dynamic view of declared variable values.

        Values are interpreted strings; escape sequences in variable
        declarations have already been decoded by ``instruction``.
        """
        self.__update_dict()
        return self.__var_dict.values()

    def items(self) -> ItemsView[str, str]:
        """
        Return a dynamic view of ``(name, value)`` variable pairs.

        The variable cache is refreshed before the view is returned.
        """
        self.__update_dict()
        return self.__var_dict.items()

    def __contains__(self, item: object) -> bool:
        """
        Return whether ``item`` is a declared Markdown variable name.
        """
        self.__update_dict()
        return item in self.__var_dict

    def __iter__(self) -> Iterator[str]:
        """
        Iterate over declared Markdown variable names.

        Iteration order follows the order produced by the underlying dictionary,
        which mirrors the discovery order from ``instruction``.
        """
        self.__update_dict()
        return iter(self.__var_dict)

    @property
    def title(self) -> str | None:
        """
        Return the first level-1 Markdown title, or ``None`` when absent.

        Both ATX (``# Title``) and Setext (``Title`` followed by ``===``)
        styles are supported by the lower-level instruction helper.
        """
        return cast(
            str | None,
            instruction.get_title_from_md_text(self.__content_or_empty()),
        )

    @title.setter
    def title(self, value: str) -> None:
        """
        Replace or insert the first level-1 Markdown title.

        Args:
            value: New title text. It must be a non-empty string after
                stripping.

        Raises:
            TypeError: If ``value`` is not a string.
            ValueError: If ``value`` is empty or if the title style requested by
                the lower-level helper is invalid.
        """
        self.content = instruction.set_title_in_md_text(self.__content_or_empty(),
                                                        value)

    @property
    def toc(self) -> str:
        """
        Return an HTML table of contents generated from the current Markdown.

        The property uses Python-Markdown with the ``toc`` extension and returns
        the extension-generated HTML fragment. Empty content returns an empty
        string.
        """
        md_reader = markdown.Markdown(extensions=['toc'])
        md_reader.convert(self.__content_or_empty())
        return cast(str, getattr(md_reader, "toc", ""))

    def set_include_file(self, filename: str) -> None:
        """
        Ensure an ``include-file`` directive exists in the Markdown text.

        If the directive already exists, the content is left unchanged. If not,
        the directive is inserted according to
        :func:`pymdtools.instruction.ensure_include_file_in_md_text`.

        Args:
            filename: Referenced file name as it should appear in
                ``<!-- include-file(filename) -->``.

        Raises:
            TypeError: If the current content or ``filename`` is invalid.
            ValueError: If ``filename`` is empty.
        """
        self.content = instruction.ensure_include_file_in_md_text(
            self.__content_or_empty(),
            filename)
        self.__update_dict()

    def del_include_file(self, filename: str) -> None:
        """
        Remove ``include-file`` directives that reference ``filename``.

        Args:
            filename: Referenced file name to remove.

        Raises:
            TypeError: If the current content or ``filename`` is invalid.
            ValueError: If ``filename`` is empty.
        """
        self.content = instruction.del_include_file_to_md_text(
            self.__content_or_empty(),
            filename)
        self.__update_dict()

    def beautify(self) -> str:
        """
        Normalize Markdown formatting in the current buffer.

        The operation delegates to :func:`pymdtools.normalize.md_beautifier`,
        stores the normalized text back into ``content``, and returns it.

        Returns:
            The normalized Markdown text.
        """
        self.content = normalize.md_beautifier(self.__content_or_empty())
        return self.content

    def __collect_refs(self) -> dict[str, str]:
        """
        Collect include refs available to :meth:`process_tags`.

        Refs are discovered in two steps:

        1. If ``full_filename`` is known, scan Markdown files in the same folder
           tree using :func:`pymdtools.instruction.get_refs_around_md_file`.
        2. If ``search_folders`` was passed to the constructor, scan those
           folders and merge their refs into the previous result.

        Returns:
            A dictionary mapping ref names to replacement Markdown content.
        """
        refs: dict[str, str] = {}

        if self.full_filename is not None:
            refs = instruction.get_refs_around_md_file(
                self.full_filename,
                filename_ext=self.filename_ext or ".md",
                depth_up=0,
                depth_down=-1)

        search_folders = self.__kwargs.get("search_folders")
        if search_folders:
            refs = instruction.get_refs_from_search_folders(
                search_folders,
                refs=refs,
                filename_ext=self.filename_ext or ".md",
                depth=cast(int, self.__kwargs.get("refs_depth", -1)))

        return refs

    def process_tags(self) -> str:
        """
        Resolve include-related directives in the current Markdown buffer.

        Processing happens in this order:

        1. ``include-file`` directives are replaced by file content.
        2. ``begin-var``/``end-var`` blocks are filled from local variable
           declarations.
        3. ``begin-include``/``end-include`` blocks are filled from refs found
           around the current file and optional ``search_folders``.

        The resulting text is stored back into ``content`` and returned.

        Returns:
            The processed Markdown text.

        Raises:
            OSError: If an included file or scanned ref file cannot be read.
            KeyError: If a variable or include ref is requested but missing and
                the corresponding lower-level helper is configured to fail.
            ValueError: If include markers are malformed.
        """
        self.content = instruction.include_files_to_md_text(
            self.__content_or_empty(),
            **self.__include_kwargs())
        self.content = instruction.search_include_vars_to_md_text(self.content)

        refs = self.__collect_refs()
        self.content = instruction.include_refs_to_md_text(self.content, refs)
        self.__update_dict()

        return self.content
