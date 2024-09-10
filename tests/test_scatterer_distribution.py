import pytest
from unittest.mock import patch
import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.scatterer_distribution import ScattererDistribution
from FlowCyPy.distribution import NormalDistribution, LogNormalDistribution, DeltaDistribution, UniformDistribution, WeibullDistribution
from FlowCyPy.flow import FlowCell

# Fixtures to set up a default Flow and Distributions
@pytest.fixture
def default_flow():
    """Fixture for creating a default Flow object."""
    return FlowCell(
        flow_speed=80e-6,
        flow_area=1e-6,
        total_time=1.0,
        scatterer_density=1e12
    )


distributions = [
    NormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0),
    LogNormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0),
    DeltaDistribution(size_value=1e-6, scale_factor=1.0),
    UniformDistribution(lower_bound=5e-7, upper_bound=1.5e-6, scale_factor=1.0),
    WeibullDistribution(scale=1.0, shape=1.5),
    1e-6
]

@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_generate_distribution_size(distribution, default_flow):
    """Test if the ScattererDistribution generates sizes correctly for each distribution type."""
    # Get the distribution from the fixtures

    # Create the Scatt
    # ererDistribution object with the chosen distribution
    scatterer_distribution = ScattererDistribution(
        flow=default_flow,
        refractive_index=1.5,
        size=distribution,
    )

    # Check that sizes were generated and are positive
    assert scatterer_distribution.size_list.size > 0, "Generated size array is empty."
    assert np.all(scatterer_distribution.size_list.magnitude > 0), "Some generated sizes are not positive."

    # Check if the sizes follow the expected bounds depending on the distribution type
    if isinstance(distribution, NormalDistribution):
        expected_mean = distribution.mean
        generated_mean = np.mean(scatterer_distribution.size_list.magnitude)
        assert np.isclose(generated_mean, expected_mean, atol=1e-7), (
            f"Normal distribution: Expected mean {expected_mean}, but got {generated_mean}"
        )

    elif isinstance(distribution, LogNormalDistribution):
        assert np.all(scatterer_distribution.size_list.magnitude > 0), "Lognormal distribution generated non-positive sizes."

    elif isinstance(distribution, UniformDistribution):
        lower_bound = distribution.lower_bound
        upper_bound = distribution.upper_bound
        assert np.all((scatterer_distribution.size_list.magnitude >= lower_bound) & (scatterer_distribution.size_list.magnitude <= upper_bound)), (
            f"Uniform distribution: Sizes are out of bounds [{lower_bound}, {upper_bound}]"
        )

    elif isinstance(distribution, DeltaDistribution):
        singular_value = distribution.size_value
        assert np.all(scatterer_distribution.size_list.magnitude == singular_value), (
            f"Singular distribution: All sizes should be {singular_value}, but got varying sizes."
        )

    scatterer_distribution.get_size_pdf(100)
    scatterer_distribution.get_refractive_index_pdf(100)


@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_generate_longitudinal_positions(default_flow, distribution):
    """Test the generation of longitudinal positions based on Poisson process."""
    scatterer_distribution = ScattererDistribution(
        refractive_index=[1.5],
        flow=default_flow,
        size=distribution,
    )

    # Assert correct shape of generated longitudinal positions
    assert scatterer_distribution.flow.longitudinal_positions.size > 0, "Generated longitudinal positions array has incorrect shape."

    # Assert that longitudinal positions are increasing (since they are cumulative)
    assert np.all(np.diff(scatterer_distribution.flow.longitudinal_positions.magnitude) >= 0), "Longitudinal positions are not monotonically increasing."

    # Assert that no positions are negative
    assert np.all(scatterer_distribution.flow.longitudinal_positions.magnitude >= 0), "Some longitudinal positions are negative."


@patch('matplotlib.pyplot.show')
@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_plot_positions(mock_show, default_flow, distribution):
    """Test the plotting of longitudinal positions."""
    scatterer_distribution = ScattererDistribution(
        refractive_index=[NormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0)],
        flow=default_flow,
        size=distribution,
    )

    scatterer_distribution.plot()

    plt.close()


if __name__ == '__main__':
    pytest.main([__file__])
