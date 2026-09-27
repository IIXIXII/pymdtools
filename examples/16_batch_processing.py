"""Normalize a copied document tree and collect per-file errors without stopping."""

import json
from dataclasses import asdict

from _support import DATA, output_directory

from pymdtools.common import apply_to_files
from pymdtools.normalize import md_file_beautifier


def main() -> None:
    output = output_directory(__file__, __doc__)
    documents = output / "documents"
    documents.mkdir(exist_ok=True)
    (documents / "valid.md").write_text(
        (DATA / "document.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (documents / "empty.md").write_text("", encoding="utf-8")  # Intentional recoverable error.
    generated = documents / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "ignored.md").write_text("Not processed.\n", encoding="utf-8")
    results, summary, errors = apply_to_files(
        documents,
        lambda path: md_file_beautifier(path, read_encoding="utf-8"),
        expected_ext=".md",
        exclude_globs=("generated/*",),
        on_error="collect",
    )
    assert summary.succeeded == 1 and summary.failed == 1
    report = {
        "summary": asdict(summary),
        "written": results,
        "errors": [{"file": str(path), "error": str(error)} for path, error in errors],
    }
    (output / "batch-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("One empty-file error is expected in this example:", summary)


if __name__ == "__main__":
    main()
