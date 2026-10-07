"""Sphinx configuration for geoaquacrop_simulate."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../src"))

project = "geoaquacrop-simulate"
author = "Christopher Bowden"
copyright = f"{datetime.now():%Y}, {author}"
release = "0.1.0"
version = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# Napoleon: accept both NumPy- and Google-style docstrings.
napoleon_google_docstring = True
napoleon_numpy_docstring = True

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

# plots.py is an interactive Dash dashboard with module-level configuration and
# side effects; importing it during a docs build would execute that setup, so it
# is documented narratively rather than by autodoc.
autodoc_mock_imports = []          # nothing to mock: every module imports cleanly

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "preprocess": (
        "https://geoaquacrop-preprocess.readthedocs.io/en/latest/", None),
    "visualize": ("https://geoaquacrop-visualize.readthedocs.io/en/stable/",      None)
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]
html_favicon = "_static/favicon.png"

html_theme_options = {
    "light_logo": "logo.svg",
    "dark_logo": "logo.svg",
}
html_title = f"{project} {release}"
