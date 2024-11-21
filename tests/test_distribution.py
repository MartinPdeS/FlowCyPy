import pytest
import numpy as np
from FlowCyPy import distribution as dist
from FlowCyPy.units import nanometer, micrometer, particle
from unittest.mock import patch
import matplotlib.pyplot as plt


# Common test parameters
@pytest.fixture
def n_samples():
    return 1000


@pytest.fixture
def x_values():
    return np.linspace(0.01, 1, 1000) * micrometer


# Parametrize different distributions
distributions = [
    dist.Normal(mean=1.0 * micrometer, std_dev=1.0 * nanometer),
    dist.LogNormal(mean=1.0 * micrometer, std_dev=0.01 * micrometer),
    dist.Uniform(lower_bound=0.5 * micrometer, upper_bound=1.5 * micrometer),
    dist.Delta(position=1 * micrometer),
]


@patch('matplotlib.pyplot.show')
@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__.__name__)
def test_number_of_samples(mock_show, distribution, n_samples, x_values):
    """Test the generate method of the Distribution class."""

    # Generate particle sizes
    sizes = distribution.generate(n_samples * particle)

    print(str(sizes))

    # Assert the shape is correct
    assert sizes.shape == (n_samples,), f"{distribution.__class__.__name__}: Generated size array has incorrect shape."

    # Assert all sizes are positive
    assert np.all(sizes > 0), f"{distribution.__class__.__name__}: Generated sizes should all be positive."

    # Get the PDF and assert it returns values
    x, pdf = distribution.get_pdf(x_values)

    # Assert PDF has the same shape as input x_values
    assert pdf.shape == x_values.shape, f"{distribution.__class__.__name__}: PDF output shape mismatch."

    # Assert PDF values are non-negative
    assert np.all(pdf >= 0), f"{distribution.__class__.__name__}: PDF should return non-negative values."

    # Additional check for DeltaDistribution (which should be a single peak)
    if isinstance(distribution, dist.Delta):
        assert np.sum(pdf > 0) == 1, "DeltaDistribution: PDF should have only one non-zero value."

    distribution.plot()

    plt.close()


def test_uniform_properties(x_values):
    """Test boundary conditions in the PDF generation."""
    distribution = distributions[2]

    x, pdf = distribution.get_pdf(x_values)

    # Check if the PDF at the lower boundary is reasonable
    assert pdf[0] >= 0, f"{distribution.__class__.__name__}: PDF at the lower boundary (x_min) should be non-negative."
    assert pdf[-1] >= 0, f"{distribution.__class__.__name__}: PDF at the upper boundary (x_max) should be non-negative."

    # For UniformDistribution, check if the PDF is zero outside bounds
    if isinstance(distribution, dist.Uniform):
        assert pdf[0] == 0 or pdf[-1] == 0, "UniformDistribution: PDF should be zero at boundaries outside of distribution range."


def test_normal_properties():
    """Test specific properties of certain distributions."""
    distribution = distributions[0]
    sizes = distribution.generate(100 * particle)

    # Test for NormalDistribution: Check that the mean is approximately correct
    mean_size = np.mean(sizes)
    expected_mean = distribution.mean
    assert np.isclose(mean_size, expected_mean, rtol=0.1), f"NormalDistribution: Mean size {mean_size} deviates from expected mean {expected_mean}"


def test_lognormal_properties():
    """Test specific properties of certain distributions."""
    distribution = distributions[1]
    sizes = distribution.generate(4000 * particle)

    # Test for LogNormalDistribution: Check that the standard deviation is approximately correct
    std_dev_size = np.std(sizes)
    expected_std = distribution.std_dev

    assert np.isclose(std_dev_size, expected_std, rtol=2), f"LogNormalDistribution: Standard deviation {std_dev_size} deviates from expected {expected_std}"


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
