from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import pymdtools


def test_package_metadata_and_public_directory_are_exposed() -> None:
    public_names = dir(pymdtools)

    assert pymdtools.__version__
    assert pymdtools.__license__ == "MIT"
    assert set(pymdtools.__all__) <= set(public_names)
    assert "__name__" in public_names


def test_lazy_public_symbol_is_resolved_and_cached(monkeypatch: Any) -> None:
    monkeypatch.delitem(vars(pymdtools), "convert_for_stdout", raising=False)

    resolved = pymdtools.__getattr__("convert_for_stdout")

    assert resolved("hello") == "hello"
    assert vars(pymdtools)["convert_for_stdout"] is resolved


def test_unknown_package_attribute_is_rejected() -> None:
    with pytest.raises(AttributeError, match="has no attribute"):
        pymdtools.__getattr__("not_public")


def test_lazy_import_failure_has_actionable_context(monkeypatch: Any) -> None:
    monkeypatch.setitem(pymdtools._LAZY, "unavailable", (".unavailable", "value"))

    def missing_module(*args: Any, **kwargs: Any) -> Any:
        raise ModuleNotFoundError("optional dependency is absent")

    monkeypatch.setattr(pymdtools, "import_module", missing_module)

    with pytest.raises(ImportError, match="installation is incomplete"):
        pymdtools.__getattr__("unavailable")


def test_lazy_missing_attribute_has_actionable_context(monkeypatch: Any) -> None:
    monkeypatch.setitem(pymdtools._LAZY, "missing_symbol", (".fake", "missing"))
    fake_module = SimpleNamespace(__name__="pymdtools.fake")
    monkeypatch.setattr(pymdtools, "import_module", lambda *args, **kwargs: fake_module)

    with pytest.raises(ImportError, match="attribute 'missing' not found"):
        pymdtools.__getattr__("missing_symbol")
