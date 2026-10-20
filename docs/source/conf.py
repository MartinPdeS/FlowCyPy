"""Sphinx configuration for FlowCyPy documentation."""

import os
from pathlib import Path

from MPSPlots.styles import use_mpsplots_style
from martinpdes_docs import configure


DOCS_SOURCE = Path(__file__).resolve().parent
examples_sections = ["tutorials", "studies", "validation"]


def reset_mpl(gallery_conf, fname):
    """Restore the project's plotting style before each gallery example."""
    use_mpsplots_style()


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
            "reset_modules": reset_mpl,
            "within_subsection_order": "FileNameSortKey",
        },
    )
)

extensions += [
    "sphinx.ext.mathjax",
    "pyvista.ext.plot_directive",
    "sphinx.ext.autosectionlabel",
]

autodoc_default_options.update(
    {"members": True, "exclude-members": "__annotations__", "member-order": "bysource"}
)
autosectionlabel_maxdepth = 1
intersphinx_mapping = {
    "numpy": ("https://numpy.org/devdocs", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}
