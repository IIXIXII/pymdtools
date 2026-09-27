"""Shared CLI paths only; each example keeps its pymdtools calls in its own file."""

from __future__ import annotations

import argparse
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent
DATA = EXAMPLES / "data"


def output_directory(script: str, description: str | None) -> Path:
    """Create a dedicated output directory, independent of the working directory."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        type=Path,
        default=EXAMPLES / "output" / Path(script).stem,
        help="Dedicated output directory; example files in it may be replaced",
    )
    output = parser.parse_args().output.resolve()
    if output == EXAMPLES or output.is_relative_to(DATA):
        parser.error("Choose an output directory outside the example sources and data.")
    output.mkdir(parents=True, exist_ok=True)
    return output
