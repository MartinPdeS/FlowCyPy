"""Public native classes are shared with their defining submodules."""

import FlowCyPy._utils
import FlowCyPy.fluidics.population_events
import FlowCyPy.fluidics.scatterer_collection
import FlowCyPy.opto_electronics.coupling_model


def test_native_exports_share_their_defining_classes():
    """Resolve each re-export through its fully qualified Python module."""
    fluidics = FlowCyPy.fluidics
    optics = FlowCyPy.opto_electronics
    assert fluidics.PopulationEvents is fluidics.population_events.PopulationEvents
    assert fluidics.ScattererCollection is fluidics.scatterer_collection.ScattererCollection
    assert optics.ScatteringModel is optics.coupling_model.ScatteringModel


def test_native_utilities_load_with_fft_support():
    """Exercise FFTW plan creation and destruction through the installed extension."""
    FlowCyPy._utils.butterworth_lowpass_filter(
        signal=[1.0] * 8, sampling_rate=8.0, cutoff_frequency=2.0, order=2
    )
