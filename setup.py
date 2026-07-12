#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ===============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# ===============================================================================
"""Setuptools build configuration.

Release operations deliberately live in ``scripts/release.py``.  Keeping this
file declarative prevents a package build from mutating Git state or publishing
artifacts as a side effect.
"""

from pathlib import Path

from setuptools import find_packages, setup


PACKAGE = "pymdtools"
ROOT = Path(__file__).resolve().parent

about: dict[str, object] = {}
exec((ROOT / PACKAGE / "_about.py").read_text(encoding="utf-8"), about)

version: dict[str, object] = {}
exec((ROOT / PACKAGE / "version.py").read_text(encoding="utf-8"), version)
package_version = ".".join(map(str, version["__version_info__"]))


setup(
    name=str(about["__title__"]),
    version=package_version,
    author=str(about["__author__"]),
    author_email=str(about["__author_email__"]),
    license="MIT",
    description=str(about["__description__"]),
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/IIXIXII/pymdtools",
    project_urls={
        "Documentation": "https://pymdtools.readthedocs.io/",
        "Issues": "https://github.com/IIXIXII/pymdtools/issues",
        "Source": "https://github.com/IIXIXII/pymdtools",
    },
    install_requires=[
        "beautifulsoup4>=4.12,<5",
        "chardet>=5,<6",
        "markdown>=3.5,<4",
        "markdownify>=1.1,<2",
        "mistune>=3.0,<4",
        "pdfkit>=1.0,<2",
        "pypdf>=6,<7",
        "python-dateutil>=2.8,<3",
        "unidecode>=1.3,<2",
    ],
    packages=find_packages(exclude=("tests", "tests.*")),
    package_data={
        PACKAGE: [
            "*.conf",
            "*.ico",
            "*.md",
            "layouts/**/*",
            "referenced_files/*.txt",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": [
            "build>=1.2,<2",
            "pyright>=1.1.350,<2",
            "pytest>=7,<10",
            "pytest-cov>=5,<8",
            "twine>=5,<7",
            "vulture>=2.11,<3",
        ],
        "docs": [
            "myst-parser>=3,<5",
            "sphinx>=8,<9",
            "sphinx-rtd-theme>=3,<4",
        ],
    },
)
