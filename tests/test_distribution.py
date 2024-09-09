import pytest
import numpy as np
from FlowCyPy.distribution import NormalDistribution, LogNormalDistribution, DeltaDistribution, UniformDistribution, WeibullDistribution
from FlowCyPy import ureg

# Common test parameters
@pytest.fixture
def n_samples():
    return 1000

@pytest.fixture
def x_values():
    return np.linspace(1e-8, 1e-6, 1000)

# Parametrize different distributions
distributions = [
    NormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0),
    LogNormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0),
    DeltaDistribution(size_value=1e-6, scale_factor=1.0),
    UniformDistribution(lower_bound=5e-7, upper_bound=1.5e-6, scale_factor=1.0),
    WeibullDistribution(scale=1.0, shape=1.5)
]

@pytest.mark.parametrize("distribution", distributions, ids=lambda x: x.__class__.__name__)
def test_number_of_samples(distribution, n_samples, x_values):
    """Test the generate method of the Distribution class."""

    # Generate particle sizes
    sizes = distribution.generate(n_samples * ureg.particle)

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
    if isinstance(distribution, DeltaDistribution):
        assert np.sum(pdf > 0) == 1, "DeltaDistribution: PDF should have only one non-zero value."


def test_uniform_properties():
    """Test boundary conditions in the PDF generation."""
    x_values = np.linspace(1e-8, 1e-6, 1000)
    distribution = UniformDistribution(lower_bound=5e-7, upper_bound=1.5e-6, scale_factor=1.0)
    x_min, x_max = x_values.min(), x_values.max()

    x, pdf = distribution.get_pdf(x_values)

    # Check if the PDF at the lower boundary is reasonable
    assert pdf[0] >= 0, f"{distribution.__class__.__name__}: PDF at the lower boundary (x_min) should be non-negative."
    assert pdf[-1] >= 0, f"{distribution.__class__.__name__}: PDF at the upper boundary (x_max) should be non-negative."

    # For UniformDistribution, check if the PDF is zero outside bounds
    if isinstance(distribution, UniformDistribution):
        assert pdf[0] == 0 or pdf[-1] == 0, "UniformDistribution: PDF should be zero at boundaries outside of distribution range."


def test_normal_properties():
    """Test specific properties of certain distributions."""
    distribution = NormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0)
    sizes = distribution.generate(100 * ureg.particle)

    # Test for NormalDistribution: Check that the mean is approximately correct
    mean_size = np.mean(sizes)
    expected_mean = distribution.mean
    assert np.isclose(mean_size.magnitude, expected_mean, rtol=0.1), f"NormalDistribution: Mean size {mean_size} deviates from expected mean {expected_mean}"

def test_lognormal_properties():
    """Test specific properties of certain distributions."""
    distribution = LogNormalDistribution(mean=1e-6, std_dev=1e-7, scale_factor=1.0)
    sizes = distribution.generate(400 * ureg.particle)

    # Test for LogNormalDistribution: Check that the standard deviation is approximately correct
    std_dev_size = np.std(sizes)
    expected_std = distribution.std_dev

    assert np.isclose(std_dev_size.magnitude, expected_std, rtol=0.2), f"LogNormalDistribution: Standard deviation {std_dev_size} deviates from expected {expected_std}"



if __name__ == "__main__":
    pytest.main([__file__])
