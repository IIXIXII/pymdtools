from pathlib import Path
import pytest

from pymdtools.common import find_file


def test_find_file_finds_in_relative_path(tmp_path):
    # structure: tmp/a/b/target.txt
    base = tmp_path / "a" / "b"
    base.mkdir(parents=True)
    target = base / "target.txt"
    target.write_text("x", encoding="utf-8")

    found = find_file(
        "target.txt",
        start_points=[base],
        relative_paths=["."],
        max_up=0,
    )
    assert Path(found) == target.resolve()


def test_find_file_walks_up_parents(tmp_path):
    # tmp/root/rel/target.txt and start at tmp/root/sub
    root = tmp_path / "root"
    (root / "rel").mkdir(parents=True)
    (root / "sub").mkdir(parents=True)

    target = root / "rel" / "target.txt"
    target.write_text("x", encoding="utf-8")

    found = find_file(
        "target.txt",
        start_points=[root / "sub"],
        relative_paths=["rel"],
        max_up=2,
    )
    assert Path(found) == target.resolve()


def test_find_file_tries_multiple_start_points(tmp_path):
    p1 = tmp_path / "p1"
    p2 = tmp_path / "p2"
    p1.mkdir()
    p2.mkdir()

    target = p2 / "target.txt"
    target.write_text("x", encoding="utf-8")

    found = find_file(
        "target.txt",
        start_points=[p1, p2],
        relative_paths=["."],
        max_up=0,
    )
    assert Path(found) == target.resolve()


def test_find_file_raises_with_details(tmp_path):
    with pytest.raises(FileNotFoundError) as exc:
        find_file("missing.txt", start_points=[tmp_path], relative_paths=["."], max_up=1)
    assert "missing.txt" in str(exc.value)


def test_find_file_invalid_max_up_raises(tmp_path):
    with pytest.raises(ValueError):
        find_file("x.txt", start_points=[tmp_path], relative_paths=["."], max_up=-1)


@pytest.mark.parametrize(
    "filename",
    [
        "../outside.txt",
        "folder/target.txt",
        "C:target.txt",
        "\\target.txt",
        "..",
    ],
)
def test_find_file_rejects_filename_paths(tmp_path: Path, filename: str) -> None:
    with pytest.raises(ValueError, match="plain filename"):
        find_file(filename, [tmp_path], ["."], max_up=0)


def test_find_file_rejects_parent_traversal_in_relative_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not contain"):
        find_file("target.txt", [tmp_path], ["../outside"], max_up=0)


def test_find_file_rejects_drive_relative_search_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be relative"):
        find_file("target.txt", [tmp_path], ["C:relative"], max_up=0)


def test_find_file_rejects_resolved_symlink_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = tmp_path / "anchor"
    search = anchor / "linked"
    search.mkdir(parents=True)
    outside = tmp_path / "outside" / "target.txt"
    outside.parent.mkdir()
    outside.write_text("outside", encoding="utf-8")
    unresolved_candidate = search / "target.txt"
    original_resolve = Path.resolve

    def fake_resolve(self: Path, *args, **kwargs) -> Path:
        if self == unresolved_candidate:
            return outside
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    with pytest.raises(ValueError, match="escapes its anchor"):
        find_file("target.txt", [anchor], ["linked"], max_up=0)
