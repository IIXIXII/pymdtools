from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_release_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pymdtools_release_script",
        ROOT / "scripts" / "release.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = _load_release_module()


@pytest.fixture
def release_tree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "VERSION_PY", tmp_path / "version.py")
    monkeypatch.setattr(release, "VERSION_BAT", tmp_path / "version.bat")
    monkeypatch.setattr(release, "CHANGELOG", tmp_path / "CHANGELOG.md")
    release.write_version((1, 2, 3))
    release.CHANGELOG.write_text(
        "# Changelog\n\n## Unreleased\n\n- Preserve café links.\n\n"
        "### Migration\n\nKeep these instructions.\n\n"
        "## 1.2.3 - 2026-01-01\n\n- Previous release.\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.parametrize(
    "part,expected", [("patch", "1.2.4"), ("minor", "1.3.0"), ("major", "2.0.0")]
)
def test_prepare_release_preserves_notes_and_history(
    release_tree: Path, monkeypatch: pytest.MonkeyPatch, part: str, expected: str
) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    assert release.prepare_release(part) == expected
    assert release.verify_version_files() == expected
    changelog = release.CHANGELOG.read_text(encoding="utf-8")
    assert f"## Unreleased\n\n## {expected} - {release.date.today().isoformat()}" in changelog
    assert changelog.endswith("## 1.2.3 - 2026-01-01\n\n- Previous release.\n")
    assert (
        release.release_notes()
        == "- Preserve café links.\n\n### Migration\n\nKeep these instructions.\n"
    )
    assert b"\r\nSET VERSION=" in (release_tree / "version.bat").read_bytes()


@pytest.mark.parametrize(
    "changelog,message",
    [
        ("# Changelog\n", "exactly one Unreleased"),
        ("## Unreleased\n\n## 1.2.3 - 2026-01-01\n- Old\n", "Unreleased section is empty"),
        ("## Unreleased\n- A\n## Unreleased\n- B\n", "exactly one Unreleased"),
        ("## Unreleased\n- A\n## 1.2.4 - 2026-01-01\n- B\n", "already contains version"),
    ],
)
def test_prepare_rejects_invalid_changelog_before_editing_versions(
    release_tree: Path, monkeypatch: pytest.MonkeyPatch, changelog: str, message: str
) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    release.CHANGELOG.write_text(changelog, encoding="utf-8")
    before = {path: path.read_bytes() for path in release_tree.iterdir()}
    with pytest.raises(release.ReleaseError, match=message):
        release.prepare_release("patch")
    assert {path: path.read_bytes() for path in release_tree.iterdir()} == before


