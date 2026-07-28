import FlowCyPy


def test_top_level_public_api_is_explicit():
    assert FlowCyPy.__all__ == [
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
