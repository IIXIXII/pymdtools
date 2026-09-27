from pathlib import Path

import pytest

from pymdtools import instruction
from pymdtools.mdfile import MarkdownContent
from pymdtools.options import IncludeOptions


def write_ref(path, name="section"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<!-- begin-ref({name}) -->{name}<!-- end-ref -->", encoding="utf-8")


def test_no_directive_never_scans_the_document_tree(tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("reference discovery was not needed")

    monkeypatch.setattr(instruction, "get_refs_around_md_file", unexpected)
    doc = MarkdownContent(tmp_path / "doc.md", content="# Title\n", search_folders=None)
    assert doc.process_tags() == "# Title\n"


def test_discovery_depth_applies_to_document_and_additional_roots(tmp_path):
    local, extra = tmp_path / "local", tmp_path / "extra"
    for folder in (local, extra):
        write_ref(folder / "nested" / "ref.md", folder.name)
    source = "<!-- begin-include(local) -->old<!-- end-include -->\n<!-- begin-include(extra) -->old<!-- end-include -->"
    options = IncludeOptions(search_folders=(extra,), refs_depth=1)
    doc = MarkdownContent(local / "doc.md", content=source, include_options=options)
    assert "old" not in doc.process_tags()
    shallow = MarkdownContent(local / "doc.md", content=source, search_folders=[extra])
    with pytest.raises(KeyError):
        shallow.process_tags()


def test_exclusions_prune_reference_and_variable_searches(tmp_path):
    write_ref(tmp_path / "visible.md", "visible")
    write_ref(tmp_path / ".venv" / "hidden.md", "hidden")
    write_ref(tmp_path / "docs" / "generated" / "hidden.md", "generated")
    (tmp_path / ".venv" / "vars.md").write_text('<!-- var(secret)="hidden" -->', encoding="utf-8")
    assert instruction.get_refs_from_md_directory(
        tmp_path, exclude_dirs=(".venv", "docs/generated")
    ) == {"visible": "visible"}
    assert instruction.get_vars_from_md_directory(tmp_path) == {}
    assert "hidden" in instruction.get_refs_from_md_directory(tmp_path, exclude_dirs=())
    assert instruction.get_vars_from_md_directory(tmp_path, exclude_dirs=()) == {"secret": "hidden"}


def test_discovery_skips_symlinked_entries(tmp_path, monkeypatch):
    write_ref(tmp_path / "ignored.md")
    real = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path.name == "ignored.md" or real(path))
    assert instruction.get_refs_from_md_directory(tmp_path) == {}


@pytest.mark.parametrize(
    "options", [{"refs_depth": -2}, {"nb_up_path": -1}, {"render_mode": "typo"}]
)
def test_invalid_include_options_fail_early(options):
    with pytest.raises(ValueError):
        IncludeOptions(**options)


def test_unknown_legacy_options_fail_early():
    with pytest.raises(TypeError, match="refs_dept"):
        MarkdownContent(content="", refs_dept=1)


def test_invalid_directory_depth_fails_early(tmp_path):
    with pytest.raises(ValueError, match="depth"):
        instruction.get_refs_from_md_directory(tmp_path, depth=-2)


def test_in_memory_document_resolves_from_explicit_roots(tmp_path):
    write_ref(tmp_path / "ref.md")
    content = "<!-- begin-include(section) -->old<!-- end-include -->"
    doc = MarkdownContent(
        content=content, include_options=IncludeOptions(search_folders=(tmp_path,))
    )
    assert "old" not in doc.process_tags()
    with pytest.raises(KeyError):
        MarkdownContent(content=content, search_folders=None).process_tags()


def test_discovery_terminates_on_a_directory_alias_cycle(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    (root / "alias").mkdir()
    write_ref(root / "ref.md")
    resolve = Path.resolve

    def aliased(path, *args, **kwargs):
        return root if path.name == "alias" else resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", aliased)
    assert instruction.get_refs_from_md_directory(root) == {"section": "section"}
