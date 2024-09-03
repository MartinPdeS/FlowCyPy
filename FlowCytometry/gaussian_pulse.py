import numpy as np
import matplotlib.pyplot as plt


class GaussianPulse:
    """
    A class to represent a Gaussian pulse used in simulating flow cytometry signals.

    Attributes
    ----------
    center : float
        The center of the Gaussian pulse in time (microseconds).
    height : float
        The peak height (amplitude) of the Gaussian pulse (volts).
    width : float
        The width (standard deviation) of the Gaussian pulse (microseconds).

    Methods
    -------
    generate(time):
        Generates the Gaussian pulse over a given time axis.
    plot(time=None):
        Plots the Gaussian pulse over a given time axis. If no time axis is provided, a default is used.

    Equations
    ---------
    The Gaussian pulse is generated using the equation:

        V(t) = height * exp(-((t - center)^2) / (2 * width^2))

    where:
        - V(t) is the signal amplitude at time t (volts),
        - height is the peak amplitude of the pulse (volts),
        - center is the time at which the pulse is centered (microseconds),
        - width is the standard deviation of the Gaussian function (microseconds).
    """

    def __init__(self, center, height, width):
        """
        Constructs all the necessary attributes for the GaussianPulse object.

        Parameters
        ----------
        center : float
            The center of the Gaussian pulse in time (microseconds).
        height : float
            The peak height (amplitude) of the Gaussian pulse (volts).
        width : float
            The width (standard deviation) of the Gaussian pulse (microseconds).
        """
        self.center = center
        self.height = height
        self.width = width

    def generate(self, time):
        """
        Generates the Gaussian pulse over a given time axis.

        Parameters
        ----------
        time : numpy.ndarray
            A numpy array representing the time axis over which the pulse is generated (microseconds).

        Returns
        -------
        numpy.ndarray
            A numpy array representing the generated Gaussian pulse (volts).
        """
        return self.height * np.exp(-((time - self.center) ** 2) / (2 * self.width ** 2))

    def plot(self, time=None):
        """
        Plots the Gaussian pulse over a given time axis. If no time axis is provided, a default is used.

        Parameters
        ----------
        time : numpy.ndarray, optional
            A numpy array representing the time axis over which the pulse is generated and plotted (microseconds).
            If not provided, a default time axis will be used.
        """
        if time is None:
            time = np.linspace(self.center - 5*self.width, self.center + 5*self.width, 1000)

        pulse = self.generate(time)
        plt.figure(figsize=(8, 4))
        plt.plot(time, pulse, label=f'Center={self.center} μs, Height={self.height} V, Width={self.width} μs')
        plt.title('Gaussian Pulse')
        plt.xlabel('Time (μs)')
        plt.ylabel('Amplitude (V)')
        plt.legend()
        plt.grid(True)
        plt.show()