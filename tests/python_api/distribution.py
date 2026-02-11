from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pytest
from TypedUnit import ureg, Length

import FlowCyPy
from FlowCyPy.fluidics import distributions as dist

FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging


# ----------------- CONSTANTS -----------------

N_SAMPLES = 1000
X_VALUES = np.linspace(0.01, 1, N_SAMPLES) * ureg.micrometer


# ----------------- DISTRIBUTIONS -----------------

distributions = [
    dist.Normal(mean=1.0 * ureg.micrometer, standard_deviation=1.0 * ureg.nanometer),
    dist.LogNormal(
        mean=1.0 * ureg.micrometer, standard_deviation=0.1 * ureg.micrometer
    ),
    dist.Uniform(lower_bound=0.5 * ureg.micrometer, upper_bound=1.5 * ureg.micrometer),
    dist.Delta(value=1 * ureg.micrometer),
]


# ----------------- TESTS -----------------


@patch("matplotlib.pyplot.show")
@pytest.mark.parametrize(
    "distribution", distributions, ids=lambda x: x.__class__.__name__
)
def test_number_of_samples(mock_show, distribution):
    """Test the generate method of the Distribution class."""

    # Generate particle sizes
    sizes = distribution.sample(N_SAMPLES)

    assert np.all(
        Length.check(sizes)
    ), f"{distribution.__class__.__name__}: Generated sizes have incorrect units."

    # Assert the shape is correct
    assert sizes.shape == (
        N_SAMPLES,
    ), f"{distribution.__class__.__name__}: Generated size array has incorrect shape."

    # Assert all sizes are positive
    assert np.all(
        sizes > 0
    ), f"{distribution.__class__.__name__}: Generated sizes should all be positive."

    plt.close()


def test_uniform_properties():
    """Test boundary conditions in the PDF generation."""
    distribution = distributions[2]


def test_normal_properties():
    """Test specific properties of certain distributions."""
    distribution = distributions[0]
    sizes = distribution.sample(100)

    # Test for NormalDistribution: Check that the mean is approximately correct
    mean_size = np.mean(sizes)
    expected_mean = distribution.mean
    assert np.isclose(
        mean_size, expected_mean, rtol=0.1
    ), f"NormalDistribution: Mean size {mean_size} deviates from expected mean {expected_mean}"


def test_lognormal_properties():
    """Test specific properties of certain distributions."""
    distribution = distributions[1]
    diameters = distribution.sample(4000)

    # Test for LogNormalDistribution: Check that the standard deviation is approximately correct
    standard_deviation_size = np.std(diameters)
    expected_std = distribution.standard_deviation

    assert np.isclose(
        standard_deviation_size, expected_std, rtol=2
    ), f"LogNormalDistribution: Standard deviation {standard_deviation_size} deviates from expected {expected_std}"


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
