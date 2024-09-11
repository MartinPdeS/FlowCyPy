import pytest
from unittest.mock import patch
import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.scatterer_distribution import ScattererDistribution
from FlowCyPy.distribution import NormalDistribution, LogNormalDistribution, DeltaDistribution, UniformDistribution, WeibullDistribution
from FlowCyPy.flow import FlowCell
from FlowCyPy.units import micrometer, refractive_index_unit, nanometer

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

# Parametrize different distributions
distributions = [
    NormalDistribution(mean=1.0 * micrometer, std_dev=1.0 * nanometer, scale_factor=1.0),
    LogNormalDistribution(mean=1.0 * micrometer, std_dev=0.01 * micrometer, scale_factor=1.0),
    UniformDistribution(lower_bound=0.5 * micrometer, upper_bound=1.5 * micrometer, scale_factor=1.0),
    DeltaDistribution(size_value=1 * micrometer, scale_factor=1.0),
    1 * micrometer
]

@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_generate_distribution_size(distribution, default_flow):
    """Test if the ScattererDistribution generates sizes correctly for each distribution type."""
    # Get the distribution from the fixtures

    # Create the Scatt
    # ererDistribution object with the chosen distribution
    scatterer_distribution = ScattererDistribution(
        flow=default_flow,
        refractive_index=1.5 * refractive_index_unit,
        size=distribution,
    )

    print('scatterer_distribution', scatterer_distribution.size_list)

    # Check that sizes were generated and are positive
    assert scatterer_distribution.size_list.size > 0, "Generated size array is empty."
    assert np.all(scatterer_distribution.size_list.magnitude > 0), "Some generated sizes are not positive."

    # Check if the sizes follow the expected bounds depending on the distribution type
    if isinstance(distribution, NormalDistribution):
        expected_mean = distribution.mean

        generated_mean = np.mean(scatterer_distribution.size_list)

        assert np.isclose(generated_mean, expected_mean, rtol=1e-1), (
            f"Normal distribution: Expected mean {expected_mean}, but got {generated_mean}"
        )

    elif isinstance(distribution, LogNormalDistribution):
        assert np.all(scatterer_distribution.size_list.magnitude > 0), "Lognormal distribution generated non-positive sizes."

    elif isinstance(distribution, UniformDistribution):
        lower_bound = distribution.lower_bound
        upper_bound = distribution.upper_bound

        assert np.all((scatterer_distribution.size_list >= lower_bound) & (scatterer_distribution.size_list <= upper_bound)), (
            f"Uniform distribution: Sizes are out of bounds [{lower_bound}, {upper_bound}]"
        )

    elif isinstance(distribution, DeltaDistribution):
        singular_value = distribution.size_value

        assert np.all(scatterer_distribution.size_list == singular_value), (
            f"Singular distribution: All sizes should be {singular_value}, but got varying sizes."
        )

    scatterer_distribution.get_size_pdf(100)
    scatterer_distribution.get_refractive_index_pdf(100)


@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__)
def test_generate_longitudinal_positions(default_flow, distribution):
    """Test the generation of longitudinal positions based on Poisson process."""
    scatterer_distribution = ScattererDistribution(
        refractive_index=[1.5 * refractive_index_unit],
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
    distribution = distributions[0]

    scatterer_distribution = ScattererDistribution(
        refractive_index=distribution,
        flow=default_flow,
        size=distribution,
    )

    scatterer_distribution.plot()

    plt.close()


if __name__ == '__main__':
    pytest.main([__file__])
