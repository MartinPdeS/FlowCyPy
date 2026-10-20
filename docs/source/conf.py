"""Sphinx configuration for FlowCyPy documentation."""

import os
from pathlib import Path
import sys
from importlib.metadata import distribution as package_distribution

from martinpdes_docs import configure


DOCS_SOURCE = Path(__file__).resolve().parent
examples_sections = ["tutorials", "studies", "validation"]
installed_site = str(package_distribution("FlowCyPy").locate_file(""))
if installed_site in sys.path:
    sys.path.remove(installed_site)
sys.path.insert(0, installed_site)


globals().update(
    configure(
        project="FlowCyPy",
        package="FlowCyPy",
        repository="MartinPdeS/FlowCyPy",
        logo="_static/logo.png",
        favicon="_static/favicon.ico",
        version=os.getenv("tag", "latest"),
        html_theme_options={
            "logo": {
                "text": "",
                "image": "_static/logo.png",
                "alt_text": "FlowCyPy logo",
            },
            "show_nav_level": 1,
            "collapse_navigation": False,
        },
        sphinx_gallery_conf={
            "examples_dirs": [f"../examples/{name}" for name in examples_sections],
            "gallery_dirs": [f"gallery/{name}" for name in examples_sections],
            "image_scrapers": ("matplotlib",),
            "default_thumb_file": str(DOCS_SOURCE / "_static" / "gallery-default.png"),
            "reset_modules_order": "after",
            "within_subsection_order": "FileNameSortKey",
        },
    )
)

extensions += [
    "sphinx.ext.mathjax",
    "sphinx.ext.autosectionlabel",
]
