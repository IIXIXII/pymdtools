# Bundled third-party licenses and provenance

Reviewed on 2026-10-03. Paths below are relative to `src/pymdtools/layouts/`.
The original Python implementation is MIT-licensed; this does not relicense
third-party templates, stylesheets, images or fonts.

The wheel and source archive include this inventory and the full notices under
`THIRD_PARTY_LICENSES/`. Each layout also contains `assets/LICENSES.txt`, copied
alongside its resources when generating HTML. Keep that file with exported assets.
Installed Python dependencies are covered separately in
[LICENSES-dependencies.md](LICENSES-dependencies.md).

## Collection and local changes

The layouts originate from [markdown-styles](https://github.com/mixu/markdown-styles),
by Mikito Takada and contributors. Its
[package declaration](https://github.com/mixu/markdown-styles/blob/eed20d2c71e7bf456e5bfbcd27135ac662002cd3/package.json)
specifies BSD-3-Clause. The collection's
[credits](https://github.com/mixu/markdown-styles/blob/eed20d2c71e7bf456e5bfbcd27135ac662002cd3/readme.md#acknowledgments)
identify the independent theme authors. This revision is the audit reference,
not a claim that every local file matches that revision byte for byte.

Collection terms: [BSD-3-Clause](THIRD_PARTY_LICENSES/BSD-3-Clause.txt).
The collection declaration is not evidence of permission to relicense the
independent works listed below. Original in-file notices remain authoritative.

Local adaptations include Python template integration, removal of bundled
JavaScript and remote font loads, and removal of WiTeX's Latin Modern fonts.
Upstream notices have been retained. These changes do not replace the original
licenses. No Latin Modern fonts, jQuery or Bootstrap JavaScript are distributed.

## Theme inventory

All layouts also include the collection's page/pilcrow adaptations. All except
`roryg-ghostwriter` contain a highlight.js stylesheet, described below.

| Layout | Theme-specific origin and identified terms |
| --- | --- |
| `bootstrap3` | Bootstrap 3.1.1 CSS: MIT; embedded normalize.css: MIT; Glyphicons have a separate Bootstrap permission notice. |
| `github` | Sindre Sorhus, github-markdown-css: MIT. |
| `jasonm23-swiss` | Florian Wolters, copyright 2012: LGPL-3.0-or-later, explicitly declared in `assets/style.css`. |
| `mixu-book` | Mikito Takada's collection contributions: BSD-3-Clause; Google Code Prettify styles: Apache-2.0. |
| `mixu-bootstrap` | Collection contributions: BSD-3-Clause; Bootstrap 2.3.x CSS: Apache-2.0; Glyphicons have a separate Bootstrap permission notice. |
| `mixu-bootstrap-2col` | Collection contributions: BSD-3-Clause; Bootstrap 2.3.x CSS: Apache-2.0; Glyphicons have a separate Bootstrap permission notice. |
| `mixu-gray` | Same Bootstrap/Glyphicons terms, plus Stephen Gilbert's Textured Paper: CC-BY-SA-3.0. |
| `mixu-page` | Collection contributions: BSD-3-Clause; Code Prettify: Apache-2.0; Isaac's Groovepaper: CC-BY-SA-3.0. |
| `mixu-radar` | Collection contributions: BSD-3-Clause; Isaac's Groovepaper: CC-BY-SA-3.0. |
| `roryg-ghostwriter` | Rory Gibson's Ghostwriter: MIT; normalize.css and NProgress: MIT. |
| `thomasf-solarizedcssdark` | Thomas Frössman's solarized-css: MIT, including normalize.css reset rules; highlight.js Solarized theme credits Jeremy Hull. |
| `thomasf-solarizedcsslight` | Same solarized-css/normalize.css terms and Jeremy Hull credit. |
| `witex` | Andrew Belt's WiTeX; the local stylesheet explicitly carries an Unlicense/public-domain dedication. |

## Shared components and exact notices

| Files/component | Attribution and source | Distributed notice |
| --- | --- | --- |
| `**/hljs-github.min.css` | highlight.js; GitHub theme by Vasily Polovnyov. [Upstream BSD terms, tag 8.4](https://github.com/highlightjs/highlight.js/blob/8.4/LICENSE), copyright 2006 Ivan Sagalaev. | [highlight.js-BSD-3-Clause.txt](THIRD_PARTY_LICENSES/highlight.js-BSD-3-Clause.txt) |
| `**/hljs-solarized-*.min.css` | highlight.js; Solarized themes by Jeremy Hull, based on Ethan Schoonover's Solarized colors. Same BSD terms. | [highlight.js-BSD-3-Clause.txt](THIRD_PARTY_LICENSES/highlight.js-BSD-3-Clause.txt) |
| `bootstrap3/assets/css/bootstrap.min.css` | Twitter, Inc., copyright 2011-2014. [Bootstrap 3.1.1](https://github.com/twbs/bootstrap/blob/v3.1.1/LICENSE). | [bootstrap-3.1.1-MIT.txt](THIRD_PARTY_LICENSES/bootstrap-3.1.1-MIT.txt) |
| `mixu-{bootstrap,bootstrap-2col,gray}/assets/css/bootstrap*.css` | Twitter, Inc., copyright 2012; versions retained in each CSS header. [Bootstrap 2.3.2](https://github.com/twbs/bootstrap/blob/v2.3.2/LICENSE). | [Apache-2.0.txt](THIRD_PARTY_LICENSES/Apache-2.0.txt) |
| `bootstrap3/assets/fonts/glyphicons-halflings-regular.*` and Bootstrap 2 PNG sprites | Jan Kovarik / Glyphicons. The font's name table identifies copyright 2013 Jan Kovarik. Bootstrap documents a special free-use arrangement for Halflings. Do not describe these fonts as Twitter's own MIT work. | [LicenseRef-Glyphicons-Bootstrap.txt](THIRD_PARTY_LICENSES/LicenseRef-Glyphicons-Bootstrap.txt) |
| `github/assets/css/github-markdown.css` | [Sindre Sorhus](https://github.com/sindresorhus/github-markdown-css/blob/v2.0.0/license). | [github-markdown-css-MIT.txt](THIRD_PARTY_LICENSES/github-markdown-css-MIT.txt) |
| `thomasf-solarizedcss*/assets/style.css` | [Thomas Frössman](https://github.com/thomasf/solarized-css/blob/master/LICENSE), copyright 2015. | [solarized-css-MIT.txt](THIRD_PARTY_LICENSES/solarized-css-MIT.txt) |
| `roryg-ghostwriter/assets/css/style.css` and its theme template | [Rory Gibson](https://github.com/roryg/ghostwriter/blob/master/LICENSE.txt), copyright 2013. | [ghostwriter-MIT.txt](THIRD_PARTY_LICENSES/ghostwriter-MIT.txt) |
| `roryg-ghostwriter/assets/css/normalize.css`, reset rules in Bootstrap 3 and solarized-css | Nicolas Gallagher and Jonathan Neal. [normalize.css 2.1.2](https://github.com/necolas/normalize.css/blob/v2.1.2/LICENSE.md) and [3.0.0](https://github.com/necolas/normalize.css/blob/3.0.0/LICENSE.md) have the same notice. | [normalize.css-MIT.txt](THIRD_PARTY_LICENSES/normalize.css-MIT.txt) |
| `roryg-ghostwriter/assets/css/nprogress.css` | [Rico Sta. Cruz](https://github.com/rstacruz/nprogress/blob/v0.1.2/License.md), copyright 2013. | [nprogress-MIT.txt](THIRD_PARTY_LICENSES/nprogress-MIT.txt) |
| `mixu-book/assets/{prettify,sunburst}.css`, `mixu-page/assets/css/prettify.css` | [Google Code Prettify](https://github.com/googlearchive/code-prettify/blob/master/COPYING), copyright 2011 Mike Samuel et al. `sunburst.css` also credits David Leibovic. | [code-prettify-Apache-2.0.txt](THIRD_PARTY_LICENSES/code-prettify-Apache-2.0.txt) |
| `jasonm23-swiss/assets/style.css` | Florian Wolters; LGPL version 3 or later as stated in the file. | [LGPL-3.0.txt](THIRD_PARTY_LICENSES/LGPL-3.0.txt) and [GPL-3.0.txt](THIRD_PARTY_LICENSES/GPL-3.0.txt) |
| `witex/assets/css/style.css` | Andrew Belt; dedication embedded in the stylesheet. | [Unlicense.txt](THIRD_PARTY_LICENSES/Unlicense.txt) |

The generic [MIT text](THIRD_PARTY_LICENSES/MIT.txt) is a reference; the
component-specific copies above preserve the actual upstream copyright notices.

## Texture images

The local PNGs have different compression/metadata from the Subtle Patterns
copies, but their decoded pixels were verified identical during this review.
Both Groovepaper copies in the module are identical.

| Paths | Original author and work | License |
| --- | --- | --- |
| `mixu-page/assets/img/groovepaper.png`, `mixu-radar/assets/img/groovepaper.png` | Isaac, [Groovepaper](https://www.toptal.com/designers/subtlepatterns/groovepaper/) | CC-BY-SA-3.0 |
| `mixu-gray/assets/img/textured_paper.png` | Stephen Gilbert, [Textured Paper](https://www.toptal.com/designers/subtlepatterns/textured-paper/) | CC-BY-SA-3.0 |

The [Subtle Patterns repository](https://github.com/subtlepatterns/SubtlePatterns/blob/gh-pages/README.md)
declares CC-BY-SA-3.0. The full [legal code](THIRD_PARTY_LICENSES/CC-BY-SA-3.0.txt)
is included. Keep the author, source and license attribution with redistributed
images; adaptations of those images remain subject to their ShareAlike terms.

## Replaced historical themes

The original resources for `jasonm23-dark`, `jasonm23-foghorn`,
`jasonm23-markdown` and `markedapp-byword` are no longer distributed because
an explicit original-author redistribution grant could not be established.
Their names remain accepted as compatibility aliases: the dark theme uses
`thomasf-solarizedcssdark`; the other three use `github`. Appearance changes,
and exported assets and notices belong to the replacement theme.

## Distribution and maintenance

The SPDX expression in `pyproject.toml` describes the identified terms of the
distributed files, not a choice between licenses. It does not change the MIT
license of the original project code. Separately installed dependencies are not
folded into this expression; review their terms when assembling or redistributing an application.

The CSS sources and their embedded notices are retained in the wheel and source
archive. When sharing generated HTML/assets, keep `assets/LICENSES.txt` (exported
under `_pymdtools_assets/<layout>/LICENSES.txt`). PDF output does not automatically
attach these text files: supply the applicable notices alongside any redistributed
resources and review the terms of embedded fonts and modified styles.

When changing a layout, update its attribution and exported `LICENSES.txt`, retain
upstream notices, and update the bundled license texts and SPDX expression. Never
apply the project's MIT header to upstream resources.
