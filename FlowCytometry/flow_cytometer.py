import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from FlowCytometry.gaussian_pulse import GaussianPulse
from MPSPlots.styles import mps

@dataclass
class FlowCytometer:
    """
    A dataclass to simulate the operation of a flow cytometer, generating realistic raw signals
    for Forward Scatter (FSC) and Side Scatter (SSC) channels.

    Attributes
    ----------
    n_events : int
        The number of particle events to simulate.
    time_points : int
        The number of time points over which to simulate the signals.
    noise_level : float
        The level of noise added to the signal (as a fraction of the signal amplitude).
    baseline_shift : float
        The amplitude of the baseline shift added to the signal.
    saturation_level : float
        The maximum signal level before saturation occurs.
    n_bins : int
        The number of bins to discretize the signal into.
    time : numpy.ndarray
        A numpy array representing the time axis for the simulation.
    fsc_raw_signal : numpy.ndarray
        The simulated raw signal for the FSC channel.
    ssc_raw_signal : numpy.ndarray
        The simulated raw signal for the SSC channel.
    """

    n_events: int = 1000
    time_points: int = 1000
    noise_level: float = 0.05
    baseline_shift: float = 0.01
    saturation_level: float = 1e3
    n_bins: int = 100
    time: np.ndarray = field(init=False)
    fsc_raw_signal: np.ndarray = field(init=False)
    ssc_raw_signal: np.ndarray = field(init=False)

    def __post_init__(self):
        """Initializes fields that depend on other fields."""
        self.time = np.linspace(0, 10, self.time_points)
        self.fsc_raw_signal = np.zeros(self.time_points)
        self.ssc_raw_signal = np.zeros(self.time_points)
        np.random.seed(42)

    def simulate_pulse(self):
        """
        Simulates pulses for FSC and SSC channels, including noise, baseline shift, and saturation.
        """
        baseline = self.baseline_shift * np.sin(0.5 * np.pi * self.time)  # Simulate baseline shift

        for _ in range(self.n_events):
            center = np.random.uniform(0, 10)
            fsc_height = np.random.uniform(100, 1000)
            ssc_height = np.random.uniform(50, 500)
            width = np.random.uniform(0.05, 0.2)

            fsc_pulse = GaussianPulse(center, fsc_height, width)
            ssc_pulse = GaussianPulse(center, ssc_height, width)

            self.fsc_raw_signal += fsc_pulse.generate(self.time)
            self.ssc_raw_signal += ssc_pulse.generate(self.time)

        # Add noise and baseline shift
        self.fsc_raw_signal += baseline + self.noise_level * np.random.normal(size=self.time_points)
        self.ssc_raw_signal += baseline + self.noise_level * np.random.normal(size=self.time_points)

        # Apply saturation
        self.fsc_raw_signal = np.clip(self.fsc_raw_signal, 0, self.saturation_level)
        self.ssc_raw_signal = np.clip(self.ssc_raw_signal, 0, self.saturation_level)

        # Discretize the signals into bins
        self.fsc_raw_signal = self._discretize_signal(self.fsc_raw_signal)
        self.ssc_raw_signal = self._discretize_signal(self.ssc_raw_signal)

    def _discretize_signal(self, signal):
        """
        Discretizes the signal into a specified number of bins.

        Parameters
        ----------
        signal : numpy.ndarray
            The continuous signal to be discretized.

        Returns
        -------
        numpy.ndarray
            The discretized signal.
        """
        bins = np.linspace(np.min(signal), np.max(signal), self.n_bins)
        digitized = np.digitize(signal, bins) - 1
        return bins[digitized]

    def plot_signals(self):
        """
        Plots the raw FSC and SSC signals.
        """
        with plt.style.context(mps):
            plt.figure(figsize=(12, 6))

            plt.subplot(2, 1, 1)
            plt.plot(self.time, self.fsc_raw_signal, color='blue')
            plt.title('Simulated Raw FSC Signal with Noise, Baseline Shift, and Saturation')
            plt.xlabel('Time')
            plt.ylabel('FSC Signal Intensity')

            plt.subplot(2, 1, 2)
            plt.plot(self.time, self.ssc_raw_signal, color='green')
            plt.title('Simulated Raw SSC Signal with Noise, Baseline Shift, and Saturation')
            plt.xlabel('Time')
            plt.ylabel('SSC Signal Intensity')

            plt.tight_layout()
            plt.show()

    def plot(self, channel="both"):
        """
        Plots either or both FSC and SSC signals based on the channel parameter.

        Parameters
        ----------
        channel : str, optional
            The channel to plot. Can be "fsc", "ssc", or "both" (default is "both").
        """
        with plt.style.context(mps):
            plt.figure(figsize=(10, 5))

            if channel.lower() == "fsc":
                plt.plot(self.time, self.fsc_raw_signal, color='blue', label='FSC Signal')
                plt.title('Simulated Raw FSC Signal')
                plt.xlabel('Time')
                plt.ylabel('FSC Signal Intensity')
            elif channel.lower() == "ssc":
                plt.plot(self.time, self.ssc_raw_signal, color='green', label='SSC Signal')
                plt.title('Simulated Raw SSC Signal')
                plt.xlabel('Time')
                plt.ylabel('SSC Signal Intensity')
            elif channel.lower() == "both":
                plt.plot(self.time, self.fsc_raw_signal, color='blue', label='FSC Signal')
                plt.plot(self.time, self.ssc_raw_signal, color='green', label='SSC Signal')
                plt.title('Simulated Raw FSC and SSC Signals')
                plt.xlabel('Time')
                plt.ylabel('Signal Intensity')
                plt.legend()

            plt.grid(True)
            plt.show()
