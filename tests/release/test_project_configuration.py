from __future__ import annotations

import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]


def _assert_action_pinned(text: str, action: str) -> None:
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

    _assert_action_pinned(workflow, "actions/checkout")
    _assert_action_pinned(workflow, "actions/setup-python")
    _assert_action_pinned(workflow, "actions/upload-artifact")
    assert 'python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]' in workflow
    assert "scripts/check_distribution.py" in workflow
    assert "scripts/release.py build" in workflow


def test_publish_keeps_build_code_away_from_oidc_credentials() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    build_section, publish_section = workflow.split("\n  publish:\n", maxsplit=1)
    publish_section, github_release_section = publish_section.split(
        "\n  github-release:\n", maxsplit=1
    )

    _assert_action_pinned(workflow, "actions/checkout")
    _assert_action_pinned(workflow, "actions/setup-python")
    _assert_action_pinned(workflow, "actions/upload-artifact")
    _assert_action_pinned(workflow, "actions/download-artifact")
    _assert_action_pinned(workflow, "pypa/gh-action-pypi-publish")
    assert "id-token: write" not in build_section
    assert "actions/upload-artifact@" in build_section
    assert "RELEASE_TAG: ${{ github.ref_name }}" in build_section
    assert 'verify-tag "$RELEASE_TAG"' in build_section
    assert "ref: ${{ github.sha }}" in build_section
    assert "cache: pip" not in build_section
    assert "enable-cache: true" not in build_section
    assert "enable-cache: false" in build_section
    assert "id-token: write" in publish_section
    assert "actions/checkout" not in publish_section
    assert "python -m build" not in publish_section
    assert "actions/download-artifact@" in publish_section
    assert "pypa/gh-action-pypi-publish@" in publish_section
    assert "artifact-ids: ${{ needs.build.outputs.artifact-id }}" in publish_section
    assert "digest-mismatch: error" in publish_section
    assert "attestations: true" in publish_section
    assert "contents: write" not in build_section + publish_section
    assert "contents: write" in github_release_section
    assert "id-token: write" not in github_release_section
    assert "actions/checkout" not in github_release_section


def test_tag_push_publishes_before_creating_github_release() -> None:
    workflow = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    trigger = workflow.split("\npermissions:", maxsplit=1)[0]
    assert 'tags: ["v*"]' in trigger
    assert "  push:" in trigger
    assert "  release:" not in trigger  # Avoid publishing the same version twice.
    build_section, following_jobs = workflow.split("\n  publish:\n", maxsplit=1)
    assert 'scripts/release.py notes --output "$RUNNER_TEMP/release-notes.md"' in build_section
    github_release = following_jobs.split("\n  github-release:\n", maxsplit=1)[1]
    assert "needs: [build, publish]" in github_release
    assert "artifact-ids: ${{ needs.build.outputs.artifact-id }}" in github_release
    assert "artifact-ids: ${{ needs.build.outputs.notes-artifact-id }}" in github_release
    assert github_release.count("digest-mismatch: error") == 2
    assert 'gh release create "$RELEASE_TAG" dist/*.whl dist/*.tar.gz' in github_release
    assert "--verify-tag" in github_release
    assert "--notes-file notes/release-notes.md" in github_release
    assert "--clobber" not in github_release


def test_dependabot_tracks_python_and_action_dependencies() -> None:
    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert "package-ecosystem: uv" in dependabot
    assert "package-ecosystem: pip" not in dependabot
    assert "package-ecosystem: github-actions" in dependabot
    assert dependabot.count("interval: weekly") == 2


def test_workflows_pin_external_actions_and_do_not_persist_git_credentials() -> None:
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        workflow = path.read_text(encoding="utf-8")
        assert "pull_request_target:" not in workflow, path
        for action in re.findall(r"uses: ([^\s]+)", workflow):
            if action.startswith(("./", "$/")):
                assert (ROOT / action[2:]).is_file(), action
            else:
                assert re.fullmatch(r"[^@]+@[a-f0-9]{40}", action), action
        assert workflow.count("actions/checkout@") == workflow.count(
            "persist-credentials: false"
        ), path


def test_ci_gate_rejects_failed_cancelled_or_skipped_validation_jobs() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    gate = workflow.split("\n  ci-success:\n", maxsplit=1)[1]
    assert "if: ${{ always() }}" in gate
    assert "needs: [workflow-safety, tests, quality, pdf]" in gate
    assert 'all(.[]; .result == "success")' in gate
    assert "merge_group:" in workflow
    assert "--no-cov" not in workflow


def test_read_the_docs_uses_supported_python_and_strict_sphinx() -> None:
    config = (ROOT / ".readthedocs.yml").read_text(encoding="utf-8")

    assert 'python: "3.12"' in config
    assert "fail_on_warning: true" in config
    assert "requirements: requirements-docs.txt" in config
