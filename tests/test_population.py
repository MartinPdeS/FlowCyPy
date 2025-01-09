import pytest
import pandas as pd
import numpy as np
from FlowCyPy import distribution
from FlowCyPy.population import Population
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.units import (
    nanometer, micrometer, milliliter, second, RIU, particle, meter
)
from pint import UnitRegistry

# Initialize a UnitRegistry
ureg = UnitRegistry()

RUN_TIME = 100e-3 * second


# Step 1: Define some global variables and objects to be used across tests
@pytest.fixture
def flow_cell():
    """Fixture to create a FlowCell object for testing."""
    return FlowCell(
        flow_speed=5 * micrometer / second,
        flow_area=(10 * micrometer) ** 2,
    )


@pytest.fixture
def populations():
    """Fixture to create a Population object for testing."""
    size_dist = distribution.Normal(
        mean=500 * nanometer, std_dev=50 * nanometer
    )
    refractive_index_dist = distribution.Normal(
        mean=1.4 * RIU,
        std_dev=0.01 * RIU
    )
    population_0 = Population(
        particle_count=1.8e11 * particle / milliliter,
        size=size_dist,
        refractive_index=refractive_index_dist,
        name="Test Population 0"
    )

    population_1 = Population(
        particle_count=1.8e11 * particle / milliliter,
        size=size_dist,
        refractive_index=refractive_index_dist,
        name="Test Population 1"
    )

    return [population_0, population_1]


@pytest.fixture
def scatterer_collection(populations):
    scatterer_collection = ScattererCollection(
        medium_refractive_index=1.33 * RIU,
        populations=populations
    )

    return scatterer_collection

@pytest.fixture
def population_dataframe(flow_cell, populations):
    dataframe = flow_cell.generate_event_dataframe(populations, run_time=RUN_TIME)

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
