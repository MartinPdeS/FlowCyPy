import pytest
import numpy as np
from FlowCyPy.fluidics import FlowCell, ScattererCollection, population, distribution
from FlowCyPy import units

from pint import UnitRegistry
import FlowCyPy
FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging

# Initialize a UnitRegistry
ureg = UnitRegistry()

RUN_TIME = 1e-3 * units.second


# Step 1: Define some global variables and objects to be used across tests
@pytest.fixture
def flow_cell():
    """Fixture to create a FlowCell object for testing."""
    return FlowCell(
        sample_volume_flow=1 * units.microliter / units.second,
        sheath_volume_flow=6 * units.microliter / units.second,
        width=20 * units.micrometer,
        height=10 * units.micrometer,
    )



@pytest.fixture
def populations():
    """Fixture to create a Population object for testing."""
    diameter_dist = distribution.Normal(
        mean=500 * units.nanometer, std_dev=50 * units.nanometer
    )
    refractive_index_dist = distribution.Normal(
        mean=1.4 * units.RIU,
        std_dev=0.01 * units.RIU
    )
    population_0 = population.Sphere(
        particle_count=1.8e11 * units.particle / units.milliliter,
        diameter=diameter_dist,
        refractive_index=refractive_index_dist,
        name="Test Population 0"
    )

    population_1 = population.Sphere(
        particle_count=1.8e11 * units.particle / units.milliliter,
        diameter=diameter_dist,
        refractive_index=refractive_index_dist,
        name="Test Population 1"
    )

    return [population_0, population_1]


@pytest.fixture
def scatterer_collection(populations):
    scatterer_collection = ScattererCollection(
        medium_refractive_index=1.33 * units.RIU,
        populations=populations
    )

    return scatterer_collection

@pytest.fixture
def population_dataframe(flow_cell, populations):
    dataframe = flow_cell._generate_event_dataframe(populations, run_time=RUN_TIME)

    return dataframe

# Test 1: Check if the population is properly initialized
def test_population_initialization(scatterer_collection, population_dataframe):
    """Test if the Population object initializes correctly."""
    scatterer_collection.fill_dataframe_with_sampling(population_dataframe)

    assert len(population_dataframe) > 0, "Number of events should be greater than 0 after initialization"


# Test 2: Check if particle arrival times are generated correctly
def test_particle_arrival_times(flow_cell, population_dataframe):
    """Test if the particle arrival times are generated correctly."""

    assert len(population_dataframe['Time']) > 0, "Particle arrival times should be generated"

    assert np.all(population_dataframe['Time'] <= RUN_TIME), "Arrival times should not exceed total experiment duration"

# Test 4: Check if invalid flow parameters raise errors
def test_invalid_flow_cell():
    """Test if providing invalid flow cell parameters raises an error."""
    with pytest.raises(ValueError):
        invalid_flow_cell = FlowCell(
            volume_flow=0 * units.microliter / units.second,  # Invalid flow speed
            flow_area=(10 * units.micrometer) ** 2,
            run_time=1 * units.second,
        )
        population_0 = population.Sphere(
            size=distribution.Normal(mean=500 * units.nanometer, std_dev=50 * units.nanometer),
            refractive_index=distribution.Normal(mean=1.4, std_dev=0.01),
            name="Invalid Test"
        )
        population_0.initialize(invalid_flow_cell)


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
