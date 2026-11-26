"""Public population factories and independent sampling."""

import numpy as np
import pytest
from FlowCyPy.fluidics.populations import SpherePopulation
from FlowCyPy.samples import beads, cells, lipoproteins, vesicles
from FlowCyPy.units import ureg


@pytest.mark.parametrize(
    ("factory", "default_name"),
    [
        (vesicles.exosome, "Exosome"),
        (vesicles.microvesicle, "MicroVesicle"),
        (vesicles.apoptotic_bodies, "ApoptoticBodies"),
        (lipoproteins.hdl, "HDL"),
        (lipoproteins.ldl, "LDL"),
        (lipoproteins.vldl, "VLDL"),
        (cells.platelet, "Platelet"),
        (cells.cellular_debris, "CellularDebris"),
    ],
)
def test_preset_builds_independent_populations(factory, default_name):
    """Advancing one population's sampler leaves the other at its original seed."""
    concentration = 5 * ureg.particle / ureg.milliliter
    first = factory(name="first", concentration=concentration)
    second = factory(concentration=concentration)
    assert isinstance(first, SpherePopulation)
    assert first.name == "first" and second.name == default_name
    assert first.concentration == second.concentration == concentration
    first.seed(123)
    second.seed(123)
    expected = first.sample(16)
    first.sample(9)
    actual = second.sample(16)
    for column in expected:
        np.testing.assert_array_equal(
            actual[column].m_as(expected[column].units), expected[column].magnitude
        )


def test_microbeads_have_fixed_diameter_and_refractive_index():
    """Every sampled bead has the requested diameter and refractive index."""
    diameter = 0.3 * ureg.micrometer
    index = 1.59 * ureg.RIU
    sample = beads.microbeads(name="beads", diameter=diameter, refractive_index=index)
    properties = sample.sample(3)
    np.testing.assert_allclose(properties["Diameter"].m_as("nm"), [300] * 3)
    np.testing.assert_allclose(properties["RefractiveIndex"].m_as("RIU"), [1.59] * 3)
