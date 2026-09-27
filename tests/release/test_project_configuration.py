from __future__ import annotations

import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]


def _assert_action_version(text: str, action: str, minimum: tuple[int, int, int]) -> None:
    del minimum
    matches = re.findall(rf"{re.escape(action)}@([^\s]+)", text)
    assert matches, action
    assert all(re.fullmatch(r"[a-f0-9]{40}", ref) for ref in matches)


def test_metadata_is_centralized_and_pdf_is_optional() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert not any("pdfkit" in req or "pypdf" in req for req in project["dependencies"])
    assert any("playwright" in req for req in project["optional-dependencies"]["pdf"])
    assert (ROOT / "requirements-dev.txt").read_text().strip() == "-e .[dev,pdf]"
    assert (ROOT / "src" / "pymdtools" / "py.typed").is_file()
    assert not (ROOT / "setup.py").exists()


def test_packaging_carries_license_inventory() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert "MIT" in project["license"]
    for pattern in project["license-files"]:
        assert list(ROOT.glob(pattern))


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
    assert "scripts/check_distribution.py" in workflow
    assert "scripts/release.py build" in workflow


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
