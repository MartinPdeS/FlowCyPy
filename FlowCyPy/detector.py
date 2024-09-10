#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from typing import Optional, Union
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from tabulate import tabulate
from FlowCyPy import ureg
from FlowCyPy.units import Quantity, hertz, volt, watt, degree

@dataclass
class Detector:
    """
    Represents the properties and functionality of a detector in a flow cytometer. The detector
    captures, processes, and discretizes the signal, while adding noise and handling baseline
    shifts and signal saturation.

    Attributes
    ----------
    name : str
        The name or identifier of the detector.
    acquisition_frequency : float
        The frequency at which the signal is sampled, in Hertz.
    responsitivity: float
        Responsitivity of the detector.
    noise_level : float, optional
        The level of noise added to the signal, in volts. Default is 0.05 volts.
    baseline_shift : float, optional
        The baseline shift applied to the signal, in volts. Default is 0.01 volts.
    saturation_level : float, optional
        The maximum signal level before saturation occurs, in volts. Default is 1000 volts.
    n_bins : int or str, optional
        The number of bins for signal discretization or a string (e.g., '12bit') to compute bins based on bit depth.

    Methods
    -------
    capture_signal(time: np.ndarray, raw_signal: np.ndarray) -> None
        Captures and processes the raw signal by adding noise, applying baseline shifts, and saturating the signal.
    print_properties() -> None
        Prints the key properties of the detector in a tabular format.
    _add_to_ax(ax: plt.Axes, color: str = 'C0') -> None
        Adds the processed signal to a matplotlib Axes for plotting.
    """
    name: str
    acquisition_frequency: float  # Acquisition frequency in Hertz
    phi_angle: float  # Azimuthal angle (used for the coupling mechanism)
    NA: float

    gamma_angle: float = 0  # Longitudinal angle (used for the coupling mechanism)
    sampling: int = 100  # Number of points that define the detector in the far-field regime
    responsitivity: Optional[float] = 1  # Electrical response for the optical power
    noise_level: Optional[float] = 0.0  # Noise level (in volts)
    baseline_shift: Optional[float] = 0.0  # Baseline shift (in volts)
    saturation_level: Optional[float] = np.inf  # Saturation level (in volts)
    n_bins: Optional[Union[int, str]] = '12bit'  # Number of bins for discretization or bit-depth string

    signal: np.ndarray = field(init=False, default=None)
    raw_signal: np.ndarray = field(init=False, default=None)
    time: np.ndarray = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Automatically adds physical units to the attributes after initialization."""
        self._process_n_bins()
        self._add_units()
        self.pulses = []

    def _add_units(self) -> None:
        """
        Assigns the appropriate physical units to the detector's attributes using the pint library.
        """
        self.acquisition_frequency = Quantity(self.acquisition_frequency, hertz)
        self.responsitivity = Quantity(self.responsitivity, volt / watt)
        self.noise_level = Quantity(self.noise_level, volt)
        self.baseline_shift = Quantity(self.baseline_shift, volt)
        self.saturation_level = Quantity(self.saturation_level, volt)
        self.phi_angle = Quantity(self.phi_angle, degree)
        self.gamma_angle = Quantity(self.gamma_angle, degree)

    def _process_n_bins(self) -> None:
        """Processes the n_bins value, converting a bit-depth string to the corresponding number of bins."""
        if isinstance(self.n_bins, str):
            try:
                bit_depth = int(self.n_bins.rstrip('bit'))
                self.n_bins = 2 ** bit_depth
            except (ValueError, TypeError):
                raise ValueError(f"Invalid n_bins value: '{self.n_bins}'. Expected an integer or a string like '12bit'.")
        elif not isinstance(self.n_bins, int) or self.n_bins is None:
            self.n_bins = 100  # Default value

    def print_properties(self) -> None:
        """
        Prints the key properties of the detector in a tabular format using the `tabulate` library.
        """
        properties = [
            ["Acquisition Frequency", f"{self.acquisition_frequency:.2f~#P}"],
            ["Noise Level", f"{self.noise_level:.2f~#P}"],
            ["Baseline Shift Amplitude", f"{self.baseline_shift:.2f~#P}"],
            ["Saturation Level", f"{self.saturation_level:.2f~#P}"],
            ["Number of Discretization Bins", self.n_bins],
        ]

        print(f"\nDetector [{self.name}] Properties")
        print(tabulate(properties, headers=["Property", "Value"], tablefmt="grid"))

    def add_pulse_to_raw_signal(self, pulse) -> None:
        self.raw_signal += pulse.generate(self.time)
        self.pulses.append(pulse)

    def capture_signal(self) -> None:
        """
        Captures and processes the raw signal by adding noise, applying baseline shifts, and saturating the signal.

        Parameters
        ----------
        time : np.ndarray
            The time axis of the signal.
        raw_signal : np.ndarray
            The raw signal before processing.
        """
        self.signal = self.raw_signal.copy()

        # Add baseline shift
        baseline = self.baseline_shift * np.sin(0.5 * np.pi * self.time.magnitude)

        # Add noise
        noise = self.noise_level * np.random.normal(size=len(self.time))

        self.signal += noise + baseline

        # Apply saturation
        self.signal = np.clip(self.signal, 0, self.saturation_level)

        if self.n_bins is not None:
            # Discretize the signal into bins
            bins = np.linspace(np.min(self.signal), np.max(self.signal), self.n_bins)
            digitized = np.digitize(self.signal.magnitude, bins.magnitude) - 1
            self.signal = bins[digitized]

    def init_raw_signal(self, total_time: float) -> None:
        time_points = int((self.acquisition_frequency * total_time))

        self.time = np.linspace(0, total_time, time_points)
        self.dt = self.time[1] - self.time[0]
        self.raw_signal = np.zeros(time_points) * ureg.volt

    def _add_to_ax(self, ax: plt.Axes, color: str = 'C0') -> None:
        """
        Adds the processed signal to a matplotlib Axes for plotting.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib Axes object where the signal will be plotted.
        color : str, optional
            The color of the plot (default is 'C0').
        """
        ax.plot(
            self.time.magnitude,
            self.signal.magnitude,
            color=color,
            label=f'{self.name} Signal'
        )

        for pulse in self.pulses:
            pulse._add_to_ax(ax=ax)

        ax.set(
            title=f'Detector: {self.name}',
            xlabel='Time [seconds]',
            ylabel='Signal [V]'
        )

        ax.legend()
