"""Public native classes are shared with their defining submodules."""

from importlib import import_module
from importlib.machinery import EXTENSION_SUFFIXES
from pkgutil import iter_modules
import FlowCyPy._utils
import FlowCyPy.digital_processing.pipeline
import FlowCyPy.fluidics.population_events
import FlowCyPy.fluidics.scatterer_collection
import FlowCyPy.opto_electronics.coupling_model


def test_native_exports_share_their_defining_classes():
    """Resolve each re-export through its fully qualified Python module."""
    pipeline = FlowCyPy.digital_processing.pipeline
    assert FlowCyPy.DigitalProcessing is pipeline.DigitalProcessing
    assert pipeline.__file__.endswith(tuple(EXTENSION_SUFFIXES))
    fluidics = FlowCyPy.fluidics
    optics = FlowCyPy.opto_electronics
    assert fluidics.Fluidics is fluidics.system.Fluidics
    assert fluidics.system.__file__.endswith(tuple(EXTENSION_SUFFIXES))
    assert fluidics.PopulationEvents is fluidics.population_events.PopulationEvents
    assert (
        fluidics.ScattererCollection
        is fluidics.scatterer_collection.ScattererCollection
    )
    assert FlowCyPy.OptoElectronics is optics.system.OptoElectronics
    assert optics.system.__file__.endswith(tuple(EXTENSION_SUFFIXES))
    assert optics.ScatteringModel is optics.coupling_model.ScatteringModel


def test_native_utilities_load_with_fft_support():
    """Exercise FFTW plan creation and destruction through the installed extension."""
    FlowCyPy._utils.butterworth_lowpass_filter(
        signal=[1.0] * 8, sampling_rate=8.0, cutoff_frequency=2.0, order=2
    )


def test_native_classes_have_docs_and_repr():
    """Check that each native class documents itself and defines its representation."""
    for package in (
        FlowCyPy.fluidics,
        FlowCyPy.opto_electronics,
        FlowCyPy.digital_processing,
    ):
        for entry in iter_modules(package.__path__):
            module = import_module(f"{package.__name__}.{entry.name}")
            if not (module.__file__ or "").endswith(tuple(EXTENSION_SUFFIXES)):
                continue

            for cls in vars(module).values():
                if isinstance(cls, type) and cls.__module__ == module.__name__:
                    assert cls.__doc__ and cls.__doc__.strip(), cls
                    assert "__repr__" in vars(cls), cls


def test_normal_repr_shows_units_and_configured_cutoffs():
    """Show a physical bound while omitting the unbounded lower limit."""
    units = FlowCyPy.ureg
    distribution = FlowCyPy.distributions.Normal(
        mean=10 * units.nanometer,
        standard_deviation=2 * units.nanometer,
        high_cutoff=15 * units.nanometer,
    )
    description = repr(distribution)
    assert "mean=10 nanometer" in description
    assert "high_cutoff=15 nanometer" in description
    assert "low_cutoff" not in description
