import numpy as np
import pytest
from TypedUnit import ureg

import FlowCyPy
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    distribution,
    population,
)

FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging

CONCENTRATION = 3e5 * ureg.particle / ureg.milliliter


# Fixtures to set up a default Flow and Distributions
@pytest.fixture
def default_flow_cell():
    """Fixture for creating a default Flow object."""
    return FlowCell(
        sample_volume_flow=10 * ureg.microliter / ureg.second,
        sheath_volume_flow=6 * ureg.microliter / ureg.second,
        width=20 * ureg.micrometer,
        height=10 * ureg.micrometer,
    )


# Parametrize different distributions
distributions = [
    distribution.Normal(
        mean=1.0 * ureg.micrometer, standard_deviation=100.0 * ureg.nanometer
    ),
    distribution.LogNormal(
        mean=1.0 * ureg.micrometer, standard_deviation=0.01 * ureg.micrometer
    ),
    distribution.Uniform(
        lower_bound=0.5 * ureg.micrometer, upper_bound=1.5 * ureg.micrometer
    ),
    distribution.RosinRammler(
        characteristic_property=0.5 * ureg.micrometer, spread=1.5
    ),
]


@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_generate_distribution_size(dist, default_flow_cell):
    """Test if the ScattererCollection generates sizes correctly for each distribution type."""
    # Get the distribution from the fixtures

    ri_distribution = distribution.Normal(
        mean=1.4 * ureg.RIU, standard_deviation=0.01 * ureg.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
    )

    # Create the ScattererCollection Distribution object with the chosen distribution
    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0)

    fluidics = Fluidics(
        scatterer_collection=scatterer_collection, flow_cell=default_flow_cell
    )


@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_generate_longitudinal_positions(default_flow_cell, dist):
    """Test the generation of longitudinal positions based on Poisson process."""
    ri_distribution = distribution.Normal(
        mean=1.4 * ureg.RIU, standard_deviation=0.01 * ureg.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
    )

    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0)


@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_add_population(dist):
    """Test the plotting of longitudinal positions."""
    ri_distribution = distribution.Normal(
        mean=1.4 * ureg.RIU, standard_deviation=0.01 * ureg.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
    )

    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0)


@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_extra(dist):
    """Test the generation of longitudinal positions based on Poisson process."""
    ri_distribution = distribution.Normal(
        mean=1.4 * ureg.RIU, standard_deviation=0.01 * ureg.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
    )

    population_1 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
    )

    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0, population_1)

    scatterer_collection.dilute(factor=2)

    assert np.isclose(
        population_0.particle_count, CONCENTRATION / 2
    ), "Dilution mechanism does not return expected results"

    scatterer_collection.set_concentrations([CONCENTRATION, CONCENTRATION])


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
