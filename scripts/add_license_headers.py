#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Autonomous license header injector.

- Scans recursively from ../ (relative to this script location)
- Adds a centered 79-char MIT header to project-owned files without a notice
- Always excludes third-party resources, license documents and environments
- Supports multiple file types with appropriate comment syntax
- Preserves Python shebang & coding cookie; preserves shebang for .sh
- Default: dry-run. Use --write to apply changes.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Tuple

MARKER = "Author: Florent TOURNOIS | License: MIT"
SCAN_LINES = 150
PROTECTED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "third_party_licenses",
    "layouts",
    "referenced_files",
    "dist",
    "build",
    "_build",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
}
NOTICE_RE = re.compile(
    r"copyright|SPDX-License-Identifier|licen[cs]e\s*[:=]|licensed under|all rights reserved",
    re.IGNORECASE,
)

# PEP 263 coding cookie (must be in line 1 or 2 of file, after optional shebang)
CODING_RE = re.compile(r"^#\s*.*coding[:=]\s*([-\w.]+)", re.IGNORECASE)


# -----------------------------------------------------------------------------
# Comment style registry
# -----------------------------------------------------------------------------
# Each entry defines how to build a header and where to insert it.
# - line_comment: prefix used for line comment headers ("# ", "REM ", etc.)
# - block_comment: (open, close) for block comment headers ("/*", "*/", "<!--", "-->")
# - keep_shebang: preserve "#!" line at top if present
# - keep_coding: preserve coding cookie after shebang (Python only)
# - keep_echo_off: preserve "@ECHO OFF" (bat/cmd)
SUPPORTED = {
    # Python
    ".py": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=True,
        keep_coding=True,
        keep_echo_off=False,
    ),
    # Windows batch
    ".bat": dict(
        line_comment="REM",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=True,
    ),
    ".cmd": dict(
        line_comment="REM",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=True,
    ),
    # Config/text with # comments
    ".conf": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".ini": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".cfg": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".toml": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".yaml": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".yml": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # PowerShell
    ".ps1": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # Shell scripts
    ".sh": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=True,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # Markdown (HTML comment block)
    ".md": dict(
        line_comment=None,
        block_comment=("<!--", "-->"),
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # # JS/TS/CSS (block comment)
    # ".js": dict(line_comment=None, block_comment=("/*", "*/"), keep_shebang=False, keep_coding=False, keep_echo_off=False),
    # ".ts": dict(line_comment=None, block_comment=("/*", "*/"), keep_shebang=False, keep_coding=False, keep_echo_off=False),
    # ".css": dict(line_comment=None, block_comment=("/*", "*/"), keep_shebang=False, keep_coding=False, keep_echo_off=False),
}


