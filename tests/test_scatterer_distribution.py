import pytest
from unittest.mock import patch
import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.fluidics import FlowCell, ScattererCollection, population, distribution
from FlowCyPy import units
import FlowCyPy
FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging

CONCENTRATION = 3e+5 * units.particle / units.milliliter


# Fixtures to set up a default Flow and Distributions
@pytest.fixture
def default_flow_cell():
    """Fixture for creating a default Flow object."""
    return FlowCell(
        sample_volume_flow=10 * units.microliter / units.second,
        sheath_volume_flow=6 * units.microliter / units.second,
        width=20 * units.micrometer,
        height=10 * units.micrometer,
    )


# Parametrize different distributions
distributions = [
    distribution.Normal(mean=1.0 * units.micrometer, std_dev=100.0 * units.nanometer),
    distribution.LogNormal(mean=1.0 * units.micrometer, std_dev=0.01 * units.micrometer),
    distribution.Uniform(lower_bound=0.5 * units.micrometer, upper_bound=1.5 * units.micrometer),
    distribution.RosinRammler(characteristic_property=0.5 * units.micrometer, spread=1.5),
]


@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_generate_distribution_size(dist, default_flow_cell):
    """Test if the ScattererCollection generates sizes correctly for each distribution type."""
    # Get the distribution from the fixtures

    ri_distribution = distribution.Normal(
        mean=1.4 * units.RIU,
        std_dev=0.01 * units.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        name="Default population"
    )

    # Create the ScattererCollection Distribution object with the chosen distribution
    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0)

    dataframe = default_flow_cell._generate_event_dataframe(
        scatterer_collection.populations,
        run_time=100e-4 * units.second
    )

    # # Check that sizes were generated and are positive
    assert len(dataframe) > 0, "Generated size array is empty."

    scatterer_collection.fill_dataframe_with_sampling(dataframe)

    assert np.all(dataframe['Diameter'] > 0), "Some generated sizes are not positive."

    # Check if the sizes follow the expected bounds depending on the distribution type
    if isinstance(dist, distribution.Normal):
        expected_mean = dist.mean

        generated_mean = dataframe['Diameter'].mean()

        assert np.isclose(generated_mean, expected_mean, rtol=1e-1), (
            f"Normal distribution: Expected mean {expected_mean}, but got {generated_mean}"
        )

    elif isinstance(dist, distribution.LogNormal):
        assert np.all(dataframe['Diameter'] > 0 * units.meter), "Lognormal distribution generated non-positive sizes."

    elif isinstance(dist, distribution.Uniform):
        lower_bound = dist.lower_bound
        upper_bound = dist.upper_bound

        assert np.all((dataframe['Diameter'] >= lower_bound) & (dataframe['Diameter'] <= upper_bound)), (
            f"Uniform distribution: Diameters are out of bounds [{lower_bound}, {upper_bound}]"
        )

    elif isinstance(dist, distribution.Delta):
        singular_value = dist.size_value

        assert np.all(dataframe['Diameter'] == singular_value), (
            f"Singular distribution: All sizes should be {singular_value}, but got varying sizes."
        )


@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_generate_longitudinal_positions(default_flow_cell, dist):
    """Test the generation of longitudinal positions based on Poisson process."""
    ri_distribution = distribution.Normal(
        mean=1.4 * units.RIU,
        std_dev=0.01 * units.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        name="Default population"
    )

    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0)

    dataframe = default_flow_cell._generate_event_dataframe(
        scatterer_collection.populations,
        run_time=100e-4 * units.second
    )

    # Assert correct shape of generated longitudinal positions
    for _, group in dataframe.groupby('Population'):
        assert group['Time'].size > 0, "Generated longitudinal positions array has incorrect shape."

    # Assert that longitudinal positions are increasing (since they are cumulative)
    for _, group in dataframe.groupby('Population'):
        assert np.all(np.diff(group['Time']) >= 0 * units.second), "Longitudinal positions are not monotonically increasing."

    # Assert that no positions are negative
    for _, group in dataframe.groupby('Population'):
        assert np.all(group['Time'] >= 0 * units.second), "Some longitudinal positions are negative."


@patch('matplotlib.pyplot.show')
@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_plot_positions(mock_show, dist):
    """Test the plotting of longitudinal positions."""
    ri_distribution = distribution.Normal(
        mean=1.4 * units.RIU,
        std_dev=0.01 * units.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        name="Default population"
    )

    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0)

    scatterer_collection.get_population_dataframe()

    plt.close()

@pytest.mark.parametrize("dist", distributions, ids=lambda x: x.__class__)
def test_extra(dist):
    """Test the generation of longitudinal positions based on Poisson process."""
    ri_distribution = distribution.Normal(
        mean=1.4 * units.RIU,
        std_dev=0.01 * units.RIU
    )

    population_0 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        name="Default population"
    )

    population_1 = population.Sphere(
        particle_count=CONCENTRATION,
        diameter=dist,
        refractive_index=ri_distribution,
        name="Default population"
    )

    scatterer_collection = ScattererCollection()

    scatterer_collection.add_population(population_0, population_1)

    scatterer_collection.dilute(factor=2)

    assert np.isclose(population_0.particle_count.value, CONCENTRATION / 2), "Dilution mechanism does not return expected results"

    scatterer_collection.set_concentrations([CONCENTRATION, CONCENTRATION])


if __name__ == '__main__':
    pytest.main(["-W error", __file__])