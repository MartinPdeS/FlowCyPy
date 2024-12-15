import pytest
from unittest.mock import patch
import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.scatterer import Scatterer
from FlowCyPy import distribution as dist
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.population import Population
from FlowCyPy.units import (
    micrometer, meter, refractive_index_unit, nanometer, milliliter, particle, millisecond, second
)


CONCENTRATION = 3e+5 * particle / milliliter


# Fixtures to set up a default Flow and Distributions
@pytest.fixture
def default_flow_cell():
    """Fixture for creating a default Flow object."""
    return FlowCell(
        flow_speed=80e-3 * meter / second,
        flow_area=1e-6 * meter ** 2,
        run_time=1.0 * millisecond,
    )


# Parametrize different distributions
distributions = [
    dist.Normal(mean=1.0 * micrometer, std_dev=1.0 * nanometer),
    dist.LogNormal(mean=1.0 * micrometer, std_dev=0.01 * micrometer),
    dist.Uniform(lower_bound=0.5 * micrometer, upper_bound=1.5 * micrometer),
    dist.RosinRammler(characteristic_size=0.5 * micrometer, spread=1.5),
]


@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_generate_distribution_size(distribution, default_flow_cell):
    """Test if the Scatterer generates sizes correctly for each distribution type."""
    # Get the distribution from the fixtures

    ri_distribution = dist.Normal(
        mean=1.4 * refractive_index_unit,
        std_dev=0.01 * refractive_index_unit
    )

    population_0 = Population(
        size=distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

    # Create the Scatterer Distribution object with the chosen distribution
    scatterer = Scatterer()

    scatterer.add_population(population_0, particle_count=CONCENTRATION)

    scatterer.initialize(flow_cell=default_flow_cell)

    # Check that sizes were generated and are positive
    assert len(scatterer.dataframe) > 0, "Generated size array is empty."
    assert np.all(scatterer.dataframe['Size'] > 0), "Some generated sizes are not positive."

    # Check if the sizes follow the expected bounds depending on the distribution type
    if isinstance(distribution, dist.Normal):
        expected_mean = distribution.mean

        generated_mean = scatterer.dataframe['Size'].mean()

        assert np.isclose(generated_mean, expected_mean, rtol=1e-1), (
            f"Normal distribution: Expected mean {expected_mean}, but got {generated_mean}"
        )

    elif isinstance(distribution, dist.LogNormal):
        assert np.all(scatterer.dataframe['Size'] > 0 * meter), "Lognormal distribution generated non-positive sizes."

    elif isinstance(distribution, dist.Uniform):
        lower_bound = distribution.lower_bound
        upper_bound = distribution.upper_bound

        assert np.all((scatterer.dataframe['Size'] >= lower_bound) & (scatterer.dataframe['Size'] <= upper_bound)), (
            f"Uniform distribution: Sizes are out of bounds [{lower_bound}, {upper_bound}]"
        )

    elif isinstance(distribution, dist.Delta):
        singular_value = distribution.size_value

        assert np.all(scatterer.dataframe['Size'] == singular_value), (
            f"Singular distribution: All sizes should be {singular_value}, but got varying sizes."
        )


@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_generate_longitudinal_positions(default_flow_cell, distribution):
    """Test the generation of longitudinal positions based on Poisson process."""
    ri_distribution = dist.Normal(
        mean=1.4 * refractive_index_unit,
        std_dev=0.01 * refractive_index_unit
    )

    population_0 = Population(
        size=distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

    scatterer = Scatterer()

    scatterer.add_population(population_0, particle_count=CONCENTRATION)

    scatterer.initialize(flow_cell=default_flow_cell)

    # Assert correct shape of generated longitudinal positions
    for population in scatterer.populations:
        assert population.dataframe['Position'].size > 0, "Generated longitudinal positions array has incorrect shape."

    # Assert that longitudinal positions are increasing (since they are cumulative)
    for population in scatterer.populations:
        print(population.dataframe['Position'])
        assert np.all(np.diff(population.dataframe['Position']) >= 0 * meter), "Longitudinal positions are not monotonically increasing."

    # Assert that no positions are negative
    for population in scatterer.populations:
        assert np.all(population.dataframe['Position'] >= 0 * meter), "Some longitudinal positions are negative."


@patch('matplotlib.pyplot.show')
@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_plot_positions(mock_show, default_flow_cell, distribution):
    """Test the plotting of longitudinal positions."""
    ri_distribution = dist.Normal(
        mean=1.4 * refractive_index_unit,
        std_dev=0.01 * refractive_index_unit
    )

    population_0 = Population(
        size=distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

    scatterer = Scatterer()

    scatterer.add_population(population_0, particle_count=CONCENTRATION)

    scatterer.initialize(flow_cell=default_flow_cell)

    scatterer.plot()

    plt.close()


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
