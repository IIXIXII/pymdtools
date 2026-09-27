"""Normalize a copied Markdown file and keep a dated backup of the original."""

import shutil

from _support import DATA, output_directory

from pymdtools.normalize import md_file_beautifier


def main() -> None:
    output = output_directory(__file__, __doc__)
    target = output / "guide.md"
    shutil.copyfile(DATA / "document.md", target)
    original = target.read_bytes()
    md_file_beautifier(target, backup_option=True, read_encoding="utf-8")
    backups = sorted(output.glob("guide.md.*.bak"))
    assert any(path.read_bytes() == original for path in backups)
    print("Normalized:", target)
    print("Backups:", *backups, sep="\n")


if __name__ == "__main__":
    main()
