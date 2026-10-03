Installation and first steps
============================

Use Python 3.11 or newer. CI tests Python 3.11–3.14 on Linux and Windows, with
additional macOS coverage. Commands below run from a terminal; Python examples
can be saved as scripts. ``pymdtools`` is a library, with no general-purpose
``pymdtools`` command-line program.

Install a published version
---------------------------

Create a virtual environment in your working directory::

   python -m venv .venv

Activate it in PowerShell::

   .venv\Scripts\Activate.ps1

Or in a POSIX shell (Linux/macOS)::

   . .venv/bin/activate

Then install and check the version with the same interpreter::

   python -m pip install pymdtools
   python -c "import pymdtools; print(pymdtools.__version__)"

Activation is optional if you invoke that environment's Python directly.
For example, use ``.venv\Scripts\python.exe -m pip install pymdtools`` on
Windows when your shell does not allow activation scripts.

Markdown and HTML operations need no browser. For PDF rendering::

   python -m pip install "pymdtools[pdf]"
   python -m playwright install chromium

On Linux, add ``--with-deps`` to install browser system libraries. Browser
installation downloads files; subsequent rendering of local documents can run
offline. Metadata and overlay operations require the PDF extra but do not
launch Chromium. See :doc:`mdtopdf` for rendering and resource options.

Work from a checkout
--------------------

Use a checkout to run the examples, contribute changes or build this manual::

   git clone https://github.com/IIXIXII/pymdtools.git
   cd pymdtools
   python -m pip install uv==0.12.19
   uv sync --locked --group dev --group docs --extra pdf

This installs the package in editable mode under ``.venv``. Use
``uv run --no-sync`` for commands in that environment, for example::

   uv run --no-sync python examples/run_all.py --list
   uv run --no-sync python examples/run_all.py

The examples also ship in the source archive, together with their data. They
are not installed by the wheel. A core-only editable installation is sufficient
for the 23 standard scenarios: ``python -m pip install -e .``. See
:doc:`workflows` for the optional PDF scenarios.

Create and publish a document
-----------------------------

The following blocks form one runnable Python script. They write only under
``build/`` relative to the script's working directory. First assemble a variable
and a link in memory:

.. testcode::

   from pathlib import Path

   from pymdtools.mdfile import MarkdownContent

   output = Path("build")
   output.mkdir(exist_ok=True)
   document = MarkdownContent(
       content=(
           "# Welcome\n\n"
           "Project: <!-- begin-var(project) --><!-- end-var -->\n\n"
           "[User guide](guide.md)\n"
       )
   )
   document["project"] = "pymdtools"
   document.process_tags()
   assert document["project"] == "pymdtools"

Inspect links, normalize and save the result:

.. testcode::

   from pymdtools.mdcommon import search_link_in_md_text

   links = search_link_in_md_text(document.content or "")
   assert links[0]["url"] == "guide.md"
   document.beautify()
   document.write(output / "hello.md")
   assert not document.save_needed

Convert the saved file into a full HTML page:

.. testcode::

   from pymdtools.mdtopdf import convert_md_to_html

   html_path = convert_md_to_html(output / "hello.md", layout="github")
   assert html_path.is_file()
   assert (output / "_pymdtools_assets" / "github" / "LICENSES.txt").is_file()

Open ``build/hello.html``. Copy the adjacent ``_pymdtools_assets/`` tree when
sharing the page, including its license notices. The example link to
``guide.md`` is illustrative; link inspection does not create or check the target.
Running the script again replaces its outputs and creates a dated Markdown
backup. See :doc:`mdfile` for persistence and :doc:`mdtopdf` for PDF output.

Build this manual
-----------------

In the locked development environment::

   uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b html docs docs/_build/html
   uv run --no-sync python -m sphinx.cmd.build -W --keep-going -b doctest docs docs/_build/doctest

Open ``docs/_build/html/index.html``. The doctest builder executes the marked
offline Python examples in temporary directories, without translation requests
or Chromium. The :doc:`contributing` guide lists the remaining checks.

For a documentation-only installation without uv, use pip 25.1 or newer from
the repository root, in one Python environment::

   python -m pip install --group docs .
   python -m sphinx.cmd.build -W --keep-going -b html docs docs/_build/html
   python -m sphinx.cmd.build -W --keep-going -b doctest docs docs/_build/doctest
