"""Validate archives and exercise an installed wheel outside the source tree."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import venv
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile

SMOKE = """
from pathlib import Path
import sys
from pymdtools import __version__
from pymdtools.normalize import md_beautifier
from pymdtools.mdcommon import search_link_in_md_text
from pymdtools.mdcommon import move_base_path_in_md_text, update_links_in_md_text
from pymdtools.instruction import include_files_to_md_file
from pymdtools.mdtopdf import convert_md_to_html
from pymdtools.mdfile import MarkdownContent
from pymdtools.options import IncludeOptions, PdfFeatures
from pymdtools.translation_client import TranslationClient
from pymdtools.translate import translate_md
import pymdtools

assert Path(pymdtools.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert md_beautifier(r"\\[literal](file.md)") == r"\\[literal](file.md)"
assert search_link_in_md_text("[doc](file(v2).md)")[0]["url"] == "file(v2).md"
assert search_link_in_md_text(move_base_path_in_md_text("[doc](<file(.md>)", "docs"))[0]["url"] == "docs/file(.md"
assert update_links_in_md_text("[A](a.md)", [{"name_to_replace": "A", "name": "B", "url": "b.md"}, {"name_to_replace": "B", "name": "C", "url": "c.md"}]) == "[C](c.md)"
client = TranslationClient(lambda text, *args, **kwargs: text)
reference = "[doc][id]\\n\\n[id]: <file(.md>\\n"
assert search_link_in_md_text(translate_md(reference, client=client))[0]["url"] == "file(.md"
assert MarkdownContent(content="# Title", include_options=IncludeOptions()).process_tags() == "# Title"
assert PdfFeatures(metadata={"Title": "Test"}).metadata["Title"] == "Test"
Path("snippet.md").write_text("included", encoding="utf-8")
Path("doc.md").write_text("# Title\\n\\n<!-- include-file(snippet.md) -->\\n", encoding="utf-8")
include_files_to_md_file("doc.md", render_mode="raw")
assert "included" in Path("doc.md").read_text()
assert "<h1>Title</h1>" in convert_md_to_html("doc.md").read_text(encoding="utf-8")
print("Installed wheel functional checks passed:", __version__)
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    (wheel,) = args.directory.resolve().glob("*.whl")
    (sdist,) = args.directory.resolve().glob("*.tar.gz")
    with ZipFile(wheel) as archive:
        for name in (
            "pymdtools/py.typed",
            "pymdtools/layouts/github/page.html",
            "pymdtools/referenced_files/license.txt",
        ):
            assert name in archive.namelist(), name
        metadata = archive.read(
            next(p for p in archive.namelist() if p.endswith("/METADATA"))
        ).decode()
        assert "License-Expression:" in metadata
        assert "pdfkit" not in metadata
        headers = Parser().parsestr(metadata)
        license_files = headers.get_all("License-File", [])
        assert "LICENSES-3rd-party.md" in license_files
        assert "LICENSES-dependencies.md" in license_files
        metadata_name = next(p for p in archive.namelist() if p.endswith("/METADATA"))
        license_root = metadata_name.rsplit("/", 1)[0] + "/licenses/"
        for filename in license_files:
            assert license_root + filename in archive.namelist(), filename
        for page in archive.namelist():
            if page.startswith("pymdtools/layouts/") and page.endswith("/page.html"):
                notice = page.removesuffix("page.html") + "assets/LICENSES.txt"
                assert notice in archive.namelist(), notice
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
        for suffix in (
            "pyproject.toml",
            "uv.lock",
            "tests/mdcommon/test_commonmark_regressions.py",
            "scripts/release.py",
            "src/pymdtools/version.bat",
            "docs/index.rst",
            "tests/fixtures/markdown/parentheses.md",
            "examples/workflows.py",
            "scripts/common.bat",
            "make.bat",
        ):
            assert any(p.endswith("/" + suffix) for p in names), suffix
    with tempfile.TemporaryDirectory(prefix="pymdtools-wheel-") as directory:
        root = Path(directory)
        venv.EnvBuilder(with_pip=True).create(root / "env")
        python = root / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONUTF8"] = "1"
        env["PATH"] = str(python.parent) + os.pathsep + env.get("PATH", "")
        env["VIRTUAL_ENV"] = str(root / "env")
        # No PDF extra: HTML and Markdown must work without browser dependencies.
        subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True, env=env)
        subprocess.run([str(python), "-c", SMOKE], cwd=root, check=True, env=env)
        # Check the installed package, since editable setuptools import hooks are
        # not discoverable by every type checker.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pyright",
                "--pythonpath",
                str(python),
                "--verifytypes",
                "pymdtools",
                "--ignoreexternal",
            ],
            cwd=root,
            check=True,
            env=env,
        )


if __name__ == "__main__":
    main()
