from pathlib import Path

import pymdtools.filetools as filetools


def test_get_this_filename_unfrozen():
    path = filetools._get_this_filename()
    p = Path(path)

    assert p.exists()
    assert p.is_file()

def test_get_this_filename_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "app.exe"
    fake_exe.write_text("binary", encoding="utf-8")

    monkeypatch.setattr(filetools.sys, "frozen", True, raising=False)
    monkeypatch.setattr(filetools.sys, "executable", str(fake_exe))

    path = filetools._get_this_filename()
    assert Path(path) == fake_exe.resolve()