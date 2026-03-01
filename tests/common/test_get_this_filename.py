from __future__ import annotations

from pathlib import Path
import sys
import types

import pytest

import pymdtools.common.fs as common


def test_get_this_filename_frozen(monkeypatch, tmp_path: Path):
    fake_exe = tmp_path / "app.exe"
    fake_exe.write_text("x", encoding="utf-8")

    monkeypatch.setattr(sys, "executable", str(fake_exe))
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    out = common.get_this_filename()
    assert Path(out).name == "app.exe"


def test_get_this_filename_unfrozen_uses___file__(monkeypatch, tmp_path: Path):
    fake_mod = tmp_path / "instruction.py"
    fake_mod.write_text("#", encoding="utf-8")

    # patch module globals
    monkeypatch.setattr(common, "__file__", str(fake_mod), raising=False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    out = common.get_this_filename()
    assert Path(out).resolve() == fake_mod.resolve()


def test_get_this_filename_fallback_to_argv0(monkeypatch, tmp_path: Path):
    # simulate missing __file__
    if hasattr(common, "__file__"):
        monkeypatch.delattr(common, "__file__", raising=False)

    fake_script = tmp_path / "run.py"
    fake_script.write_text("#", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [str(fake_script)])
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    out = common.get_this_filename()
    assert Path(out).resolve() == fake_script.resolve()

def test_get_this_filename_unfrozen():
    path = common.get_this_filename()
    p = Path(path)

    assert p.exists()
    assert p.is_file()

def test_get_this_filename_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "app.exe"
    fake_exe.write_text("binary", encoding="utf-8")

    monkeypatch.setattr(common.sys, "frozen", True, raising=False)
    monkeypatch.setattr(common.sys, "executable", str(fake_exe))

    path = common.get_this_filename()
    assert Path(path) == fake_exe.resolve()

def test_get_this_filename_default_returns_module_file() -> None:
    # In normal imports, __file__ exists: function should return resolved module path.
    got = common.get_this_filename()
    assert isinstance(got, Path)
    assert Path(got) == Path(common.__file__).resolve()


def test_get_this_filename_frozen_uses_sys_executable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_exe = tmp_path / "app.exe"
    fake_exe.write_text("x", encoding="utf-8")

    monkeypatch.setattr(common.sys, "frozen", True, raising=False)
    monkeypatch.setattr(common.sys, "executable", str(fake_exe), raising=False)

    got = common.get_this_filename()
    assert Path(got) == fake_exe.resolve()


def test_get_this_filename_without___file___uses_argv0(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Simulate an interactive context: no __file__
    monkeypatch.setitem(common.__dict__, "__file__", None)

    # Provide argv0 as a relative path; resolution should be anchored to cwd.
    monkeypatch.chdir(tmp_path)
    rel = Path("bin") / "script.py"
    monkeypatch.setattr(common.sys, "argv", [str(rel)], raising=False)

    got = common.get_this_filename()
    assert Path(got) == (tmp_path / rel).resolve()


def test_get_this_filename_without___file___and_empty_argv_falls_back_to_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setitem(common.__dict__, "__file__", None)
    monkeypatch.setattr(common.sys, "argv", [], raising=False)
    monkeypatch.setattr(common.sys, "frozen", False, raising=False)

    monkeypatch.chdir(tmp_path)

    got = common.get_this_filename()
    assert Path(got) == tmp_path.resolve()


def test_get_this_filename_frozen_takes_precedence_over___file__(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_exe = tmp_path / "app.exe"
    fake_exe.write_text("x", encoding="utf-8")

    # Even if __file__ is set, frozen branch must win.
    monkeypatch.setitem(common.__dict__, "__file__", str(tmp_path / "ignored.py"))
    monkeypatch.setattr(common.sys, "frozen", True, raising=False)
    monkeypatch.setattr(common.sys, "executable", str(fake_exe), raising=False)

    got = common.get_this_filename()
    assert Path(got) == fake_exe.resolve()