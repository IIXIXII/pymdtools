#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
# Copyright (c) 2018 Florent TOURNOIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# @package pymdtools
# Markdown Tools develops for Gucihet Entreprises
#
# -----------------------------------------------------------------------------

import sys
import io
import os
import os.path
import time
from shutil import rmtree
from setuptools import setup, Command

__root__ = os.path.abspath(os.path.join(os.path.dirname(__file__)))

# ---------------------------------------------------------------------------
# Load package metadata WITHOUT importing the package (PEP517/660 safe)
# ---------------------------------------------------------------------------
__root__ = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(__root__, "pymdtools", "_about.py"), encoding="utf-8") as f:
    exec(f.read(), about)

version = {}
with open(os.path.join(__root__, "pymdtools", "version.py"), encoding="utf-8") as f:
    exec(f.read(), version)

__version__ = ".".join(map(str, version["__version_info__"]))


# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
__long_description__ = ""
try:
    with io.open(os.path.join(__root__, 'README.md'), encoding='utf-8') as f:
        __long_description__ = '\n' + f.read()
except FileNotFoundError:
    __long_description__ = ""

# -------------------------------------------------------------------------------
# Increase the version number
# -------------------------------------------------------------------------------


def print_status(msg):
    print('>> {0}'.format(msg))

# -------------------------------------------------------------------------------
# Increase the version number
# -------------------------------------------------------------------------------


def increase_version():
    about = {}
    with open(os.path.join(__root__, "pymdtools",
                           'version.py'), "r") as ver:
        exec(ver.read(), about)

    current_version = about['__version_info__']
    new_version = (current_version[0],
                   current_version[1],
                   current_version[2] + 1)
    print_status("New version = %s.%s.%s" % new_version)

    with open(os.path.join(__root__, "pymdtools",
                           'version.py'), "w") as ver:
        ver.write("#!/usr/bin/env python\n")
        ver.write("# -*- coding: utf-8 -*-\n\n")
        ver.write("__version_info__ = %s\n" % repr(new_version))
        ver.write("__release_date__ = '%s'\n" %
                  time.strftime("%Y-%m-%d", time.gmtime()))


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(msg):
        print_status(msg)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(__root__, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel '
                  '--universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload --verbose dist/*')

        sys.exit()


class IncreaseVersionCommand(Command):
    """Support setup.py increaseversion."""

    description = 'Increase the package version.'
    user_options = []

    @staticmethod
    def status(msg):
        print_status(msg)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status('Change version number…')
        increase_version()
        sys.exit()


class TagVersionCommand(Command):
    """Support setup.py increaseversion."""

    description = 'Increase the package version.'
    user_options = []

    @staticmethod
    def status(msg):
        print_status(msg)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status('Tag the version number {0}'.format(__version__))
        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(__version__))
        os.system('git push --tags')
        sys.exit()


# -------------------------------------------------------------------------------
# All setup parameter
# -------------------------------------------------------------------------------
setup(
    name=about["__title__"],
    version=__version__,
    author=about["__author__"],
    author_email=about["__author_email__"],
    license=about["__license__"],
    description=about["__description__"],
    long_description=__long_description__,
    long_description_content_type="text/markdown",

    url="https://github.com/IIXIXII/pymdtools",

    install_requires=[
        "markdown",
        "pdfkit",
        "PyPDF2",
        "python-dateutil",
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],

    packages=["pymdtools"],
    package_dir={"pymdtools": "pymdtools"},

    package_data={
        "pymdtools": [
            "*.conf",
            "*.ico",
            "*.md",
            "layouts/**/*",
            "referenced_files/*.txt",
        ],
    },

    python_requires=">=3.7",

    tests_require=["pytest"],
    setup_requires=["pytest-runner"],

    cmdclass={
        "upload": UploadCommand,
        "increaseversion": IncreaseVersionCommand,
        "tagversion": TagVersionCommand,
    },
)
# -----------------------------------------------------------------------------
