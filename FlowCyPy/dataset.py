import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from dataclasses import dataclass


@dataclass
class DataSet:
    """
    A dataclass to store features extracted from signal peaks.

    Attributes:
    ----------
    height : np.ndarray
        Array of peak heights.
    width : np.ndarray
        Array of peak widths.
    area : np.ndarray
        Array of areas under each peak.
    time : np.ndarray
        Array of times at which peaks occur.
    """
    height: np.ndarray = None
    width: np.ndarray = None
    area: np.ndarray = None
    time: np.ndarray = None

    def _add_to_ax(self, ax: plt.Axes, t_time: np.ndarray, signal: np.ndarray) -> None:
        """
        Add the peak information to a matplotlib axis.

        Parameters:
        ----------
        ax : plt.Axes
            The matplotlib axis where the plot will be added.
        t_time : np.ndarray
            Time axis for the signal.
        signal : np.ndarray
            Signal values to plot.
        """
        # Create a 2D mask where each row corresponds to a peak time and width.
        start_times = self.time - self.width / 2
        end_times = self.time + self.width / 2

        # Create a mask for the regions to fill between (use broadcasting for vectorized comparison)
        where = (t_time[:, None] >= start_times) & (t_time[:, None] <= end_times)

        # Collapse the mask into a single array to find where any of the conditions are true (combine all peaks)
        where_combined = np.any(where, axis=1)

        # Fill the regions under the signal where the mask is True
        ax.fill_between(
            x=t_time.magnitude,
            y1=0,
            y2=signal.magnitude,
            where=where_combined,
            color='red',
            alpha=0.3,
            label='Width at Half-Max'
        )

    def print_properties(self) -> None:
        """
        Displays extracted peak features in a tabular format.
        Handles the case where 'self.area' might be None.
        """
        headers = ["Peak", "Time [s]", "Height", "Width", "Area"]
        table = []

        # If area is None, fill the 'area' column with 'Not calculated'
        if self.area is None:
            for idx, (time, height, width) in enumerate(zip(self.time, self.height, self.width)):
                table.append([
                    idx + 1,  # Peak number
                    f"{time:.2f~#P}",  # Time in scientific notation
                    f"{height:.2f~#P}",  # Height in scientific notation
                    f"{width:.2f~#P}",  # Width in scientific notation
                    "Not calculated"  # Area (if not available)
                ])
        else:
            # Iterate over time, height, width, and area if area is available
            for idx, (time, height, width, area) in enumerate(zip(self.time, self.height, self.width, self.area)):
                table.append([
                    idx + 1,  # Peak number
                    f"{time:.2f~#P}",  # Time in scientific notation
                    f"{height:.2f~#P}",  # Height in scientific notation
                    f"{width:.2f~#P}",  # Width in scientific notation
                    f"{area:.2f~#P}"  # Area (if available)
                ])

        # Print the table using tabulate
        print(tabulate(table, headers=headers, tablefmt="grid"))
