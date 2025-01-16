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
