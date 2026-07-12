from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _assert_action_version(text: str, action: str, minimum: tuple[int, int, int]) -> None:
    matches = re.findall(rf"{re.escape(action)}@v(\d+)\.(\d+)\.(\d+)", text)
    assert matches, f"{action} must use an exact semantic version"
    assert all(tuple(map(int, match)) >= minimum for match in matches)


def _setup_kwargs() -> dict[str, Any]:
    tree = ast.parse((ROOT / "setup.py").read_text(encoding="utf-8"))
    setup_call = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setup"
    )
    wanted = {"install_requires", "extras_require"}
    return {
        keyword.arg: ast.literal_eval(keyword.value)
        for keyword in setup_call.keywords
        if keyword.arg in wanted
    }


def _requirements(name: str) -> tuple[list[str], list[str]]:
    requirements: list[str] = []
    includes: list[str] = []
    for raw_line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            includes.append(line[3:].strip())
        else:
            requirements.append(line)
    return requirements, includes


def test_requirement_files_match_setup_metadata() -> None:
    setup = _setup_kwargs()
    runtime, runtime_includes = _requirements("requirements.txt")
    development, development_includes = _requirements("requirements-dev.txt")
    documentation, documentation_includes = _requirements("requirements-docs.txt")

    assert runtime == setup["install_requires"]
    assert development == setup["extras_require"]["dev"]
    assert documentation == setup["extras_require"]["docs"]
    assert runtime_includes == []
    assert development_includes == ["requirements.txt"]
    assert documentation_includes == ["requirements.txt"]


def test_packaging_is_declarative_and_carries_license_inventory() -> None:
    setup_text = (ROOT / "setup.py").read_text(encoding="utf-8")
    setup_cfg = (ROOT / "setup.cfg").read_text(encoding="utf-8")

    assert "cmdclass" not in setup_text
    assert "os.system" not in setup_text
    assert "upload" not in setup_text.lower()
    assert "LICENSE.md" in setup_cfg
    assert "LICENSES-3rd-party.md" in setup_cfg
    assert "THIRD_PARTY_LICENSES/*" in setup_cfg
    assert (ROOT / "LICENSE.md").is_file()
    assert (ROOT / "LICENSES-3rd-party.md").is_file()
    assert {path.name for path in (ROOT / "THIRD_PARTY_LICENSES").iterdir()} >= {
        "Apache-2.0.txt",
        "BSD-3-Clause.txt",
        "GPL-3.0.txt",
        "LGPL-3.0.txt",
        "MIT.txt",
        "Unlicense.txt",
    }


def test_pyright_configuration_is_ci_portable() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"scripts/release.py"' in pyproject
    assert "venvPath" not in pyproject
    assert '\nvenv = "' not in pyproject


def test_ci_uses_current_actions_and_an_isolated_wheel_smoke_test() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    _assert_action_version(workflow, "actions/checkout", (7, 0, 0))
    _assert_action_version(workflow, "actions/setup-python", (6, 2, 0))
    _assert_action_version(workflow, "actions/upload-artifact", (7, 0, 1))
    assert 'python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]' in workflow
    assert "pymdtools-wheel-smoke" in workflow
    assert "python scripts/release.py build\n" in workflow


def test_publish_keeps_build_code_away_from_oidc_credentials() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    build_section, publish_section = workflow.split("\n  publish:\n", maxsplit=1)

    _assert_action_version(workflow, "actions/checkout", (7, 0, 0))
    _assert_action_version(workflow, "actions/setup-python", (6, 2, 0))
    _assert_action_version(workflow, "actions/upload-artifact", (7, 0, 1))
    _assert_action_version(workflow, "actions/download-artifact", (7, 0, 0))
    _assert_action_version(workflow, "pypa/gh-action-pypi-publish", (1, 14, 0))
    assert "id-token: write" not in build_section
    assert "actions/upload-artifact@" in build_section
    assert "RELEASE_TAG: ${{ github.event.release.tag_name }}" in build_section
    assert 'verify-tag "$RELEASE_TAG"' in build_section
    assert "id-token: write" in publish_section
    assert "actions/checkout" not in publish_section
    assert "python -m build" not in publish_section
    assert "actions/download-artifact@" in publish_section
    assert "pypa/gh-action-pypi-publish@" in publish_section


def test_dependabot_tracks_python_and_action_dependencies() -> None:
    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert "package-ecosystem: pip" in dependabot
    assert "package-ecosystem: github-actions" in dependabot
    assert dependabot.count("interval: weekly") == 2


def test_read_the_docs_uses_supported_python_and_strict_sphinx() -> None:
    config = (ROOT / ".readthedocs.yml").read_text(encoding="utf-8")

    assert 'python: "3.12"' in config
    assert "fail_on_warning: true" in config
    assert "requirements: requirements-docs.txt" in config
