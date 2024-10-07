import numpy as np
import pytest
from FlowCyPy.utils import find_matching_indices
from FlowCyPy.units import megahertz, degree


def find_matching_indices(array1, array2, margin):
    """
    Finds the indices where the values of two arrays match within a certain margin.

    Parameters:
        array1 (np.ndarray): First array.
        array2 (np.ndarray): Second array.
        margin (float): The margin within which values are considered matching.

    Returns:
        np.ndarray: Array of index pairs (i, j) where array1[i] and array2[j] match within the margin.
    """
    difference_matrix = np.abs(array1[:, np.newaxis] - array2)
    matching_indices = np.argwhere(difference_matrix <= margin)
    return matching_indices

# Test cases using pytest

def test_exact_matches():
    """Test with exact matching values between the two arrays."""
    array1 = np.array([1, 2, 3, 4, 5])
    array2 = np.array([5, 4, 3, 2, 1])
    margin = 0

    expected = np.array([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]])
    result = find_matching_indices(array1, array2, margin)

    np.testing.assert_array_equal(result, expected)

def test_with_margin():
    """Test with values that match within a margin."""
    array1 = np.array([1.0, 2.05, 3.1, 4.2])
    array2 = np.array([1.01, 2.1, 3.05, 4.0])
    margin = 0.1

    expected = np.array([[0, 0], [1, 1], [2, 2]])
    result = find_matching_indices(array1, array2, margin)

    np.testing.assert_array_equal(result, expected)

def test_no_matches():
    """Test with arrays where no values match within the margin."""
    array1 = np.array([1, 2, 3])
    array2 = np.array([10, 20, 30])
    margin = 0.5

    expected = np.array([]).reshape(0, 2)
    result = find_matching_indices(array1, array2, margin)

    np.testing.assert_array_equal(result, expected)

def test_empty_arrays():
    """Test with empty arrays."""
    array1 = np.array([])
    array2 = np.array([])
    margin = 0.1

    expected = np.array([]).reshape(0, 2)
    result = find_matching_indices(array1, array2, margin)

    np.testing.assert_array_equal(result, expected)

if __name__ == '__main__':
    pytest.main([__file__])