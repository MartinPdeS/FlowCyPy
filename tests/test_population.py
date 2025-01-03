import pytest
import numpy as np
from FlowCyPy import distribution
from FlowCyPy.population import Population
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.particle_count import ParticleCount
from FlowCyPy.units import (
    nanometer, micrometer, meter, milliliter, second, RIU, particle
)
from pint import UnitRegistry

# Initialize a UnitRegistry
ureg = UnitRegistry()


# Step 1: Define some global variables and objects to be used across tests
@pytest.fixture
def flow_cell():
    """Fixture to create a FlowCell object for testing."""
    return FlowCell(
        flow_speed=5 * micrometer / second,
        flow_area=(10 * micrometer) ** 2,
        run_time=1 * second,
    )


@pytest.fixture
def population(flow_cell):
    """Fixture to create a Population object for testing."""
    size_dist = distribution.Normal(
        mean=500 * nanometer, std_dev=50 * nanometer
    )
    refractive_index_dist = distribution.Normal(
        mean=1.4 * RIU,
        std_dev=0.01 * RIU
    )
    population = Population(
        particle_count=1.8e11 * particle / milliliter,
        size=size_dist,
        refractive_index=refractive_index_dist,
        name="Test Population"
    )

    scatterer_collection = ScattererCollection(
        medium_refractive_index=1.33 * RIU,
        populations=[population]
    )

    flow_cell.initialize(scatterer_collection=scatterer_collection)

    return population


# Test 1: Check if the population is properly initialized
def test_population_initialization(population, flow_cell):
    """Test if the Population object initializes correctly."""
    assert population.n_events > 0 * particle, "Number of events should be greater than 0 after initialization"
    assert len(population.dataframe) == population.n_events.magnitude, "Size list should match number of events"


# Test 2: Check if particle arrival times are generated correctly
def test_particle_arrival_times(population, flow_cell):
    """Test if the particle arrival times are generated correctly."""
    assert len(population.dataframe['Time']) > 0, "Particle arrival times should be generated"
    # print(population.dataframe['Time'])
    # print(flow_cell.run_time)
    assert np.all(population.dataframe['Time'] <= flow_cell.run_time), "Arrival times should not exceed total experiment duration"


# Test 3: Check longitudinal positions
def test_longitudinal_positions(population, flow_cell):
    """Test if longitudinal positions are generated correctly."""
    population.print_properties()

    assert len(population.dataframe['Position']) == len(population.dataframe['Time']), "Longitudinal positions should match the number of time positions"
    assert np.all(population.dataframe['Position'] >= 0 * meter), "All longitudinal positions should be positive"


# Test 4: Check if invalid flow parameters raise errors
def test_invalid_flow_cell():
    """Test if providing invalid flow cell parameters raises an error."""
    with pytest.raises(ValueError):
        invalid_flow_cell = FlowCell(
            flow_speed=0 * meter / second,  # Invalid flow speed
            flow_area=(10 * micrometer) ** 2,
            run_time=1 * second,
        )
        population = Population(
            size=distribution.Normal(mean=500 * nanometer, std_dev=50 * nanometer),
            refractive_index=distribution.Normal(mean=1.4, std_dev=0.01),
            name="Invalid Test"
        )
        population.initialize(invalid_flow_cell)


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
