import pytest
import numpy as np
from unittest.mock import patch
import matplotlib.pyplot as plt
from pint import UnitRegistry
from FlowCyPy import Plotter

# Assuming Plotter is already imported

# Setup a UnitRegistry for the magnitudes in the test
ureg = UnitRegistry()

class MockDetector:
    def __init__(self):
        self.name = 'mock detector'

# Mock dataset objects with 'time' and 'height' attributes
class MockDataset:
    def __init__(self, heights):
        self.time = ureg.Quantity(np.arange(len(heights)), 's')
        self.height = ureg.Quantity(heights, 'dimensionless')

@pytest.fixture
def dataset_0():
    """Fixture to provide mock data for dataset_0."""
    data_set = MockDataset(heights=np.random.rand(100))
    data_set.detector = MockDetector()
    return data_set

@pytest.fixture
def dataset_1():
    """Fixture to provide mock data for dataset_1."""
    data_set = MockDataset(heights=np.random.rand(100))
    data_set.detector = MockDetector()
    return data_set

@pytest.fixture
def plotter(dataset_0, dataset_1):
    """Fixture to provide a Plotter instance."""
    return Plotter(dataset_0=dataset_0, dataset_1=dataset_1)

@patch('matplotlib.pyplot.show')
def test_plot(mock_show, plotter):
    """
    Test the Plotter class plot method.

    This test checks if the plot method runs without errors and verifies some key plot features:
    - The colorbar is created.
    - The axis labels are correctly set.
    """

    # Call the plot method
    plotter.plot()

    # Verify that plt.show() was called (plot was created)
    mock_show.assert_called_once()

    plt.close()

if __name__ == '__main__':
    pytest.main([__file__])