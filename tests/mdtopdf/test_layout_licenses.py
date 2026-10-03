from __future__ import annotations

from pathlib import Path

import pytest

from pymdtools.mdtopdf import convert_md_to_html

LAYOUT_ROOT = Path(__file__).resolve().parents[2] / "src" / "pymdtools" / "layouts"


@pytest.mark.parametrize("layout", sorted(p.parent.name for p in LAYOUT_ROOT.glob("*/page.html")))
def test_html_exports_the_complete_license_notice_for_each_layout(
    tmp_path: Path, layout: str
) -> None:
    source = tmp_path / "document.md"
    source.write_text("# Document\n\nText.\n", encoding="utf-8")

    html = Path(convert_md_to_html(source, layout=layout, path_dest=tmp_path))

    assert html.is_file()
    notice = tmp_path / "_pymdtools_assets" / layout / "LICENSES.txt"
    original = LAYOUT_ROOT / layout / "assets" / "LICENSES.txt"
    assert notice.read_bytes() == original.read_bytes()
    assert "Redistribution and use" in notice.read_text(encoding="utf-8")
    if layout != "roryg-ghostwriter":
        assert "Ivan Sagalaev" in notice.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "legacy,replacement",
    [
        ("jasonm23-dark", "thomasf-solarizedcssdark"),
        ("jasonm23-foghorn", "github"),
        ("jasonm23-markdown", "github"),
        ("markedapp-byword", "github"),
    ],
)
def test_legacy_layout_names_export_only_replacement_resources(
    tmp_path: Path, legacy: str, replacement: str
) -> None:
    source = tmp_path / "document.md"
    source.write_text("# Compatibility\n", encoding="utf-8")
    output = convert_md_to_html(source, layout=legacy, path_dest=tmp_path)
    assert f"_pymdtools_assets/{replacement}/" in Path(output).read_text(encoding="utf-8")
    assets = tmp_path / "_pymdtools_assets"
    assert not (assets / legacy).exists()
    assert not (LAYOUT_ROOT / legacy).exists()
    assert (assets / replacement / "LICENSES.txt").read_bytes() == (
        LAYOUT_ROOT / replacement / "assets" / "LICENSES.txt"
    ).read_bytes()
