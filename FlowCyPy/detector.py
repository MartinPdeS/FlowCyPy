#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from typing import Optional
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from tabulate import tabulate
from FlowCyPy import ureg

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
    n_bins : int, optional
        The number of bins for signal discretization. Default is 100 bins.

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
    theta_angle: float  # Azimuthal angle (used for the coupling mechanism)
    NA: float
    responsitivity: float  # Electrical response for the optical power
    noise_level: Optional[float] = 0.0  # Noise level (in volts)
    baseline_shift: Optional[float] = 0.0  # Baseline shift (in volts)
    saturation_level: Optional[float] = np.inf  # Saturation level (in volts)
    n_bins: Optional[int] = None  # Number of bins for discretization

    signal: np.ndarray = field(init=False, default=None)
    raw_signal: np.ndarray = field(init=False, default=None)
    time: np.ndarray = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Automatically adds physical units to the attributes after initialization."""
        self._add_units()
        self.pulses = []

    def _add_units(self) -> None:
        """
        Assigns the appropriate physical units to the detector's attributes using the pint library.
        """
        self.acquisition_frequency *= ureg.hertz
        self.responsitivity *= ureg.volt / ureg.watt
        self.noise_level *= ureg.volt
        self.baseline_shift *= ureg.volt
        self.saturation_level *= ureg.volt

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
