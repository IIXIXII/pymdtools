"""Check exported layout notices; use --write after updating licensing inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_ROOT = ROOT / "src" / "pymdtools" / "layouts"
LICENSE_ROOT = ROOT / "THIRD_PARTY_LICENSES"
COLLECTION = "https://github.com/mixu/markdown-styles/tree/eed20d2c71e7bf456e5bfbcd27135ac662002cd3"

GLYPHICONS = "LicenseRef-Glyphicons-Bootstrap.txt"
BOOTSTRAP_2 = ("Apache-2.0.txt", GLYPHICONS)
SOURCES = {
    "BSD-3-Clause.txt": f"{COLLECTION}/package.json",
    "highlight.js-BSD-3-Clause.txt": "https://github.com/highlightjs/highlight.js/blob/8.4/LICENSE",
    "bootstrap-3.1.1-MIT.txt": "https://github.com/twbs/bootstrap/blob/v3.1.1/LICENSE",
    "Apache-2.0.txt": "https://github.com/twbs/bootstrap/blob/v2.3.2/LICENSE",
    "github-markdown-css-MIT.txt": (
        "https://github.com/sindresorhus/github-markdown-css/blob/v2.0.0/license"
    ),
    "solarized-css-MIT.txt": "https://github.com/thomasf/solarized-css/blob/master/LICENSE",
    "ghostwriter-MIT.txt": "https://github.com/roryg/ghostwriter/blob/master/LICENSE.txt",
    "normalize.css-MIT.txt": "https://github.com/necolas/normalize.css/blob/v2.1.2/LICENSE.md",
    "nprogress-MIT.txt": "https://github.com/rstacruz/nprogress/blob/v0.1.2/License.md",
    "code-prettify-Apache-2.0.txt": "https://github.com/googlearchive/code-prettify/blob/master/COPYING",
    "CC-BY-SA-3.0.txt": "https://creativecommons.org/licenses/by-sa/3.0/",
    "LGPL-3.0.txt": "https://www.gnu.org/licenses/lgpl-3.0.html",
    "GPL-3.0.txt": "https://www.gnu.org/licenses/gpl-3.0.html",
    "Unlicense.txt": "https://unlicense.org/",
    GLYPHICONS: "https://github.com/twbs/bootstrap/blob/v3.1.1/docs/components.html",
}
GROOVEPAPER = (
    "Groovepaper by Isaac, Subtle Patterns, CC-BY-SA-3.0.\n"
    "https://www.toptal.com/designers/subtlepatterns/groovepaper/\n"
    "Decoded pixels unchanged; PNG encoding differs from the upstream copy."
)
BOOTSTRAP_CREDIT = "Bootstrap CSS: Copyright 2012 Twitter, Inc. Glyphicons: Jan Kovarik."
PRETTIFY_CREDIT = "Code Prettify: Copyright 2011 Mike Samuel et al; Sunburst: David Leibovic."

# Collection terms supplement, and never replace, the component-specific terms.
LAYOUTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "bootstrap3": (
        "Bootstrap 3.1.1: Copyright 2011-2014 Twitter, Inc.\n"
        "Glyphicons font: Copyright 2013 Jan Kovarik.",
        ("bootstrap-3.1.1-MIT.txt", "normalize.css-MIT.txt", GLYPHICONS),
    ),
    "github": ("github-markdown-css: Sindre Sorhus.", ("github-markdown-css-MIT.txt",)),
    "jasonm23-swiss": (
        "Theme: Copyright 2012 Florian Wolters. LGPL-3.0-or-later; see style.css.\n"
        "The distributed style.css is the editable source of this stylesheet.",
        ("LGPL-3.0.txt", "GPL-3.0.txt"),
    ),
    "mixu-book": (PRETTIFY_CREDIT, ("code-prettify-Apache-2.0.txt",)),
    "mixu-bootstrap": (BOOTSTRAP_CREDIT, BOOTSTRAP_2),
    "mixu-bootstrap-2col": (BOOTSTRAP_CREDIT, BOOTSTRAP_2),
    "mixu-gray": (
        BOOTSTRAP_CREDIT + "\nTextured Paper by Stephen Gilbert, Subtle Patterns, CC-BY-SA-3.0.\n"
        "https://www.toptal.com/designers/subtlepatterns/textured-paper/\n"
        "Decoded pixels unchanged; PNG encoding differs from the upstream copy.",
        (*BOOTSTRAP_2, "CC-BY-SA-3.0.txt"),
    ),
    "mixu-page": (GROOVEPAPER, ("code-prettify-Apache-2.0.txt", "CC-BY-SA-3.0.txt")),
    "mixu-radar": (GROOVEPAPER, ("CC-BY-SA-3.0.txt",)),
    "roryg-ghostwriter": (
        "Ghostwriter: Copyright 2013 Rory Gibson.\n"
        "normalize.css: Nicolas Gallagher and Jonathan Neal.\n"
        "NProgress: Copyright 2013 Rico Sta. Cruz.",
        ("ghostwriter-MIT.txt", "normalize.css-MIT.txt", "nprogress-MIT.txt"),
    ),
    "thomasf-solarizedcssdark": (
        "solarized-css: Copyright 2015 Thomas Frössman.\n"
        "normalize.css reset: Nicolas Gallagher and Jonathan Neal.",
        ("solarized-css-MIT.txt", "normalize.css-MIT.txt"),
    ),
    "thomasf-solarizedcsslight": (
        "solarized-css: Copyright 2015 Thomas Frössman.\n"
        "normalize.css reset: Nicolas Gallagher and Jonathan Neal.",
        ("solarized-css-MIT.txt", "normalize.css-MIT.txt"),
    ),
    "witex": ("WiTeX by Andrew Belt; dedication retained in style.css.", ("Unlicense.txt",)),
}


def notice_for(layout: str) -> str:
    credits, specific_licenses = LAYOUTS[layout]
    highlight_author = (
        "Solarized themes: Jeremy Hull; original Solarized colors by Ethan Schoonover."
        if layout.startswith("thomasf-")
        else "GitHub highlighting theme: Vasily Polovnyov <vast@whiteants.net>."
    )
    sections = [
        f"Licenses and attributions for the {layout} layout\n",
        "Keep this notice with redistributed layout resources.\n"
        "These terms cover the identified components, not the document author's content.\n",
        f"Collection/page/pilcrow contributions: Mikito Takada and contributors.\n{COLLECTION}\n"
        "BSD-3-Clause is declared by the upstream package metadata.\n"
        "Third-party theme and component rights are listed separately below.\n"
        "Local adaptations: pymdtools integration, JavaScript/remote-font removal;\n"
        "original notices retained. No Latin Modern font files are included.\n",
        credits + "\n",
    ]
    shared_licenses = ["BSD-3-Clause.txt"]
    if layout != "roryg-ghostwriter":
        sections.append(f"highlight.js: Copyright 2006 Ivan Sagalaev.\n{highlight_author}\n")
        shared_licenses.append("highlight.js-BSD-3-Clause.txt")
    for filename in (*shared_licenses, *specific_licenses):
        sections.append(
            f"{'=' * 72}\n{filename}\nSource: {SOURCES[filename]}\n\n"
            + (LICENSE_ROOT / filename).read_text(encoding="utf-8").rstrip()
            + "\n"
        )
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate the notices")
    args = parser.parse_args()
    actual = {p.parent.name for p in LAYOUT_ROOT.glob("*/page.html")}
    if actual != set(LAYOUTS):
        parser.error(f"Review licensing for added/removed layouts: {sorted(actual ^ set(LAYOUTS))}")
    outdated = []
    for layout in sorted(LAYOUTS):
        target = LAYOUT_ROOT / layout / "assets" / "LICENSES.txt"
        expected = notice_for(layout)
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            if args.write:
                target.write_text(expected, encoding="utf-8", newline="\n")
            else:
                outdated.append(layout)
    if outdated:
        print("Outdated notices; review sources and run with --write:", ", ".join(outdated))
        return 1
    print(f"License notices {'updated' if args.write else 'verified'} for {len(LAYOUTS)} layouts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