def test_prepare_rejects_mismatched_version_files(
    release_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    release.VERSION_BAT.write_text("SET VERSION=1.2.9\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in release_tree.iterdir()}
    with pytest.raises(release.ReleaseError, match="version mismatch"):
        release.prepare_release("patch")
    assert {path: path.read_bytes() for path in release_tree.iterdir()} == before


@pytest.mark.parametrize(
    "section,message",
    [
        ("## Unreleased\n- Pending\n", "exactly one 1.2.3"),
        ("## 1.2.3\n- Missing date\n", "exactly one 1.2.3"),
        ("## 1.2.3 - 2026-01-01\n", "section is empty"),
        ("## 1.2.3 - 2026-02-30\n- Invalid date\n", "invalid date"),
        ("## 1.2.3 - 2026-01-01\n- A\n## 1.2.3 - 2026-01-02\n- B\n", "exactly one 1.2.3"),
    ],
)
def test_notes_rejects_invalid_sections(release_tree: Path, section: str, message: str) -> None:
    release.CHANGELOG.write_text(section, encoding="utf-8")
    with pytest.raises(release.ReleaseError, match=message):
        release.release_notes()


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_notes_preserves_fenced_headings_and_unicode(
    release_tree: Path, fence: str, capsys: pytest.CaptureFixture[str]
) -> None:
    notes = f"- Café 🚀\n\n{fence}markdown\n## 1.2.3 - 2026-01-01\n## Unreleased\n{fence}\n"
    release.CHANGELOG.write_text(
        f"## Unreleased\n\n## 1.2.3 - 2026-01-01\n\n{notes}\n## 1.2.2 - 2025-01-01\n- Old\n",
        encoding="utf-8",
    )
    output = release_tree / "notes.md"
    assert release.main(["notes", "--output", str(output)]) == 0
    assert output.read_bytes() == notes.encode("utf-8")
    assert release.main(["notes"]) == 0
    assert capsys.readouterr().out == notes


def test_local_prepare_commit_tag_flow(release_tree: Path) -> None:
    """Exercise the documented sequence in a disposable, entirely local Git repo."""
    release.run_git("init")
    release.run_git("config", "user.email", "release-test@example.invalid")
    release.run_git("config", "user.name", "Release test")
    release.run_git("add", "version.py", "version.bat", "CHANGELOG.md")
    release.run_git("commit", "-m", "Initial files")
    assert release.main(["prepare", "patch"]) == 0
    # Preparing or tagging again while the release edits are uncommitted must fail.
    assert release.main(["prepare", "patch"]) == 1
    assert release.main(["tag"]) == 1
    release.run_git("add", "version.py", "version.bat", "CHANGELOG.md")
    release.run_git("commit", "-m", "Release 1.2.4")
    assert release.main(["tag"]) == 0
    assert release.verify_tag("v1.2.4") == "v1.2.4"
    assert "Keep these instructions." in release.release_notes()
    assert release.run_git("status", "--porcelain").stdout == ""
    assert release.run_git("remote").stdout == ""


def _completed(*args: str, stdout: str = "", returncode: int = 0) -> Any:
    return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr="")


def test_parse_python_version() -> None:
    assert release.parse_python_version("__version_info__ = (1, 2, 3)\n") == (1, 2, 3)

    with pytest.raises(release.ReleaseError, match="cannot parse"):
        release.parse_python_version("__version__ = 'bad'\n")


def test_parse_batch_version() -> None:
    assert release.parse_batch_version("SET VERSION=1.2.3\n") == (1, 2, 3)

    with pytest.raises(release.ReleaseError, match="cannot parse"):
        release.parse_batch_version("SET VERSION=bad\n")


def test_write_and_verify_version_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    version_py = tmp_path / "version.py"
    version_bat = tmp_path / "version.bat"
    version_py.write_text("__version_info__ = (1, 0, 0)\n", encoding="utf-8")
    version_bat.write_text("SET VERSION=1.0.0\n", encoding="utf-8")
    monkeypatch.setattr(release, "VERSION_PY", version_py)
    monkeypatch.setattr(release, "VERSION_BAT", version_bat)

    release.write_version((2, 3, 4))

    assert release.current_version() == (2, 3, 4)
    assert release.verify_version_files() == "2.3.4"
    assert "SET VERSION=2.3.4" in version_bat.read_text(encoding="utf-8")


def test_verify_version_files_rejects_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    version_py = tmp_path / "version.py"
    version_bat = tmp_path / "version.bat"
    version_py.write_text("__version_info__ = (1, 2, 3)\n", encoding="utf-8")
    version_bat.write_text("SET VERSION=1.2.4\n", encoding="utf-8")
    monkeypatch.setattr(release, "VERSION_PY", version_py)
    monkeypatch.setattr(release, "VERSION_BAT", version_bat)

    with pytest.raises(release.ReleaseError, match="version mismatch"):
        release.verify_version_files()


def test_create_tag_is_local_and_annotated(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "verify_version_files", lambda: "1.2.3")
    monkeypatch.setattr(release, "release_notes", lambda: "- Release notes.\n")

    def fake_git(*args: str, check: bool = True) -> Any:
        del check
        calls.append(args)
        if args[0] == "rev-parse":
            return _completed(*args, returncode=1)
        return _completed(*args)

    monkeypatch.setattr(release, "run_git", fake_git)

    assert release.create_tag() == "v1.2.3"
    assert ("tag", "--annotate", "v1.2.3", "--message", "Release 1.2.3") in calls
    assert all("push" not in call for call in calls)


def test_create_tag_rejects_an_existing_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "verify_version_files", lambda: "1.2.3")
    monkeypatch.setattr(release, "release_notes", lambda: "- Release notes.\n")
    monkeypatch.setattr(
        release,
        "run_git",
        lambda *args, **kwargs: _completed(*args),
    )

    with pytest.raises(release.ReleaseError, match="already exists"):
        release.create_tag()


def test_create_tag_rejects_missing_notes_before_mutating_git(
    release_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    release.CHANGELOG.write_text("## Unreleased\n- Pending\n", encoding="utf-8")

    def unexpected_git(*args: str, **kwargs: Any) -> Any:
        pytest.fail("Git must not be changed before validating release notes")

    monkeypatch.setattr(release, "run_git", unexpected_git)
    with pytest.raises(release.ReleaseError, match="exactly one 1.2.3"):
        release.create_tag()


def test_verify_tag_requires_matching_tag_at_head(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "verify_version_files", lambda: "1.2.3")

    def fake_git(*args: str, **kwargs: Any) -> Any:
        del kwargs
        if args[:2] == ("cat-file", "-t"):
            return _completed(*args, stdout="tag\n")
        return _completed(*args, stdout="v1.2.3\n")

    monkeypatch.setattr(release, "run_git", fake_git)

    assert release.verify_tag("v1.2.3") == "v1.2.3"
    with pytest.raises(release.ReleaseError, match="tag/version mismatch"):
        release.verify_tag("v1.2.4")


@pytest.mark.parametrize(
    ("kind", "returncode", "message"),
    [
        ("", 1, "does not exist"),
        ("commit\n", 0, "must be annotated"),
    ],
)
def test_verify_tag_rejects_missing_or_lightweight_tags(
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    returncode: int,
    message: str,
) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "verify_version_files", lambda: "1.2.3")
    monkeypatch.setattr(
        release,
        "run_git",
        lambda *args, **kwargs: _completed(*args, stdout=kind, returncode=returncode),
    )

    with pytest.raises(release.ReleaseError, match=message):
        release.verify_tag("v1.2.3")


