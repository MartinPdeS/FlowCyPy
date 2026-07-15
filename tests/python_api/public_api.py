import FlowCyPy


def test_top_level_public_api_is_explicit():
    assert FlowCyPy.__all__ == [
        "__version__",
        "FlowCytometer",
        "Fluidics",
        "OptoElectronics",
        "DigitalProcessing",
        "debug_mode",
    ]