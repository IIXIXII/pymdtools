"""Repeatable parser benchmark with an optional generous CI time budget."""

import argparse
import statistics
import time

from pymdtools.mdcommon import markdown_code_ranges, update_links_in_md_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=float, default=None)
    args = parser.parse_args()
    for blocks in (250, 500, 1000, 2000):
        source = ("```\ncode\n```\n" + "paragraph words " * 5 + "\n\n") * blocks
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            assert len(markdown_code_ranges(source)) == blocks
            timings.append(time.perf_counter() - start)
        elapsed = statistics.median(timings)
        print(f"{blocks:4d} blocks  {len(source):6d} bytes  {elapsed:.3f}s median")
        if args.max_seconds is not None and elapsed > args.max_seconds:
            raise SystemExit(f"Parser exceeded {args.max_seconds}s budget")
    for count in (50, 100, 200, 1000):
        source = "\n\n".join(f"[doc{i}](file{i}.md)" for i in range(count))
        changes = [{"name": f"doc{i}", "url": f"next{i}.md"} for i in range(count)]
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            updated = update_links_in_md_text(source, changes)
            timings.append(time.perf_counter() - start)
            assert updated.count("](next") == count
        elapsed = statistics.median(timings)
        print(f"{count:4d} link updates  {elapsed:.3f}s median")
        if args.max_seconds is not None and elapsed > args.max_seconds:
            raise SystemExit(f"Link updates exceeded {args.max_seconds}s budget")


if __name__ == "__main__":
    main()
