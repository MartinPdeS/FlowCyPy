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

RUN_TIME = 1e-3 * ureg.second


# Step 1: Define some global variables and objects to be used across tests
@pytest.fixture
def flow_cell():
    """Fixture to create a FlowCell object for testing."""
    return FlowCell(
        sample_volume_flow=1 * ureg.microliter / ureg.second,
        sheath_volume_flow=6 * ureg.microliter / ureg.second,
        width=20 * ureg.micrometer,
        height=10 * ureg.micrometer,
    )


@pytest.fixture
def populations():
    """Fixture to create a Population object for testing."""
    diameter_dist = distribution.Normal(
        mean=500 * ureg.nanometer, standard_deviation=50 * ureg.nanometer
    )
    refractive_index_dist = distribution.Normal(
        mean=1.4 * ureg.RIU, standard_deviation=0.01 * ureg.RIU
    )
    population_0 = population.Sphere(
        particle_count=1.8e11 * ureg.particle / ureg.milliliter,
        diameter=diameter_dist,
        refractive_index=refractive_index_dist,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Test Population 0",
    )

    population_1 = population.Sphere(
        particle_count=1.8e11 * ureg.particle / ureg.milliliter,
        diameter=diameter_dist,
        refractive_index=refractive_index_dist,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Test Population 1",
    )

    return [population_0, population_1]


@pytest.fixture
def scatterer_collection(populations):
    scatterer_collection = ScattererCollection(populations=populations)

    return scatterer_collection


# Test 4: Check if invalid flow parameters raise errors
def test_invalid_flow_cell():
    """Test if providing invalid flow cell parameters raises an error."""
    with pytest.raises(ValueError):
        invalid_flow_cell = FlowCell(
            volume_flow=0 * ureg.microliter / ureg.second,  # Invalid flow speed
            flow_area=(10 * ureg.micrometer) ** 2,
            run_time=1 * ureg.second,
        )
        population_0 = population.Sphere(
            size=distribution.Normal(
                mean=500 * ureg.nanometer, standard_deviation=50 * ureg.nanometer
            ),
            medium_refractive_index=1.33 * ureg.RIU,
            refractive_index=distribution.Normal(mean=1.4, standard_deviation=0.01),
            name="Invalid Test",
        )
        population_0.initialize(invalid_flow_cell)


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
