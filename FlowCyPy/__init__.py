try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"

debug_mode = False


_LAZY_EXPORTS = {
    "FlowCytometer": (".flow_cytometer", "FlowCytometer"),
    "Workflow": (".workflow", "Workflow"),
    "Fluidics": (".fluidics", "Fluidics"),
    "distributions": (".fluidics", "distributions"),
    "populations": (".fluidics", "populations"),
    "OptoElectronics": (".opto_electronics", "OptoElectronics"),
    "circuits": (".opto_electronics", "circuits"),
    "source": (".opto_electronics", "source"),
    "DigitalProcessing": (".digital_processing", "DigitalProcessing"),
    "classifier": (".digital_processing", "classifier"),
    "discriminator": (".digital_processing", "discriminator"),
    "peak_locator": (".digital_processing", "peak_locator"),
    "ureg": (".units", "ureg"),
}


def __getattr__(name: str):
    """Resolve public objects only when they are first accessed.

    Keeping the compatibility exports lazy makes ``import FlowCyPy`` cheap
    while retaining the established top-level API.
    """
    try:
        module_name, attribute_name = _LAZY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error

    from importlib import import_module

    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value

__all__ = [
    "__version__",
    "FlowCytometer",
    "Workflow",
    "Fluidics",
    "distributions",
    "populations",
    "OptoElectronics",
    "circuits",
    "source",
    "DigitalProcessing",
    "classifier",
    "discriminator",
    "peak_locator",
    "ureg",
    "debug_mode",
]
