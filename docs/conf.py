# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Cata-Log - the central hub for grocery store catalogs
# Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import sys
import tomllib
import os

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../src/"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Cata-Log"
copyright = "2026 David Aderbauer & The Cata-Log Contributors; Licensed under CC BY-SA 4.0 International"
author = "David Aderbauer & The Cata-Log Contributors"
release = "0.1.0"
year = datetime.date.today().year

with open("../pyproject.toml", "rb") as pyproject_toml:
    config = tomllib.load(pyproject_toml)

version = config["project"]["version"]
release = config["project"]["version"]

python_version = ".".join(map(str, sys.version_info[0:2]))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.coverage",
    "sphinx.ext.apidoc",  # sphinx-apidoc run automatically with sphinx-build
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Options for figure numbering

numfig = True
numfig_secnum_depth = 1

# Options for internationalisation

language = "en"

# Options for markup

default_role = None
option_emphasise_placeholders = False
rst_epilog = ""
rst_prolog = ""
trim_footnote_reference_space = True

# Options for the nitpicky mode

nitpicky = True
nitpick_ignore = ()
nitpick_ignore_regex = []

# Options for object signatures

toc_object_entries = False
toc_object_entries_show_parents = "domain"

# Options for source files

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_sidebars = {
    "**": [
        "about.html",
        "searchfield.html",
        "navigation.html",
        "relations.html",
        "donate.html",
    ]
}
html_theme_options = {
    "description": "The central hub for grocery store catalogs",
    "logo": "",
    # "logo_name": ,
    "touch_icon": "",
    "github_button": True,
    "github_repo": "cata-log",
    "github_user": "Cata-Log",
    "show_powered_by": True,
    "show_relbars": True,
    "fixed_sidebar": True,
}
html_title = "Cata-Log Docs"
html_short_title = "Cata-Log Docs"
html_logo = ""
html_favicon = ""
html_static_path = ["_static"]
html_last_updated_fmt = ""
html_show_sourcelink = True

# -- Autodoc configuration  ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

autoclass_content = "class"
autodoc_class_signature = "mixed"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "exclude-members": "_abc_impl",
    "member-order": "bysource",
    "undoc-members": True,
    "private-members": True,
    "special-members": "__init__, __str__",
    "show-inheritance": True,
    "inherited-members": False,
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_inherit_docstrings = True


# -- Apidoc configuration  ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/apidoc.html#configuration
#
apidoc_modules = [
    {"path": "../src/cata_log", "destination": "apidoc-rst/cata_log"},
    {"path": "../test", "destination": "apidoc-rst/test"},
]

apidoc_exclude_patterns = [
    "**/.git/**",
    "**/tools/**",
    "**/docker/**",
    "**/migrations/**",
    "**/manage.py",
    "**/__pycache__/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/.pytest_cache/**",
    "**/.vscode/**",
    "**/.venv/**",
    "**/venv/**",
    "**/htmlcov/**",
    "**/reports/**",
    "**/.coverage",
    "**/*.log",
]

apidoc_separate_modules = True
apidoc_module_first = True
apidoc_include_private = False
apidoc_implicit_namespaces = True


# -- Intersphinx configuration  ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": (f"https://docs.python.org/{python_version}", None),
    "pydantic": ("https://pydantic.dev/docs/validation/latest", None),
    "starlette": ("https://starlette.dev", None),
    "fastapi": ("https://fastapi.tiangolo.com", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/latest", None),
    "apscheduler": ("https://apscheduler.readthedocs.io/en/3.x", None),
}


# -- Napoleon configuration  ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False  # restores default autodoc behaviour
napoleon_include_private_with_doc = False  # restores default autodoc behaviour
napoleon_include_special_with_doc = False  # restores default autodoc behaviour
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_keyword = True
napoleon_use_rtype = True


# -- Todo configuration  ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True
todo_emit_warnings = False
todo_link_only = False


# -- Coverage configuration  ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/coverage.html#configuration

coverage_show_missing_items = True
coverage_statistics_to_stdout = False
