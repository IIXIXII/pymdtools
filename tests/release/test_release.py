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
    monkeypatch.setattr(
        release,
        "run_git",
        lambda *args, **kwargs: _completed(*args),
    )

    with pytest.raises(release.ReleaseError, match="already exists"):
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
