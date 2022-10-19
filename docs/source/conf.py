# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../examples"))
sys.path.insert(0, os.path.abspath("../../examples/firesat"))
sys.path.insert(0, os.path.abspath("../../examples/firesat/fires"))
sys.path.insert(0, os.path.abspath("../../examples/firesat/fires/fire_config_files"))
sys.path.insert(0, os.path.abspath("../../examples/firesat/grounds"))
sys.path.insert(0, os.path.abspath("../../examples/firesat/satellites"))
sys.path.insert(0, os.path.abspath("../../examples/firesat/manager"))
sys.path.insert(0, os.path.abspath("../../examples/realtime"))
sys.path.insert(0, os.path.abspath("../../examples/scalability"))
sys.path.insert(0, os.path.abspath("../../examples/scalability/delay"))
sys.path.insert(0, os.path.abspath("../../examples/scalability/heartbeat"))
import manager, satellites, grounds, fires, realtime, delay, heartbeat
import sphinx_rtd_theme


# -- Project information -----------------------------------------------------

project = 'New Observing Strategies - Testbed (NOS-T)'
copyright = '2022, Stevens Institute of Technology'
author = 'NOS-T Team'

# The full version, including alpha/beta/rc tags
release = '1.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx_rtd_theme"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["build"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["source/_static"]
