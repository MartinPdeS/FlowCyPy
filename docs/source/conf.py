#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import datetime
from sphinx_gallery.sorting import FileNameSortKey
from MPSPlots.styles import use_mpsplots_style
from pathlib import Path
import FlowCyPy
from FlowCyPy.directories import doc_css_path


package_name = "FlowCyPy"
version = FlowCyPy.__version__

current_dir = Path("../")

sys.path.append(str(current_dir.resolve()))


def setup(app):
    app.add_css_file(str(doc_css_path))


autodoc_mock_imports = [
    'numpy',
    'pydantic',
    'matplotlib',
    'numpydoc',
]


project = package_name
copyright = f'2024-{datetime.date.today().year}, Martin Poinsinet de Sivry-Houle'
author = 'Martin Poinsinet de Sivry-Houle'

extensions = [
    'sphinx.ext.mathjax',
    'pyvista.ext.plot_directive',
    'sphinx_gallery.gen_gallery',
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
]

autodoc_typehints = "description"
autosummary_generate = True

# Napoleon settings for docstrings
napoleon_google_docstring = False
napoleon_numpy_docstring = True

html_logo = "_static/thumbnail.png"
html_favicon = "_static/thumbnail.png"

def reset_mpl(gallery_conf, fname):
    use_mpsplots_style()

examples_files = [
    'tutorials',
    'noise_sources',
    'validation',
]

sphinx_gallery_conf = {
    'reset_modules_order': 'after',
    "examples_dirs": ['../examples/' + f for f in examples_files],
    "gallery_dirs": ['gallery/' + f for f in examples_files],
    'image_scrapers': ('matplotlib'),
    'ignore_pattern': '/__',
    'filename_pattern': r'.*\.py',
    'plot_gallery': True,
    'thumbnail_size': [600, 600],
    'download_all_examples': False,
    'reset_modules': reset_mpl,
    'line_numbers': False,
    'remove_config_comments': True,
    'capture_repr': ('_repr_html_', '__repr__'),
    'nested_sections': True,
    'within_subsection_order': FileNameSortKey,
}


autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "exclude-members": "__annotations__",
    'members-order': 'bysource',
}

autosectionlabel_prefix_document = True
numpydoc_show_class_members = False
add_module_names = False

source_suffix = '.rst'
master_doc = 'index'
language = 'en'
highlight_language = 'python3'
html_theme = "pydata_sphinx_theme"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

exclude_trees = []
# default_role = "autolink"
show_authors = True
pygments_style = "sphinx"

# -- Sphinx-gallery configuration --------------------------------------------
major, minor = version[:2]
binder_branch = f"v{major}.{minor}.x"

html_context = {
    "github_url": "https://github.com", # or your GitHub Enterprise site
    "github_user": "FlowCyPy",
    "github_repo": "FlowCyPy",
    "github_version": "master",
    "doc_path": "doc/source",
    "default_mode": "dark",
}

html_theme_options = dict()

html_theme_options['logo'] = dict(text=package_name, image="_static/thumbnail.png")
# html_theme_options["show_nav_level"] = 0


html_theme_options.update({
    "github_url": "https://github.com/MartinPdeS/FlowCyPy",
    "icon_links": [
        {
            "name": "PyPI",
            "url": f"https://pypi.org/project/{package_name}/",
            "icon": "fa-solid fa-box",
        },
        {
            "name": "Anaconda",
            "url": f"https://anaconda.org/MartinPdeS/{package_name}",
            "icon": "fa-brands fa-python",
        },
    ],
    "navbar_align": "left",
    "navbar_end": ["version-switcher", "theme-switcher", "navbar-icon-links"],
    "show_prev_next": False,
    "show_version_warning_banner": True,
    # Footer
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version", "theme-version"],
    # Other
    "pygments_light_style": "default",
    "pygments_dark_style": "github-dark",
    "show_nav_level": 2,
    "collapse_navigation": False
}
)

current_version = os.getenv("tag", "latest")

html_theme_options["switcher"] = dict(
    json_url=f"https://raw.githubusercontent.com/MartinPdeS/{package_name}/documentation_page/version_switcher.json",
    version_match=current_version,
)

htmlhelp_basename = f'{package_name}doc'

latex_elements = {}


latex_documents = [
    (master_doc, f'{package_name}.tex', '', 'Martin Poinsinet de Sivry-Houle', 'manual'),
]

man_pages = [
    (master_doc, 'FlowCyPy', '', [author], 1)
]

texinfo_documents = [
    (master_doc, package_name, '', author, package_name, 'One line description of project.', 'Miscellaneous'),
]

epub_title = project

html_static_path = ['_static']
templates_path = ['_templates']
html_css_files = ['_static/default.css']
epub_exclude_files = ['search.html']


# Intersphinx to get NumPy, SciPy, and other targets
intersphinx_mapping = {
    'numpy': ('https://numpy.org/devdocs', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}

# -
