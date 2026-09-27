from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "add_license_headers.py"


@pytest.mark.parametrize("include_hidden", [False, True])
def test_header_tool_preserves_foreign_notices_and_excluded_resources(
    tmp_path: Path, include_hidden: bool
) -> None:
    preserved = {
        "LICENSE.md": "Terms of a license.\n",
        "THIRD_PARTY_LICENSES/upstream.md": "Upstream terms.\n",
        "src/pymdtools/layouts/sample/credits.md": "Theme credits.\n",
        "src/pymdtools/referenced_files/license.md": "Document notice.\n",
        ".git/helper.py": "git_data = True\n",
        ".venv/helper.py": "dependency_data = True\n",
        "build/module.py": "generated = True\n",
        "docs/_build/index.md": "Generated documentation.\n",
        "project.egg-info/helper.py": "generated = True\n",
        "foreign.py": "# Copyright 2020 Another Author\nvalue = 1\n",
        "spdx.py": "# SPDX-License-Identifier: Apache-2.0\nvalue = 2\n",
        "late_notice.py": "\n" * 160 + "# Copyright Another Author\nvalue = 3\n",
    }
    for relative, content in preserved.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    original = tmp_path / "src" / "project.py"
    original.write_text("answer = 42\n", encoding="utf-8")
    workflow = tmp_path / ".github" / "workflows" / "check.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: Check\n", encoding="utf-8")

    command = [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--write"]
    if include_hidden:
        command.append("--include-hidden")
    subprocess.run(command, check=True, capture_output=True, text=True)

    assert "Author: Florent TOURNOIS | License: MIT" in original.read_text(encoding="utf-8")
    for relative, content in preserved.items():
        assert (tmp_path / relative).read_text(encoding="utf-8") == content, relative
    assert ("License: MIT" in workflow.read_text(encoding="utf-8")) is include_hidden


def test_header_tool_defaults_to_a_nonmutating_preview(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    content = "answer = 42\n"
    path.write_text(content, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "dryrun:would_modify" in result.stdout
    assert path.read_text(encoding="utf-8") == content
