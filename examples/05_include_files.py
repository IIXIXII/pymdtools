"""Insert a local fragment as Markdown or as a boxed comment; preserve code examples."""

from _support import DATA, output_directory

from pymdtools.instruction import include_files_to_md_text


def main() -> None:
    output = output_directory(__file__, __doc__)
    directive = "<!-- include-file(introduction.md) -->"
    source = f"# Handbook\n\n{directive}\n\n```markdown\n{directive}\n```\n"
    for mode in ("raw", "box"):
        result = include_files_to_md_text(
            source,
            search_folders=[DATA / "snippets"],
            relative_paths=(".",),
            include_cwd=False,
            render_mode=mode,
        )
        (output / f"{mode}.md").write_text(result, encoding="utf-8")
        assert f"```markdown\n{directive}\n```" in result
    print("raw.md contains visible Markdown; box.md keeps the fragment in a comment:", output)


if __name__ == "__main__":
    main()
