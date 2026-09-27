"""List or execute the examples; PDF rendering is explicitly opt-in."""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument(
        "--list", action="store_true", help="List all examples without executing them"
    )
    pdf = parser.add_mutually_exclusive_group()
    pdf.add_argument("--pdf", action="store_true", help="Also run the three optional PDF examples")
    pdf.add_argument("--only-pdf", action="store_true", help="Run only the optional PDF examples")
    args = parser.parse_args()
    scripts = sorted(ROOT.glob("[0-9][0-9]_*.py")) + [ROOT / "workflows.py"]
    if args.list:
        for script in scripts:
            description = ast.get_docstring(ast.parse(script.read_text(encoding="utf-8")))
            requirement = " [PDF extra + Chromium]" if "_pdf_" in script.stem else ""
            print(f"{script.name}{requirement}: {description}")
        return

    output = args.output.resolve()
    if output == ROOT or output.is_relative_to(ROOT / "data"):
        parser.error("Choose an output directory outside the example sources and data.")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    completed = 0
    for script in scripts:
        requires_pdf = "_pdf_" in script.stem
        if args.only_pdf and not requires_pdf:
            continue
        if requires_pdf and not (args.pdf or args.only_pdf):
            continue
        print(f"\nRunning {script.name}", flush=True)
        subprocess.run(
            [sys.executable, str(script), "--output", str(output / script.stem)],
            cwd=ROOT,
            env=env,
            check=True,
        )
        completed += 1
    print(f"\nCompleted {completed} examples. Outputs: {output}")


if __name__ == "__main__":
    main()