def test_verify_tag_rejects_tag_not_at_head(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "verify_version_files", lambda: "1.2.3")

    def fake_git(*args: str, **kwargs: Any) -> Any:
        del kwargs
        if args[:2] == ("cat-file", "-t"):
            return _completed(*args, stdout="tag\n")
        return _completed(*args, stdout="v9.9.9\n")

    monkeypatch.setattr(release, "run_git", fake_git)

    with pytest.raises(release.ReleaseError, match="does not point at HEAD"):
        release.verify_tag("v1.2.3")


def test_require_clean_worktree_rejects_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        release,
        "run_git",
        lambda *args, **kwargs: _completed(*args, stdout=" M setup.py\n"),
    )

    with pytest.raises(release.ReleaseError, match="not clean"):
        release.require_clean_worktree()


@pytest.mark.parametrize(
    ("part", "expected"),
    [
        ("major", (2, 0, 0)),
        ("minor", (1, 3, 0)),
        ("patch", (1, 2, 4)),
    ],
)
def test_bump_version(
    monkeypatch: pytest.MonkeyPatch,
    part: str,
    expected: tuple[int, int, int],
) -> None:
    written: list[tuple[int, int, int]] = []
    monkeypatch.setattr(release, "require_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "current_version", lambda: (1, 2, 3))
    monkeypatch.setattr(release, "write_version", written.append)

    assert release.bump_version(part) == ".".join(map(str, expected))
    assert written == [expected]


def test_bump_version_rejects_unknown_component(monkeypatch: pytest.MonkeyPatch) -> None:
    clean_checked = False

    def check_clean() -> None:
        nonlocal clean_checked
        clean_checked = True

    monkeypatch.setattr(release, "require_clean_worktree", check_clean)

    with pytest.raises(release.ReleaseError, match="unknown version component"):
        release.bump_version("prerelease")
    assert not clean_checked


def test_reset_dist_dir_rejects_paths_outside_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    unsafe = tmp_path / "outside" / "dist"
    unsafe.mkdir(parents=True)
    monkeypatch.setattr(release, "ROOT", tmp_path / "repository")
    monkeypatch.setattr(release, "DIST_DIR", unsafe)

    with pytest.raises(release.ReleaseError, match="unsafe distribution path"):
        release._reset_dist_dir()
    assert unsafe.is_dir()


def test_validated_artifacts_requires_exact_pair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "example-1.0-py3-none-any.whl"
    sdist = dist / "example-1.0.tar.gz"
    wheel.touch()
    sdist.touch()
    monkeypatch.setattr(release, "DIST_DIR", dist)
    monkeypatch.setattr(release, "DISTRIBUTION_NAME", "example")
    monkeypatch.setattr(release, "version_string", lambda *args: "1.0")

    assert release._validated_artifacts() == sorted([wheel, sdist])

    wrong_sdist = sdist.with_name("example-2.0.tar.gz")
    sdist.rename(wrong_sdist)
    with pytest.raises(release.ReleaseError, match="does not match version"):
        release._validated_artifacts()
    wrong_sdist.rename(sdist)

    (dist / "unexpected.txt").touch()
    with pytest.raises(release.ReleaseError, match="exactly one wheel"):
        release._validated_artifacts()


def test_build_distributions_uses_utf8_and_strict_twine(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dist = tmp_path / "dist"
    commands: list[list[str]] = []
    clean_checks: list[bool] = []
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "DIST_DIR", dist)
    monkeypatch.setattr(release, "DISTRIBUTION_NAME", "example")
    monkeypatch.setattr(release, "version_string", lambda *args: "1.0")
    monkeypatch.setattr(release, "require_clean_worktree", lambda: clean_checks.append(True))

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        commands.append(command)
        assert kwargs["cwd"] == tmp_path
        assert kwargs["check"] is True
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        assert kwargs["env"]["PYTHONIOENCODING"] == "utf-8"
        if command[2] == "build":
            dist.mkdir()
            (dist / "example-1.0-py3-none-any.whl").touch()
            (dist / "example-1.0.tar.gz").touch()
        return _completed(*command)

    monkeypatch.setattr(release.subprocess, "run", fake_run)

    artifacts = release.build_distributions()

    assert clean_checks == [True]
    assert len(artifacts) == 2
    assert commands[0][1:3] == ["-m", "build"]
    assert commands[1][1:5] == ["-m", "twine", "check", "--strict"]


def test_audit_tags_reads_both_source_layouts(monkeypatch):
    calls = []

    def fake_git(*args, **kwargs):
        calls.append(args)
        if args[0] == "tag":
            return _completed(*args, stdout="v1.0.0\nv2.0.0\n")
        if args[1] == "v1.0.0:src/pymdtools/version.py":
            return _completed(*args, returncode=1)
        version = "1, 0, 0" if args[1].startswith("v1.") else "2, 0, 0"
        return _completed(*args, stdout=f"__version_info__ = ({version})\n")

    monkeypatch.setattr(release, "run_git", fake_git)
    assert release.audit_tags() == []
    assert ("show", "v1.0.0:pymdtools/version.py") in calls
    assert ("show", "v2.0.0:pymdtools/version.py") not in calls
