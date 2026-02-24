import importlib


def test_lazy_import_and_cache():
    m = importlib.import_module("pymdtools")

    # Ensure public API names are declared
    for name in (
        "convert_for_stdout",
        "markdown_file_beautifier",
        "convert_md_to_pdf",
        "search_include_refs_to_md_file",
    ):
        assert name in getattr(m, "__all__")

    # Attribute should not be present in module dict before access
    assert "convert_for_stdout" not in m.__dict__

    # Accessing the attribute triggers lazy import and caches it
    attr = getattr(m, "convert_for_stdout")
    assert callable(attr)
    assert "convert_for_stdout" in m.__dict__


def test_dir_shows_public_only():
    m = importlib.import_module("pymdtools")
    names = set(dir(m))

    # Public names from __all__ must be present
    for name in m.__all__:
        assert name in names

    # Ensure typing-related helpers are not exposed by __dir__
    assert "Any" not in names
    assert "typing" not in names
