import numpy as np
from dataclasses import dataclass, field

@dataclass
class Peak:
    """
    A dataclass to represent and manage the properties of a detected peak.

    Attributes
    ----------
    time : float
        The time at which the peak occurs.
    height : float
        The height (amplitude) of the peak.
    width : float
        The width of the peak at half maximum.
    area : float
        The area under the peak, calculated post-initialization.
    """

    time: float
    height: float
    width: float
    area: float = field(init=False, default=None)

    def calculate_area(self, signal, time):
        """
        Calculates the area under the peak based on the signal and time axis.

        Parameters
        ----------
        signal : numpy.ndarray
            The signal from which to calculate the area.
        time : numpy.ndarray
            The time axis corresponding to the signal.
        """
        dt = time[1] - time[0]
        start_idx = int((self.time - self.width/2) / dt)
        end_idx = int((self.time + self.width/2) / dt)
        self.area = np.trapz(signal[start_idx:end_idx], time[start_idx:end_idx])
