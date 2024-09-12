import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Tuple

class JointPlotWithMarginals:
    """
    A class to create a joint plot with multiple datasets, KDE, and scatter plots, along with marginal KDE plots.

    Attributes:
        datasets (List[Tuple[np.ndarray, np.ndarray, str]]): List of datasets in the form (x, y, label).
        figure (sns.JointGrid): The JointGrid object for creating the joint plot.
    """

    def __init__(self, xlabel: str = "X-axis", ylabel: str = "Y-axis", figure_size: Tuple[float, int] = (7, 7)):
        """
        Initializes the JointPlotWithMarginals class.

        Args:
            xlabel (str, optional): Label for the x-axis. Defaults to "X-axis".
            ylabel (str, optional): Label for the y-axis. Defaults to "Y-axis".
            figure_size (Tuple[float, int], optional): Figure size with height and ratio. Defaults to (6, 2).
        """
        self.datasets = []
        self.figure = None
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.figure_size = figure_size

    def add_dataset(
            self,
            x: np.ndarray,
            y: np.ndarray,
            label: str = '',
            alpha: float = 0.3,
            color: Optional[str] = None) -> None:
        """
        Adds a dataset to the joint plot, with KDE and scatter plots.

        Args:
            x (np.ndarray): Data for the x-axis.
            y (np.ndarray): Data for the y-axis.
            label (str): Label for the dataset.
            alpha (float, optional): Transparency level for the plots. Defaults to 0.3.
            color (str, optional): Color for the dataset. If None, a color will be chosen automatically.

        Raises:
            ValueError: If x and y do not have matching lengths.
        """
        if len(x) != len(y):
            raise ValueError(f"Dataset '{label}' has mismatched x and y lengths.")

        # Add the dataset to the list of datasets
        self.datasets.append([x, y, label, alpha, color])

        # Initialize the JointGrid if it's the first dataset
        if self.figure is None:
            height, ratio = self.figure_size
            self.figure = sns.JointGrid(x=x, y=y, height=height, ratio=ratio)

        # Initialize the JointGrid if it's the first dataset
        if self.figure is None:
            self.figure = sns.JointGrid(x=x, y=y)

        # Use default color if none is provided
        if color is None:
            color = sns.color_palette("husl", len(self.datasets))[len(self.datasets) - 1]

            self.datasets[-1][-1] = color

        # Add KDE and scatter plots
        self._add_kde_plot(x, y, color, label, alpha)
        self._add_scatter_plot(x, y, color, label, alpha)

    def _add_kde_plot(self, data_x: np.ndarray, data_y: np.ndarray, color: str, label: str = '', alpha: float = 0.9) -> None:
        """
        Adds a KDE plot to the joint plot and marginals.

        Args:
            data_x (np.ndarray): Data for the x-axis.
            data_y (np.ndarray): Data for the y-axis.
            color (str): Color for the marginal KDE plots.
            label (str): Label for the dataset.
            alpha (float): Transparency level for the plots.
        """
        # Joint KDE plot
        sns.kdeplot(x=data_x, y=data_y, fill=True, ax=self.figure.ax_joint, color=color, alpha=alpha, label=label)

        # Marginal KDE plots
        sns.kdeplot(data_x, ax=self.figure.ax_marg_x, color=color, fill=True, alpha=alpha)
        sns.kdeplot(y=data_y, ax=self.figure.ax_marg_y, color=color, fill=True, alpha=alpha)

    def _add_scatter_plot(self, data_x: np.ndarray, data_y: np.ndarray, color: str, label: str = '', alpha: float = 0.9, size: int = 20) -> None:
        """
        Adds a scatter plot to the joint plot.

        Args:
            data_x (np.ndarray): Data for the x-axis.
            data_y (np.ndarray): Data for the y-axis.
            color (str): Color of the scatter points.
            label (str): Label for the scatter plot.
            alpha (float): Transparency level for the scatter plot.
            size (int, optional): Size of the scatter points. Defaults to 20.
        """
        sns.scatterplot(x=data_x, y=data_y, color=color, ax=self.figure.ax_joint, label=label, s=size, alpha=alpha)

    def add_legend(self) -> None:
        """
        Adds a legend to the joint plot.
        """
        handles = [
            plt.Line2D([0], [0], color=color, lw=4, label=label)
            for _, _, label, _, color in self.datasets
        ]
        self.figure.ax_joint.legend(handles=handles, loc='upper right')

    def show_plot(self) -> None:
        """
        Displays the final plot.
        """
        if self.figure is None:
            raise RuntimeError("No datasets have been added. Add at least one dataset before calling show_plot().")

        self.figure.ax_joint.set_xlabel(self.xlabel)
        self.figure.ax_joint.set_ylabel(self.ylabel)
        self.add_legend()
        plt.tight_layout()
        plt.show()
