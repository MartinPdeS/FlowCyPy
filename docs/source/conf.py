"""Sphinx configuration for FlowCyPy documentation."""

from martinpdes_docs import configure


gallery_sections = ["tutorials", "studies", "validation"]


globals().update(
    configure(
        project="FlowCyPy",
        package="FlowCyPy",
        repository="MartinPdeS/FlowCyPy",
        logo="_static/logo.png",
        favicon="_static/favicon.ico",
        gallery_sections=gallery_sections,
        gallery_default_thumb="_static/gallery-default.png",
        prefer_installed_package=True,
        logo_text="",
        logo_alt_text="FlowCyPy logo",
        html_theme_options={
            "show_nav_level": 1,
            "collapse_navigation": False,
        },
    )
)
