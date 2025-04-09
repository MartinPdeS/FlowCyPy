import numpy as np
from typing import List
from FlowCyPy.units import second, Quantity
import pandas as pd
import pint_pandas
from FlowCyPy.peak_locator import BasePeakLocator
from copy import copy
import matplotlib.pyplot as plt
from MPSPlots.styles import mps


class ProxyDetector():
    def __init__(self, signal, time):
        self.name = str(id(self))
        self.signal = signal
        self.time = time
        self.dt = time[1] - time[0]

        self.dataframe = pd.DataFrame(
            data={
                'Signal': pint_pandas.PintArray(self.signal, dtype=self.signal.units),
                'Time': pint_pandas.PintArray(self.time, dtype=self.time.units)
            }
        )

    def set_peak_locator(self, algorithm: BasePeakLocator, compute_peak_area: bool = True) -> None:
        # Ensure the algorithm is an instance of BasePeakLocator
        if not isinstance(algorithm, BasePeakLocator):
            raise TypeError("The algorithm must be an instance of BasePeakLocator.")

        # Ensure the detector has signal data available for analysis
        if not hasattr(self, 'dataframe') or self.dataframe is None:
            raise RuntimeError("The detector does not have signal data available for peak detection.")

        # Set the algorithm and perform peak detection
        self.algorithm = copy(algorithm)
        self.algorithm.init_data(self.dataframe)
        self.algorithm.detect_peaks(compute_area=compute_peak_area)

    def get_properties(self) -> List[List[str]]:
        return [
            ['name', 'proxy']
        ]


def generate_dummy_detector(time: np.ndarray, centers: List[float], heights: List[float], stds: List[float]):
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
    stds = Quantity(stds, second)

    signal = np.zeros_like(time) * heights.units

    for center, height, sigma in zip(centers, heights, stds):
        signal += height * np.exp(-((time - center) ** 2) / (2 * sigma ** 2))

    return ProxyDetector(time=time, signal=signal)

def plot_signal_and_peaks(signal_dataframe: pd.DataFrame, peaks_dataframe: pd.DataFrame) -> None:
    """
    Plots signal data with detected peaks for multiple detectors.

    Parameters
    ----------
    signal_dataframe : pd.DataFrame
        A DataFrame containing signal data with a MultiIndex consisting of 'Detector' and 'SegmentID'.
        It must have the columns ['Time', 'Signal'].

    peaks_dataframe : pd.DataFrame
        A DataFrame containing peak detection data. It must have the columns ['Detector', 'Time'].

    Raises
    ------
    AssertionError
        If required columns are missing in either DataFrame.
    """
    # Validate input DataFrames
    required_signal_cols = {'Time', 'Signal'}
    required_peaks_cols = {'Time'}

    assert required_signal_cols.issubset(signal_dataframe.columns), \
        f"signal_dataframe must contain columns {required_signal_cols}, but has {signal_dataframe.columns}"

    assert required_peaks_cols.issubset(peaks_dataframe.columns), \
        f"peaks_dataframe must contain columns {required_peaks_cols}, but has {peaks_dataframe.columns}"

    detector_names = signal_dataframe.index.get_level_values('Detector').unique()

    with plt.style.context(mps):
        _, axes = plt.subplots(nrows=len(detector_names), ncols=1, figsize=(18, 8), squeeze=False)

    # Create a mapping of detectors to their respective axes
    axes_dict = {name: ax for name, ax in zip(detector_names, axes.flatten())}

    # Plot signal data
    for (detector_name, segment_id), group in signal_dataframe.groupby(['Detector', 'SegmentID']):
        axes_dict[detector_name].plot(group['Time'], group['Signal'])

    # Plot detected peaks
    for detector_name, group in peaks_dataframe.groupby('Detector'):
        ax = axes_dict.get(detector_name)
        if ax:
            ax.vlines(
                group['Time'], ymin=0, ymax=1, transform=ax.get_xaxis_transform(),
                linestyle='--', color='black', label='Detected Peaks'
            )

    # Customize each plot
    for detector_name, ax in axes_dict.items():
        ax.set_ylabel(f'{detector_name}')
        ax.legend()

    plt.xlabel('Time')
    plt.suptitle('Signal and Detected Peaks')
    plt.tight_layout()
    plt.show()
