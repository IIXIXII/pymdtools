"""Load a project template and edit a text file with FileContent backups."""

from _support import DATA, output_directory

from pymdtools.filetools import FileContent, get_template_file, get_template_files_in_folder


def main() -> None:
    output = output_directory(__file__, __doc__)
    names = get_template_files_in_folder("messages", start_folder=DATA)
    template = get_template_file(names[0], start_folder=DATA)
    path = output / "welcome.md"
    path.write_text(template, encoding="utf-8")
    document = FileContent(path, encoding="utf-8", backup=True)
    assert not document.save_needed
    document.content = (document.content or "") + "\nYour local copy is ready.\n"
    document.write()
    assert any(p.read_text(encoding="utf-8") == template for p in output.glob("*.bak"))
    print("Available templates:", names)
    print("Saved with a backup:", document.full_filename)


if __name__ == "__main__":
    main()
