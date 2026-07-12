# Third-party notices

`pymdtools` includes static layout resources derived from open-source projects.
The original notices embedded in those files must be retained. This inventory
describes the resources distributed in the Python wheel and source archive.

## markdown-styles layout collection

Most folders under `pymdtools/layouts/` are derived from
[`mixu/markdown-styles`](https://github.com/mixu/markdown-styles), by Mikito
Takada and contributors. The upstream package declares the BSD 3-Clause
license. Individual themes listed below retain their additional notices.

License: [BSD-3-Clause](THIRD_PARTY_LICENSES/BSD-3-Clause.txt).

## Bootstrap resources

- `layouts/bootstrap3/assets/css/bootstrap.min.css` and the accompanying
  Glyphicons resources identify Bootstrap 3.1.1, copyright 2011-2014 Twitter,
  Inc., licensed under MIT.
- The Bootstrap and Bootstrap Responsive CSS resources in `mixu-bootstrap`,
  `mixu-bootstrap-2col`, and `mixu-gray` identify Bootstrap 2.3.x, copyright
  2012 Twitter, Inc., licensed under Apache-2.0.

Licenses: [MIT](THIRD_PARTY_LICENSES/MIT.txt) and
[Apache-2.0](THIRD_PARTY_LICENSES/Apache-2.0.txt).

The obsolete Bootstrap and jQuery JavaScript files formerly shipped by these
layouts have been removed. Generated documents no longer load executable code
or fonts over plain HTTP.

## jasonm23-swiss theme

`layouts/jasonm23-swiss/assets/style.css` is copyright 2012 Florian Wolters and
declares LGPL version 3 or later. Its original notice remains in the file.

Licenses: [LGPL-3.0](THIRD_PARTY_LICENSES/LGPL-3.0.txt) and the incorporated
[GPL-3.0](THIRD_PARTY_LICENSES/GPL-3.0.txt).

## WiTeX theme

`layouts/witex/assets/css/style.css`, based on Andrew Belt's WiTeX, carries an
Unlicense/public-domain dedication. The formerly bundled Latin Modern font
files have been removed; the theme now uses local system serif fonts.

License: [Unlicense](THIRD_PARTY_LICENSES/Unlicense.txt).

## Other retained notices

- `markedapp-byword/assets/style.css` retains copyright notices for Brett
  Terpstra and Metaclassy, Lda.
- `roryg-ghostwriter/assets/css/normalize.css` identifies normalize.css under
  the MIT license.
- Highlighting, pilcrow, texture, and theme resources remain covered by the
  markdown-styles distribution license and any notices embedded in their
  source files.

This file is an engineering inventory, not legal advice. When adding or
updating a layout, update this inventory and include the applicable license
text in `THIRD_PARTY_LICENSES/` before publishing a distribution.
