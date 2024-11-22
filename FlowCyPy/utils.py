import numpy as np
from typing import List, Dict
from FlowCyPy.units import second, volt, Quantity
import pandas as pd
import pint_pandas
from tabulate import tabulate
from dataclasses import dataclass
from FlowCyPy.peak_locator import BasePeakLocator
from copy import copy
from FlowCyPy.helper import plot_helper
import matplotlib.pyplot as plt


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

    @plot_helper
    def plot(self, color: str = 'C0', ax: plt.Axes = None, time_unit: str | Quantity = None, signal_unit: str | Quantity = None, add_peak_locator: bool = False) -> None:
        """
        Visualizes the processed signal as a function of time.

        This method generates a plot of the processed signal data over time,
        allowing customization of appearance and axis scaling.

        Parameters
        ----------
        show : bool, optional
            Whether to display the plot immediately. Default is True.
        figure_size : tuple, optional
            Size of the plot in inches as (width, height). Default is None, which uses the default Matplotlib settings.
        color : str, optional
            Color of the signal line in the plot. Default is 'C0' (Matplotlib's default color cycle).
        ax : matplotlib.axes.Axes, optional
            Pre-existing Matplotlib Axes to plot on. If None, a new figure and axes will be created.
        time_unit : str or Quantity, optional
            Unit to use for the time axis. If None, it defaults to the unit of the maximum time value in the data.
        signal_unit : str or Quantity, optional
            Unit to use for the signal axis. If None, it defaults to the unit of the maximum signal value in the data.

        Returns
        -------
        None
            Displays the plot if `show` is True. The function also updates the data's time and signal columns to the specified units.

        Notes
        -----
            - The method automatically converts the data's `Time` and `Signal` columns to the specified units,
            ensuring consistency between the data and plot axes.
            - If `show` is False, the plot will not be displayed but can be retrieved through the provided `ax`.
        """
        signal_unit = signal_unit or self.dataframe.Signal.max().to_compact().units
        time_unit = time_unit or self.dataframe.Time.max().to_compact().units

        y = self.dataframe['Signal'].pint.to(signal_unit)
        x = self.dataframe['Time'].pint.to(time_unit)

        ax.plot(x, y, color=color, label='Signal')

        if add_peak_locator:
            self.algorithm._add_to_ax(ax=ax, signal_unit=signal_unit, time_unit=time_unit)

        ax.set_xlabel(f"Time [{time_unit:P}]")
        ax.set_ylabel(f"{self.name} [{signal_unit:P}]")

        return time_unit, signal_unit


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
    heights = Quantity(heights, volt)
    stds = Quantity(stds, second)

    signal = np.zeros_like(time) * volt

    for center, height, sigma in zip(centers, heights, stds):
        signal += height * np.exp(-((time - center) ** 2) / (2 * sigma ** 2))

    return ProxyDetector(time=time, signal=signal)


def find_matching_indices(array_0: np.ndarray, array_1: np.ndarray, margin: float):
    """
    Finds the indices where the values of two arrays match within a certain margin.

    Parameters
    ----------
        array_0 (np.ndarray): First array.
        array_1 (np.ndarray): Second array.
        margin (float): The margin within which values are considered matching.

    Returns
    -------
    np.ndarray
        Array of index pairs (i, j) where array_0[i] and array_1[j] match within the margin.
    """
    # Use broadcasting to compute the absolute difference between every value in array_0 and array_1
    difference_matrix = np.abs(array_0[:, np.newaxis] - array_1)

    # Get the indices where the difference is within the margin
    matching_indices = np.argwhere(difference_matrix <= margin)

    return matching_indices


def array_to_compact(array: np.ndarray):
    compact_unit = array.mean().to_compact().units
    return array.to(compact_unit)


@dataclass(slots=True)
class PropertiesReport:
    def print_properties(self, **properties_dict: Dict[str, Quantity]) -> None:
        """
        Prints the detector's properties in a tabular format.

        This method formats the properties into a grid and prints them for easy visualization.
        """
        properties = self.get_properties(**properties_dict)

        print(f"\n{self.__class__.__name__} [{self.name if hasattr(self, 'name') else ''}] Properties")
        print(tabulate(properties, headers=["Property", "Value"], tablefmt="grid"))

    def add_to_report(self) -> List:
        """
        Returns the detector's key properties as a list for inclusion in reports.

        The list is formatted similarly to `get_properties`, providing a summary of the detector's characteristics.
        """
        return self.get_properties()

    def get_properties(self, **properties_dict: Dict[str, Quantity]) -> List[List[str]]:
        """
        Returns a list of key properties of the detector.

        The list contains formatted strings representing the detector's physical and operational characteristics.
        """
        properties_dict = {
            k: f"{v.to_compact():.1f~P}" if isinstance(v, Quantity) else v for k, v in properties_dict.items()
        }

        return list(properties_dict.items())
