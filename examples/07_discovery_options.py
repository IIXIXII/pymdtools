"""Discover reference sections at explicit depths and exclude generated folders."""

import shutil

from _support import DATA, output_directory

from pymdtools.instruction import get_refs_from_md_directory
from pymdtools.mdfile import MarkdownContent
from pymdtools.options import IncludeOptions


def main() -> None:
    output = output_directory(__file__, __doc__)
    library = output / "library"
    shutil.copytree(DATA / "references", library, dirs_exist_ok=True)
    generated = library / "build"
    generated.mkdir(exist_ok=True)
    (generated / "ignored.md").write_text(
        "<!-- begin-ref(generated) -->Do not import this.<!-- end-ref -->", encoding="utf-8"
    )
    shallow = get_refs_from_md_directory(library, depth=0)
    recursive = get_refs_from_md_directory(library, depth=-1)
    assert set(shallow) == {"support"}
    assert set(recursive) == {"support", "installation"}
    document = MarkdownContent(
        content="# Handbook\n\n<!-- begin-include(installation) -->pending<!-- end-include -->\n",
        include_options=IncludeOptions(search_folders=(library,), refs_depth=1),
        backup=False,
    )
    document.process_tags()
    document.write(output / "handbook.md")
    print("Root only:", sorted(shallow))
    print("Recursive, with default exclusions:", sorted(recursive))
    print("Saved:", document.full_filename)


if __name__ == "__main__":
    main()
