"""Common/ Filesystem: text io."""

from __future__ import annotations

import codecs
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Optional

from ..core import PathInput
from ..datetime_utils import today_utc
from .paths import as_path, check_file, require_str


def create_backup(
    file_path: PathInput,
    *,
    ext: str = ".bak",
    max_tries: int = 100,
    date_prefix: str | None = None,
) -> Path:
    """
    Create a backup copy of a file next to it.

    The backup name is built as:
        <original_name>.<YYYY-MM-DD>-<N><ext>

    Example:
        report.md -> report.md.2026-02-27-1.bak

    Parameters
    ----------
    file_path : str | os.PathLike[str] | Path
        Source file to back up.
    ext : str, default=".bak"
        Backup extension (with or without leading dot).
    max_tries : int, default=100
        Maximum number of candidate names to try before failing.
    date_prefix : str | None, default=None
        Optional override for the date prefix (format not enforced).
        If None, uses today_utc() from your module.

    Returns
    -------
    Path
        Path to the created backup file.

    Raises
    ------
    FileNotFoundError
        If the source file does not exist.
    IsADirectoryError
        If the source path is not a regular file.
    ValueError
        If ext is empty or max_tries is not positive.
    FileExistsError
        If no available backup filename is found within max_tries.
    """
    src = check_file(file_path)  # uses normpath + existence/type checks

    if not ext:
        raise ValueError("ext must not be empty")
    if max_tries <= 0:
        raise ValueError("max_tries must be > 0")

    # Normalize ext format
    if not ext.startswith("."):
        ext = f".{ext}"

    # Date prefix: keep your existing convention
    prefix = date_prefix if date_prefix is not None else today_utc()  # e.g. "2026-02-27"

    # Compose candidates in the same folder
    # Keep the original full name (including suffix) to preserve semantics
    base = src.name  # e.g. "report.md"
    folder = src.parent

    for i in range(1, max_tries + 1):
        backup = folder / f"{base}.{prefix}-{i:03d}{ext}"
        if not backup.exists():
            shutil.copy2(src, backup)
            return backup

    raise FileExistsError(
        f"Unable to find available backup filename for {src} after {max_tries} tries "
        f"(ext={ext!r}, prefix={prefix!r})."
    )


def is_binary_file(
    path: PathInput,
    *,
    sample_size: int = 8192,
    encoding: str | None = None,
) -> bool:
    """
    Determine whether a file appears to be binary.

    A file is considered text if:
    - It starts with a known Unicode BOM
    - It does not contain null bytes
    - It can be decoded as UTF-8 or as common Windows single-byte text

    When *encoding* is provided, that codec is used for the text probe. This
    avoids classifying valid CP1252 or Latin-1 text as binary before it can be
    decoded by :func:`get_file_content`.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        File path.
    sample_size : int, default=8192
        Number of bytes to read for detection.
    encoding : str | None, default=None
        Optional expected text encoding.

    Returns
    -------
    bool
        True if the file appears binary, False otherwise.
    """
    if sample_size <= 0:
        raise ValueError(f"sample_size must be > 0, got: {sample_size}")

    p = check_file(path)

    with p.open("rb") as f:
        chunk = f.read(sample_size)

    if not chunk:
        # Empty file → text
        return False

    # Known BOMs (UTF text encodings)
    BOMS = (
        b"\xef\xbb\xbf",  # UTF-8 BOM
        b"\xff\xfe",  # UTF-16 LE
        b"\xfe\xff",  # UTF-16 BE
        b"\xff\xfe\x00\x00",  # UTF-32 LE
        b"\x00\x00\xfe\xff",  # UTF-32 BE
    )

    if any(chunk.startswith(bom) for bom in BOMS):
        return False

    normalized_encoding = codecs.lookup(encoding).name if encoding is not None else None

    # Null bytes strongly indicate binary except for explicitly requested
    # UTF-16/UTF-32 text without a BOM.
    if b"\x00" in chunk and not (
        normalized_encoding is not None and normalized_encoding.startswith(("utf-16", "utf-32"))
    ):
        return True

    def _decoded_text_is_binary(text: str) -> bool:
        if not text:
            return False
        controls = sum(1 for char in text if not char.isprintable() and char not in "\n\r\t\f")
        return controls / len(text) > 0.30

    if normalized_encoding is not None:
        try:
            return _decoded_text_is_binary(chunk.decode(normalized_encoding))
        except UnicodeDecodeError:
            return True

    try:
        return _decoded_text_is_binary(chunk.decode("utf-8"))
    except UnicodeDecodeError:
        # CP1252 covers the common non-UTF-8 text produced on Windows while
        # still rejecting undefined bytes and control-heavy binary samples.
        try:
            return _decoded_text_is_binary(chunk.decode("cp1252"))
        except UnicodeDecodeError:
            return True


