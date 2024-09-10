import numpy as np
from typing import List
from FlowCyPy.units import second, volt, Quantity



class ProxyDetector():
    def __init__(self, signal, time):
        self.name = 'proxy'
        self.signal = signal
        self.time = time
        self.dt = time[1] - time[0]

def generate_gaussian_signal(time: np.ndarray, centers: List[float], heights: List[float], stds: List[float]):
    """
    Generate a synthetic signal composed of multiple Gaussian pulses.

    Parameters
    ----------
    time : numpy.ndarray
        A numpy array representing the time axis over which the signal is generated.
    centers : list of floats
        A list of centers (in time) for each Gaussian pulse.
    heights : list of floats
        A list of peak heights (amplitudes) for each Gaussian pulse.
    stds : list of floats
        A list of widths (standard deviations) for each Gaussian pulse.

    Returns
    -------
    numpy.ndarray
        A numpy array representing the generated signal composed of Gaussian pulses.
    """
    time = Quantity(time, second)
    centers = Quantity(centers, second)
    heights = Quantity(heights, volt)
    stds = Quantity(stds, second)

    signal = np.zeros_like(time) * volt

    for center, height, sigma in zip(centers, heights, stds):
        signal += height * np.exp(-((time - center) ** 2) / (2 * sigma ** 2))

    return ProxyDetector(time=time, signal=signal)

def find_matching_indices(array_0: np.ndarray, array_1: np.ndarray, margin: float):
    """
    Finds the indices where the values of two arrays match within a certain margin.

    Parameters:
        array_0 (np.ndarray): First array.
        array_1 (np.ndarray): Second array.
        margin (float): The margin within which values are considered matching.

    Returns:
        np.ndarray: Array of index pairs (i, j) where array_0[i] and array_1[j] match within the margin.
    """
    # Use broadcasting to compute the absolute difference between every value in array_0 and array_1
    difference_matrix = np.abs(array_0[:, np.newaxis] - array_1)

    # Get the indices where the difference is within the margin
    matching_indices = np.argwhere(difference_matrix <= margin)

    return matching_indices