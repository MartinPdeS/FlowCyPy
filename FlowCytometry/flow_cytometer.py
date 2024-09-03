import numpy as np
import matplotlib.pyplot as plt
from FlowCytometry.gaussian_pulse import GaussianPulse

class FlowCytometer:
    """
    A class to simulate the operation of a flow cytometer, generating realistic raw signals
    for Forward Scatter (FSC) and Side Scatter (SSC) channels.

    Attributes
    ----------
    n_events : int
        The number of particle events to simulate.
    time_points : int
        The number of time points over which to simulate the signals.
    time : numpy.ndarray
        A numpy array representing the time axis for the simulation.
    fsc_raw_signal : numpy.ndarray
        The simulated raw signal for the FSC channel.
    ssc_raw_signal : numpy.ndarray
        The simulated raw signal for the SSC channel.
    noise_level : float
        The level of noise added to the signal (as a fraction of the signal amplitude).
    baseline_shift : float
        The amplitude of the baseline shift added to the signal.
    saturation_level : float
        The maximum signal level before saturation occurs.

    Methods
    -------
    simulate_pulse():
        Simulates pulses for FSC and SSC channels, including noise, baseline shift, and saturation.
    plot_signals():
        Plots the raw FSC and SSC signals.

    Equations
    ---------
    The baseline shift is modeled as a sinusoidal function:

        baseline(t) = baseline_shift * sin(ω * t)

    where:
        - baseline_shift is the amplitude of the baseline shift,
        - ω is the angular frequency (set to 0.5π for this simulation),
        - t is the time.

    Noise is added to the signal as Gaussian noise:

        noise = noise_level * N(0, 1)

    where N(0, 1) is a normal distribution with mean 0 and standard deviation 1.

    Signal saturation is applied by clipping the signal:

        signal(t) = min(max(signal(t), 0), saturation_level)

    where saturation_level is the maximum allowable signal amplitude.
    """

    def __init__(self, n_events=1000, time_points=1000, noise_level=0.05, baseline_shift=0.01, saturation_level=1e3):
        """
        Constructs all the necessary attributes for the FlowCytometer object.

        Parameters
        ----------
        n_events : int, optional
            The number of particle events to simulate (default is 1000).
        time_points : int, optional
            The number of time points over which to simulate the signals (default is 1000).
        noise_level : float, optional
            The level of noise added to the signal as a fraction of the signal amplitude (default is 0.05).
        baseline_shift : float, optional
            The amplitude of the baseline shift added to the signal (default is 0.01).
        saturation_level : float, optional
            The maximum signal level before saturation occurs (default is 1000).
        """
        self.n_events = n_events
        self.time_points = time_points
        self.time = np.linspace(0, 10, time_points)
        self.fsc_raw_signal = np.zeros(time_points)
        self.ssc_raw_signal = np.zeros(time_points)
        self.noise_level = noise_level
        self.baseline_shift = baseline_shift
        self.saturation_level = saturation_level
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

    def plot_signals(self):
        """
        Plots the raw FSC and SSC signals.
        """
        plt.figure(figsize=(12, 6))

        plt.subplot(2, 1, 1)
        plt.plot(self.time, self.fsc_raw_signal, color='blue')
        plt.title('Simulated Raw FSC Signal with Noise, Baseline Shift, and Saturation')
        plt.xlabel('Time (arbitrary units)')
        plt.ylabel('FSC Signal Intensity')

        plt.subplot(2, 1, 2)
        plt.plot(self.time, self.ssc_raw_signal, color='green')
        plt.title('Simulated Raw SSC Signal with Noise, Baseline Shift, and Saturation')
        plt.xlabel('Time (arbitrary units)')
        plt.ylabel('SSC Signal Intensity')

        plt.tight_layout()
        plt.show()