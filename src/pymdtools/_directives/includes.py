"""Directives: includes."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import (
    Any,
    Iterable,
    Optional,
    Sequence,
)

from .. import common
from ..mdcommon import markdown_code_ranges
from ._shared import (
    INCLUDE_FILE_RE,
    IncludeRenderMode,
    RegexInput,
    compile_pattern,
    create_backup,
    directive_matches,
    is_non_empty_str,
    read_md_text,
    require_str,
    search_outside_ranges,
)

logger: logging.Logger = logging.getLogger(__name__)


def get_file_content_to_include(
    filename: common.PathInput,
    *,
    search_folders: Optional[Iterable[common.PathInput]] = None,
    include_cwd: bool = False,
    relative_paths: Sequence[str] = (".", "referenced_files"),
    nb_up_path: int = 0,
    encoding: Optional[str] = None,
) -> str:
    """
    Retrieve the content of a referenced file to include.

    The function searches `filename` using `common.find_file` starting from:
      - the directory containing this module,
      - optionally the current working directory,
      - and any additional folders provided via `search_folders`.

    Search is performed within `relative_paths` under each start point, and can
    traverse up to `nb_up_path` parent levels.

    Args:
        filename: Referenced filename (typically relative, e.g. "snippet.md").
        search_folders: Additional start points for the search.
        include_cwd: Whether to include the current working directory as a start point.
        relative_paths: Relative subpaths to probe under each start point.
        nb_up_path: Number of parent levels to traverse during the search.
        encoding: Encoding for reading. ``None`` triggers auto-detection.

    Returns:
        File content as text.

    Raises:
        Exception: Propagated if the file cannot be found or read.
    """
    requested = str(filename)
    requested_path = Path(requested)

    if (
        os.path.isabs(requested)
        or requested_path.is_absolute()
        or bool(requested_path.drive)
        or requested.startswith(("/", "\\"))
        or ".." in requested_path.parts
    ):
        raise ValueError(f"invalid referenced filename: {requested!r}")

    module_dir = Path(__file__).resolve().parents[1]
    start_paths: list[Path] = []
    if search_folders:
        start_paths.extend(Path(path).resolve() for path in search_folders)
    if include_cwd:
        start_paths.append(Path.cwd().resolve())
    start_paths.append(module_dir)

    unique_start_paths = list(dict.fromkeys(start_paths))
    start_points = [str(path) for path in unique_start_paths]

    logger.debug(
        "Include-file lookup: filename=%r start_points=%r relative_paths=%r nb_up_path=%d",
        requested,
        start_points,
        list(relative_paths),
        nb_up_path,
    )

    found = common.find_file(
        requested,
        start_points,
        list(relative_paths),
        max_up=nb_up_path,
    )

    resolved_found = Path(found).resolve()
    # Explicit parent traversal grants access to those search anchors too.
    # Keep the post-search containment check for symlinks and custom finders.
    allowed_roots = {
        anchor for root in unique_start_paths for anchor in (root, *root.parents[:nb_up_path])
    }
    if not any(
        resolved_found == root or resolved_found.is_relative_to(root) for root in allowed_roots
    ):
        raise ValueError(f"included file resolves outside the allowed roots: {requested!r}")

    logger.debug("Include-file resolved: %r -> %r", requested, resolved_found)
    return read_md_text(resolved_found, encoding)


def include_files_to_md_text(
    text: str,
    *,
    include_file_re: RegexInput = INCLUDE_FILE_RE,
    error_if_no_file: bool = True,
    render_mode: IncludeRenderMode = "box",
    **kwargs: Any,
) -> str:
    """
    Replace include-file directives with the content of referenced files.

    The directive must match `include_file_re` and provide a group 'name'
    containing the referenced filename.

    Args:
        text: Markdown text.
        include_file_re: Regex to match include-file directives (must capture 'name').
        error_if_no_file: If False, keep the directive unchanged when the file is not found/readable.
        render_mode: "box" to wrap content in an ASCII box, "raw" to insert content as-is.
        **kwargs: Forwarded to `get_file_content_to_include` (e.g. search_folders).

    Returns:
        Updated markdown text.
    """
    pattern = compile_pattern(include_file_re)

    text = require_str(text, "text")
    code_ranges = markdown_code_ranges(text)
    result_parts: list[str] = []
    pos = 0

    while True:
        m = search_outside_ranges(pattern, text, pos, code_ranges)
        if not m:
            result_parts.append(text[pos:])
            break

        filename = m.group("name")
        logger.debug("Find include-file(%s)", filename)

        result_parts.append(text[pos : m.start()])

        try:
            file_text = get_file_content_to_include(filename, **kwargs)
        except Exception:
            if error_if_no_file:
                raise
            # keep original directive unchanged
            result_parts.append(text[m.start() : m.end()])
            pos = m.end()
            continue

        # Normalize newlines
        file_text = file_text.replace("\r\n", "\n").replace("\r", "\n")

        if render_mode == "raw":
            replacement = file_text
        else:
            # box mode (deterministic)
            left = "| "
            boxed = left + file_text.replace("\n", "\n" + left)
            top = "+" + "-" * 77 + "+"
            replacement = f"<!-- include-file({filename})\n{top}\n{boxed}\n{top} -->"

        result_parts.append(replacement)
        pos = m.end()

    return "".join(result_parts)


def include_files_to_md_file(
    filename: common.PathInput,
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    read_encoding: Optional[str] = None,
    write_encoding: str = "utf-8",
    error_if_no_file: bool = True,
    render_mode: IncludeRenderMode = "box",
    **kwargs: Any,
) -> str:
    """
    Apply include-file substitutions to a markdown file in-place.

    Args:
        filename: Markdown file to process.
        backup_option: Create a backup before writing.
        backup_ext: Backup extension.
        filename_ext: Expected markdown extension.
        read_encoding: Encoding to read. ``None`` triggers auto-detection.
        write_encoding: Encoding used to write.
        error_if_no_file: If False, keep unresolved directives unchanged.
        render_mode: Forwarded to include_files_to_md_text (e.g. "box" or "raw").
        **kwargs: Forwarded to get_file_content_to_include (e.g. search_folders).

    Returns:
        Normalized filename.
    """
    logger.debug("Include file to the file %s", filename)
    checked = common.check_file(str(filename), filename_ext)

    text = read_md_text(checked, read_encoding)

    if backup_option:
        create_backup(checked, backup_ext)

    configured_search_folders = kwargs.get("search_folders")
    search_folders = [] if configured_search_folders is None else list(configured_search_folders)
    document_folder = Path(checked).resolve().parent
    kwargs["search_folders"] = [
        document_folder,
        *(folder for folder in search_folders if Path(folder).resolve() != document_folder),
    ]
    kwargs.setdefault("include_cwd", False)
    kwargs.setdefault("nb_up_path", 0)

    text = include_files_to_md_text(
        text,
        error_if_no_file=error_if_no_file,
        render_mode=render_mode,
        **kwargs,
    )

    common.set_file_content(checked, text, encoding=write_encoding)
    return str(checked)


def ensure_include_file_in_md_text(
    text: str,
    filename: str,
    *,
    include_file_re: RegexInput = INCLUDE_FILE_RE,
) -> str:
    """
    Ensure that an `include-file(filename)` directive exists in the markdown text.

    The directive is appended after the last existing include-file directive.
    If no include-file directives exist, it is inserted at the beginning of the text.

    Args:
        text: Markdown text.
        filename: Referenced file name as used in include-file(...).
        include_file_re: Regex matching include-file directives; must capture group 'name'.

    Returns:
        Updated markdown text.
    """
    text = require_str(text, "text")
    if not is_non_empty_str(filename, strip=True):
        raise ValueError("filename must be a non-empty string")

    # Normalize newlines (optional but helps determinism)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    pattern = compile_pattern(include_file_re)

    # If already present, return as-is
    matches = directive_matches(pattern, normalized)
    for m in matches:
        if m.group("name") == filename:
            return normalized

    directive = f"<!-- include-file({filename}) -->"

    if not matches:
        # insert at beginning
        if normalized and not normalized.startswith("\n"):
            return directive + "\n\n" + normalized
        return directive + "\n\n" + normalized

    # append after the last include-file directive
    last = matches[-1]
    insert_at = last.end()

    before = normalized[:insert_at]
    after = normalized[insert_at:]

    # ensure spacing
    if not before.endswith("\n"):
        before += "\n"
    if after and not after.startswith("\n"):
        # keep a blank line between directives and content
        insertion = directive + "\n\n"
    else:
        insertion = directive + "\n"

    return before + insertion + after


def get_include_file_list(
    text: str,
    *,
    include_file_re: RegexInput = INCLUDE_FILE_RE,
    unique: bool = False,
) -> list[str]:
    """
    Return the list of filenames referenced by include-file(...) directives.

    Args:
        text: Markdown text.
        include_file_re: Regex matching include-file directives; must capture group 'name'.
        unique: If True, remove duplicates while preserving first-seen order.

    Returns:
        A list of referenced filenames, in appearance order.
    """
    pattern = compile_pattern(include_file_re)

    text = require_str(text, "text")
    names = [m.group("name") for m in directive_matches(pattern, text)]

    if not unique:
        return names

    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def del_include_file_to_md_text(
    text: str,
    filename: str,
    *,
    include_file_re: RegexInput = INCLUDE_FILE_RE,
    first_only: bool = False,
) -> str:
    """
    Remove include-file directives referencing `filename` from markdown text.

    Args:
        text: Markdown text.
        filename: Target referenced filename to remove.
        include_file_re: Regex matching include-file directives; must capture group 'name'.
        first_only: If True, remove only the first matching directive.

    Returns:
        Updated markdown text.
    """
    text = require_str(text, "text")
    if not is_non_empty_str(filename):
        raise ValueError("filename must be a non-empty string")

    pattern = compile_pattern(include_file_re)

    out_parts: list[str] = []
    pos = 0
    removed = False

    for m in directive_matches(pattern, text):
        name = m.group("name")
        if name == filename and (not first_only or not removed):
            # keep everything before the match, skip the match
            out_parts.append(text[pos : m.start()])
            pos = m.end()
            removed = True
        # else: keep scanning; do not append yet (handled by pos slices)

    out_parts.append(text[pos:])
    return "".join(out_parts)
