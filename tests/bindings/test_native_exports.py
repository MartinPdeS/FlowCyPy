"""Public native classes are shared with their defining submodules."""

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
