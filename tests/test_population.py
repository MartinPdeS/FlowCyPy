import pytest
import numpy as np
from FlowCyPy.distribution import NormalDistribution
from FlowCyPy.population import Population
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.units import (
    nanometer, micrometer, meter, particle, milliliter, second, refractive_index_unit, particle
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
        total_time=1 * second,
    )

@pytest.fixture
def population():
    """Fixture to create a Population object for testing."""
    size_dist = NormalDistribution(
        mean=500 * nanometer, std_dev=50 * nanometer
    )
    refractive_index_dist = NormalDistribution(
        mean=1.4 * refractive_index_unit,
        std_dev=0.01 * refractive_index_unit
    )
    return Population(
        size=size_dist,
        refractive_index=refractive_index_dist,
        concentration=1.8e11 * particle / milliliter,
        name="Test Population"
    )

# Test 1: Check if the population is properly initialized
def test_population_initialization(population, flow_cell):
    """Test if the Population object initializes correctly."""
    population.initialize(flow_cell)

    assert population.n_events > 0 * particle, "Number of events should be greater than 0 after initialization"
    assert len(population.size_list) == population.n_events.magnitude, "Size list should match number of events"
    assert len(population.refractive_index_list) == population.n_events.magnitude, "Refractive index list should match number of events"

# Test 2: Check if particle arrival times are generated correctly
def test_particle_arrival_times(population, flow_cell):
    """Test if the particle arrival times are generated correctly."""
    population.initialize(flow_cell)

    assert len(population.time_positions) > 0, "Particle arrival times should be generated"
    assert population.time_positions[-1] <= flow_cell.total_time, "Arrival times should not exceed total experiment duration"

# Test 3: Check longitudinal positions
def test_longitudinal_positions(population, flow_cell):
    """Test if longitudinal positions are generated correctly."""
    population.initialize(flow_cell)

    population.print_properties()

    longitudinal_positions = population.longitudinal_positions
    assert len(longitudinal_positions) == len(population.time_positions), "Longitudinal positions should match the number of time positions"
    assert np.all(longitudinal_positions >= 0), "All longitudinal positions should be positive"

# Test 4: Check the concentration and particle flux
def test_particle_flux(population, flow_cell):
    """Test if the particle flux is calculated correctly."""
    particle_flux = (population.concentration * flow_cell.flow_speed * flow_cell.flow_area).to(particle / second)

    assert particle_flux.magnitude > 0, "Particle flux should be greater than 0"

# Test 5: Check if invalid flow parameters raise errors
def test_invalid_flow_cell():
    """Test if providing invalid flow cell parameters raises an error."""
    with pytest.raises(ValueError):
        invalid_flow_cell = FlowCell(
            flow_speed=0 * meter / second,  # Invalid flow speed
            flow_area=(10 * micrometer) ** 2,
            total_time=1 * second,
        )
        population = Population(
            size=NormalDistribution(mean=500 * nanometer, std_dev=50 * nanometer),
            refractive_index=NormalDistribution(mean=1.4, std_dev=0.01),
            concentration=1.8e9 * particle / milliliter,
            name="Invalid Test"
        )
        population.initialize(invalid_flow_cell)


if __name__ == '__main__':
    pytest.main([__file__])