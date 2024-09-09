from dataclasses import dataclass
from typing import Optional
import seaborn as sns
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from MPSPlots.styles import mps
from FlowCyPy.dataset import DataSet

@dataclass
class Plotter:
    """
    A class to plot a 2D density plot of scattering intensities detected by two detectors.

    This class takes two detectors' scattering intensities and plots a 2D hexbin density plot,
    with a horizontal colorbar and custom axis labels positioned on the top and right.

    Attributes
    ----------
    dataset_0 : object
        Scattering data from detector 0, expected to have 'time' and 'height' attributes.
    dataset_1 : object
        Scattering data from detector 1, expected to have 'time' and 'height' attributes.
    gridsize : Optional[int], optional
        The number of hexagonal bins for the 2D histogram (default is None).
    bins : Optional[int], optional
        Number of bins for the marginal histograms (default is 30).
    """

    dataset_0: DataSet  # Data from detector 0
    dataset_1: DataSet  # Data from detector 1
    gridsize: Optional[int] = None  # Default gridsize for hexbin
    bins: Optional[int] = 30  # Default number of bins for marginal histograms

    def plot(self) -> None:
        """
        Plots the 2D density plot of the scattering intensities from the two detectors.

        The plot includes:
        - A 2D hexbin density plot.
        - X-axis label positioned on top and y-axis label positioned on the right.
        - A horizontal colorbar at the bottom indicating the density.
        """
        # Set seaborn style for better aesthetics

        with plt.style.context(mps):

            # Create the 2D density plot
            joint_plot = sns.jointplot(
                x=self.dataset_0.height.magnitude,
                y=self.dataset_1.height.magnitude,
                kind='kde',
                color='steelblue',
                cmap='Blues',
                fill=True,
                marginal_kws=dict(fill=True, warn_singular=False),
            )


            joint_plot.plot_joint(sns.scatterplot, color='blue', alpha=0.5)

            joint_plot.figure.set_size_inches((10, 8))

            # Set axis labels for the plot
            joint_plot.set_axis_labels(
                f'Detector [{self.dataset_0.detector.name}] Scattering Intensity',
                f'Detector [{self.dataset_1.detector.name}] Scattering Intensity'
            )

            # Add a title above the plot
            joint_plot.figure.suptitle('2D Density Plot of Scattering Intensities', fontsize=14)

            if len(joint_plot.ax_joint.collections) == 2:
                # Create a divider for the axis to place the colorbar at the bottom
                divider = make_axes_locatable(joint_plot.ax_joint)
                cax = divider.append_axes("bottom", size="5%", pad=0.5)

                # Add a horizontal colorbar at the bottom
                plt.colorbar(
                    joint_plot.ax_joint.collections[0],
                    cax=cax,
                    orientation="horizontal",
                    label='Density'
                )

            plt.tight_layout()

            # Display the plot
            plt.show()
