from __future__ import annotations

from pathlib import Path
import sys
import types

import pytest

import pymdtools.common as common


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