def detect_file_encoding(
    path: PathInput,
    *,
    default: str = "utf-8",
    min_confidence: float = 0.50,
    sample_size: int = 256 * 1024,
    prefer_utf8_sig: bool = True,
) -> str:
    """
    Detect the text encoding of a file using chardet, with BOM handling.

    The function reads up to `sample_size` bytes. If a known Unicode BOM is
    present, it returns the corresponding encoding immediately. Otherwise it
    asks chardet to examine the entire sample and returns the detected encoding
    if the confidence is >= `min_confidence`. If detection is inconclusive,
    it returns `default`.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        File path to inspect.
    default : str, default="utf-8"
        Encoding returned when detection fails or confidence is too low.
    min_confidence : float, default=0.50
        Minimum confidence threshold (0.0..1.0).
    sample_size : int, default=262144
        Number of bytes read from the file (default: 256 KB).
    prefer_utf8_sig : bool, default=True
        If True, returns "utf-8-sig" when a UTF-8 BOM is present; otherwise "utf-8".

    Returns
    -------
    str
        A normalized encoding name (lowercase), or `default` if detection is
        inconclusive.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    IsADirectoryError
        If the path is not a file.
    ValueError
        If `min_confidence` is outside [0.0, 1.0] or sample_size <= 0.
    ImportError
        If chardet is not installed.
    OSError
        For underlying I/O errors.
    """
    if not (0.0 <= min_confidence <= 1.0):
        raise ValueError(f"min_confidence must be within [0.0, 1.0], got: {min_confidence}")
    if sample_size <= 0:
        raise ValueError(f"sample_size must be > 0, got: {sample_size}")

    p = check_file(path)

    with p.open("rb") as f:
        data = f.read(sample_size)

    if not data:
        return default.lower()

    # BOM detection (check longer BOMs first)
    if data.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    if data.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    if data.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if data.startswith(b"\xfe\xff"):
        return "utf-16-be"
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig" if prefer_utf8_sig else "utf-8"

    try:
        import chardet
    except ImportError as ex:
        raise ImportError("chardet is required to detect file encodings") from ex

    # chardet 7 otherwise truncates our sample to its own 200,000-byte default.
    result = chardet.detect(data, max_bytes=len(data))
    enc: Optional[str] = result.get("encoding")
    conf = float(result.get("confidence") or 0.0)

    if not enc or conf < min_confidence:
        return default.lower()

    return enc.lower()


def get_file_content(
    path: PathInput,
    *,
    encoding: str | None = None,
    default_encoding: str = "utf-8",
    min_confidence: float = 0.50,
    sample_size: int = 256 * 1024,
    errors: str = "strict",
    reject_binary: bool = True,
    strip_bom: bool = True,
) -> str:
    """
    Read a text file and return its content, with BOM protection.

    If `encoding` is not provided, the encoding is detected (BOM first,
    then chardet). Optionally rejects binary files and strips leading BOM.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        File path.
    encoding : str | None, default=None
        If provided, this encoding is used directly (no detection).
    default_encoding : str, default="utf-8"
        Default encoding used when detection is inconclusive.
    min_confidence : float, default=0.50
        Minimum confidence threshold for chardet when auto-detecting.
    sample_size : int, default=256*1024
        Number of bytes read for encoding detection.
    errors : str, default="strict"
        Error handler for decoding.
    reject_binary : bool, default=True
        If True, raises ValueError when file appears binary.
    strip_bom : bool, default=True
        If True, removes leading Unicode BOM character (U+FEFF)
        from the decoded content.

    Returns
    -------
    str
        File content as text.
    """
    p = check_file(path)

    enc = encoding
    if enc is None:
        enc = detect_file_encoding(
            p,
            default=default_encoding,
            min_confidence=min_confidence,
            sample_size=sample_size,
        )

    if reject_binary and is_binary_file(p, sample_size=sample_size, encoding=enc):
        raise ValueError(f"Binary file detected: {p}")

    text = p.read_text(encoding=enc, errors=errors)

    if strip_bom and text.startswith("\ufeff"):
        text = text[1:]

    return text


def set_file_content(
    path: PathInput,
    content: str,
    encoding: str = "utf-8",
    bom: bool = False,
    *,
    atomic: bool = True,
    newline: Optional[str] = "\n",
    create_parents: bool = True,
) -> Path:
    """
    Write text content to a file, optionally adding a UTF-8 BOM.
    """
    content = require_str(content, name="content")

    p = as_path(path)
    if create_parents:
        p.parent.mkdir(parents=True, exist_ok=True)

    target = p.resolve(strict=False)

    normalized_encoding = codecs.lookup(encoding).name
    if bom and normalized_encoding not in {"utf-8", "utf-8-sig"}:
        raise ValueError("bom=True is only supported with UTF-8 encodings")
    enc = "utf-8-sig" if bom else ("utf-8" if normalized_encoding == "utf-8-sig" else encoding)

    if not atomic:
        target.write_text(content, encoding=enc, newline=newline)
        return target

    tmp_path: Path | None = None
    existing_mode: int | None = None
    if target.exists():
        existing_mode = stat.S_IMODE(target.stat().st_mode)

    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=str(target.parent),
        )
        tmp_path = Path(tmp_name)

        # Explicit fd -> text stream
        with os.fdopen(fd, "w", encoding=enc, newline=newline) as f:
            f.write(content)

        if existing_mode is not None:
            os.chmod(tmp_path, existing_mode)

        tmp_path.replace(target)
        return target

    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def make_temp_dir(
    *,
    prefix: str = "pymdtools_",
    suffix: str = "",
    dir: PathInput | None = None,
) -> Path:
    """
    Create a temporary directory and return its Path.

    Parameters
    ----------
    prefix : str
        Prefix for the temporary directory name. Defaults to ``"pymdtools_"``.
    suffix : str, default=""
        Suffix for the temporary directory name.
    dir : str | os.PathLike[str] | Path | None, default=None
        Parent directory in which to create the temp directory.
        If None, the system default temp directory is used.

    Returns
    -------
    Path
        Path to the created temporary directory.

    Notes
    -----
    - The directory is created immediately.
    - Caller is responsible for cleanup (e.g. via shutil.rmtree).
    """
    parent = as_path(dir) if dir is not None else None

    tmp = tempfile.mkdtemp(
        prefix=prefix,
        suffix=suffix,
        dir=str(parent) if parent else None,
    )

    return Path(tmp)