def centered_line(prefix: str, text: str, width: int = 79) -> str:
    """
    Build a centered header line of exactly `width` characters, including prefix.
    For line comments:
      prefix is e.g. "#" or "REM"
    """
    prefix = prefix.strip()
    prefix = f"{prefix} "  # ensure single trailing space
    available = width - len(prefix)
    if available <= 0:
        raise ValueError("Prefix too long for requested width")

    left_pad = max(0, (available - len(text)) // 2)
    line = prefix + (" " * left_pad) + text

    if len(line) < width:
        line += " " * (width - len(line))
    else:
        line = line[:width]
    return line


def line_header(prefix: str, width: int = 79) -> Tuple[str, ...]:
    """
    3-line header using line comments, each line exactly `width`.
    """
    if prefix.upper() == "REM":
        sep = "REM " + ("=" * 75)  # 4 + 75 = 79
        mid = centered_line("REM", MARKER, width)
        return (sep, mid, sep)

    # default '#'
    sep = "# " + ("=" * 77)  # 2 + 77 = 79
    mid = centered_line("#", MARKER, width)
    return (sep, mid, sep)


def block_header(open_tok: str, close_tok: str, width: int = 79) -> Tuple[str, ...]:
    """
    Header as a compact block comment.
    Not forced to 79 for open/close lines (they are short), but content line is centered to 79.
    """
    # For block formats, we keep the centered content line with a neutral prefix
    # Example:
    # <!--
    # =============================================================================
    #                 Author: ... | License: MIT
    # =============================================================================
    # -->
    sep = "=" * width
    mid = (" " * max(0, (width - len(MARKER)) // 2)) + MARKER
    mid = mid[:width]
    return (open_tok, sep, mid, sep, close_tok)


def header_for(ext: str) -> Tuple[str, ...]:
    spec = SUPPORTED[ext]
    if spec["line_comment"]:
        return line_header(spec["line_comment"])
    if spec["block_comment"]:
        o, c = spec["block_comment"]
        return block_header(o, c)
    raise ValueError(f"No header style for extension: {ext}")


def is_text_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\x00" in data[:4096]:
        return False
    return True


def marker_present(lines: Iterable[str]) -> bool:
    return any(MARKER in line for line in lines)


def compute_insertion_index(ext: str, lines: list[str]) -> int:
    """
    Insertion policy:
    - Keep shebang line if configured
    - Keep Python coding cookie if configured
    - Keep @ECHO OFF for .bat/.cmd if configured (within first few non-empty lines)
    Otherwise insert at top.
    """
    spec = SUPPORTED[ext]
    i = 0

    if spec.get("keep_shebang") and lines and lines[0].startswith("#!"):
        i = 1

    if ext == ".py" and spec.get("keep_coding"):
        if len(lines) > i and CODING_RE.match(lines[i].rstrip("\n")):
            i += 1

    if spec.get("keep_echo_off"):
        # Find @ECHO OFF early (some files start with blanks)
        for j in range(min(5, len(lines))):
            if lines[j].strip() == "":
                continue
            if lines[j].strip().lower() == "@echo off":
                return j + 1
            break

    return i


def ensure_newline(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"


def process_file(path: Path, write: bool) -> Tuple[bool, str]:
    if (
        path.is_symlink()
        or any(part.lower() in PROTECTED_DIRS for part in path.parts[:-1])
        or path.name.lower().startswith(("license", "licence", "copying", "notice"))
    ):
        return (False, "skip:protected")
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        return (False, "skip:unsupported")

    if not is_text_file(path):
        return (False, "skip:binary")

    try:
        raw = path.read_text(encoding="utf-8", errors="surrogateescape")
    except Exception as e:
        return (False, f"skip:read_error:{e}")

    lines = raw.splitlines(keepends=True)
    head = [line.rstrip("\n") for line in lines[:SCAN_LINES]]

    # Marker already present => keep
    if marker_present(head):
        return (False, "keep:marker_present")

    # A foreign grant or attribution must never be labelled as our own MIT work.
    if NOTICE_RE.search(raw):
        return (False, "keep:license_detected")

    hdr = header_for(ext)
    hdr_lines = [ensure_newline(h) for h in hdr] + [ensure_newline("")]

    idx = compute_insertion_index(ext, lines)
    new_raw = "".join(lines[:idx] + hdr_lines + lines[idx:])

    if not write:
        return (True, "dryrun:would_modify")

    try:
        path.write_text(new_raw, encoding="utf-8", errors="surrogateescape", newline="")
    except Exception as e:
        return (False, f"error:write_error:{e}")

    return (True, "write:modified")


def iter_targets(root: Path, include_hidden: bool) -> Iterable[Path]:
    if any(part.lower() in PROTECTED_DIRS for part in root.parts):
        return
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [
            name
            for name in dirs
            if name.lower() not in PROTECTED_DIRS
            and name.lower() != "tests"
            and not name.lower().endswith(".egg-info")
            and not name.lower().startswith((".pytest_cache", ".pytest_tmp"))
            and (include_hidden or not name.startswith("."))
            and not (Path(directory) / name).is_symlink()
        ]
        for name in files:
            if include_hidden or not name.startswith("."):
                path = Path(directory) / name
                if path.suffix.lower() in SUPPORTED:
                    yield path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Scan ../ and add MIT header if missing (multi-format). Default is dry-run."
    )
    parser.add_argument(
        "--root",
        default=str((Path(__file__).resolve().parent / "..").resolve()),
        help="Root directory to scan (default: ../ relative to this script).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply changes (default: dry-run only).",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden project files; third-party and generated directories stay excluded.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output (print all processed files).",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    mode = "WRITE" if args.write else "DRY-RUN"
    exts = ", ".join(sorted(SUPPORTED.keys()))
    print(f"[START] mode={mode} root={root}")
    print(f"[INFO] supported extensions: {exts}")

    found = kept = modified = skipped = errors = 0

    for path in iter_targets(root, args.include_hidden):
        found += 1
        changed, status = process_file(path, write=args.write)

        if status.startswith("keep:"):
            kept += 1
        elif status.startswith("skip:"):
            skipped += 1
        elif status.startswith("error:"):
            errors += 1
        else:
            modified += 1

        if args.verbose or status.startswith(("error:", "dryrun:", "write:")):
            print(f"{status:18} {path}")

    print("[SUMMARY]")
    print(f"  files matched : {found}")
    print(f"  kept          : {kept}")
    print(f"  modified      : {modified}")
    print(f"  skipped       : {skipped}")
    print(f"  errors        : {errors}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
