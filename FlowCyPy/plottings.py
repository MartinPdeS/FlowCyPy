from typing import Optional, Union, Tuple
from MPSPlots.styles import mps
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


class MetricPlotter:
    """
    A class for creating 2D density and scatter plots of scattering intensities from two detectors.

    Parameters
    ----------
    coincidence_dataframe : pd.DataFrame
        The dataframe containing the coincidence data, including detector and feature columns.
    detector_names : tuple of str
        A tuple containing the names of the two detectors (detector 0 and detector 1).
    """

    def __init__(self, coincidence_dataframe: pd.DataFrame, detector_names: Tuple[str, str]):
        self.coincidence_dataframe = coincidence_dataframe.reset_index()
        self.detector_names = detector_names

    def _extract_feature_data(self, feature: str):
        """
        Extracts and processes the feature data for the two detectors.

        Parameters
        ----------
        feature : str
            The feature to extract.

        Returns
        -------
        Tuple[pd.Series, pd.Series, str, str]
            Processed x_data, y_data, x_units, and y_units.
        """
        name_0, name_1 = self.detector_names
        x_data = self.coincidence_dataframe[(name_0, feature)]
        y_data = self.coincidence_dataframe[(name_1, feature)]

        x_units = x_data.max().to_compact().units
        y_units = y_data.max().to_compact().units

        x_data = x_data.pint.to(x_units)
        y_data = y_data.pint.to(y_units)

        return x_data, y_data, x_units, y_units

    def _create_density_plot(
        self,
        x_data: pd.Series,
        y_data: pd.Series,
        bandwidth_adjust: float,
    ):
        """
        Creates a KDE density plot.

        Parameters
        ----------
        x_data : pd.Series
            The x-axis data.
        y_data : pd.Series
            The y-axis data.
        bandwidth_adjust : float
            Adjustment factor for the KDE bandwidth.

        Returns
        -------
        sns.JointGrid
            The seaborn JointGrid object.
        """
        return sns.jointplot(
            data=self.coincidence_dataframe,
            x=x_data,
            y=y_data,
            kind="kde",
            alpha=0.8,
            fill=True,
            joint_kws={"alpha": 0.7, "bw_adjust": bandwidth_adjust},
        )

    def _add_scatterplot(
        self,
        g: sns.JointGrid,
        x_data: pd.Series,
        y_data: pd.Series,
        color_palette: Optional[Union[str, dict]],
    ):
        """
        Adds a scatterplot layer to the KDE density plot.

        Parameters
        ----------
        g : sns.JointGrid
            The seaborn JointGrid object to which the scatterplot is added.
        x_data : pd.Series
            The x-axis data.
        y_data : pd.Series
            The y-axis data.
        color_palette : str or dict, optional
            The color palette to use for the hue in the scatterplot.

        Returns
        -------
        None
        """
        sns.scatterplot(
            data=self.coincidence_dataframe,
            x=x_data,
            y=y_data,
            hue="Label",
            palette=color_palette,
            ax=g.ax_joint,
            alpha=0.6,
            zorder=1,
        )

    def _apply_axis_labels(
        self,
        g: sns.JointGrid,
        feature: str,
        x_units: str,
        y_units: str,
    ):
        """
        Sets the x and y labels with units on the plot.

        Parameters
        ----------
        g : sns.JointGrid
            The seaborn JointGrid object.
        feature : str
            The feature being plotted.
        x_units : str
            Units of the x-axis data.
        y_units : str
            Units of the y-axis data.

        Returns
        -------
        None
        """
        name_0, name_1 = self.detector_names
        g.ax_joint.set_xlabel(f"{feature} : {name_0} [{x_units:P}]")
        g.ax_joint.set_ylabel(f"{feature}: {name_1} [{y_units:P}]")

    def _apply_axis_limits(
        self,
        g: sns.JointGrid,
        x_limits: Optional[Tuple],
        y_limits: Optional[Tuple],
        x_units: str,
        y_units: str):
        """
        Sets the axis limits if specified.

        Parameters
        ----------
        g : sns.JointGrid
            The seaborn JointGrid object.
        x_limits : tuple, optional
            The x-axis limits (min, max), by default None.
        y_limits : tuple, optional
            The y-axis limits (min, max), by default None.
        x_units : str
            Units of the x-axis data.
        y_units : str
            Units of the y-axis data.

        Returns
        -------
        None
        """
        if x_limits:
            x0, x1 = x_limits
            x0 = x0.to(x_units).magnitude
            x1 = x1.to(x_units).magnitude
            g.ax_joint.set_xlim(x0, x1)

        if y_limits:
            y0, y1 = y_limits
            y0 = y0.to(y_units).magnitude
            y1 = y1.to(y_units).magnitude
            g.ax_joint.set_ylim(y0, y1)

    def plot(
        self,
        feature: str,
        show: bool = True,
        log_plot: bool = True,
        x_limits: Optional[Tuple] = None,
        y_limits: Optional[Tuple] = None,
        equal_axes: bool = False,
        bandwidth_adjust: float = 1.0,
        color_palette: Optional[Union[str, dict]] = 'tab10') -> None:
        """
        Generates a 2D density plot of the scattering intensities, overlaid with individual peak heights.

        Parameters
        ----------
        feature : str
            The feature to plot (e.g., 'intensity').
        show : bool, optional
            Whether to display the plot immediately, by default True.
        log_plot : bool, optional
            Whether to use logarithmic scaling for the plot axes, by default True.
        x_limits : tuple, optional
            The x-axis limits (min, max), by default None.
        y_limits : tuple, optional
            The y-axis limits (min, max), by default None.
        equal_axes : bool, optional
            Whether to enforce the same range for the x and y axes, by default False.
        bandwidth_adjust : float, optional
            Bandwidth adjustment factor for the kernel density estimate of the marginal distributions. Default is 1.0.
        color_palette : str or dict, optional
            The color palette to use for the hue in the scatterplot.

        Returns
        -------
        None
        """
        x_data, y_data, x_units, y_units = self._extract_feature_data(feature)

        # Determine equal axis limits if required
        if equal_axes:
            min_x = x_limits[0].to(x_units).magnitude if x_limits else x_data.min()
            max_x = x_limits[1].to(x_units).magnitude if x_limits else x_data.max()
            min_y = y_limits[0].to(y_units).magnitude if y_limits else y_data.min()
            max_y = y_limits[1].to(y_units).magnitude if y_limits else y_data.max()

            # Set common limits
            min_val = min(min_x, min_y)
            max_val = max(max_x, max_y)
            x_limits = (min_val, max_val)
            y_limits = (min_val, max_val)

        with plt.style.context(mps):
            if not log_plot:
                # KDE + Scatterplot for linear plots
                g = self._create_density_plot(x_data, y_data, bandwidth_adjust)
                self._add_scatterplot(g, x_data, y_data, color_palette)
                self._apply_axis_labels(g, feature, x_units, y_units)
                self._apply_axis_limits(g, x_limits, y_limits, x_units, y_units)
            else:
                # Scatterplot only for log-scaled plots
                fig, ax = plt.subplots()
                sns.scatterplot(
                    x=x_data,
                    y=y_data,
                    hue=self.coincidence_dataframe["Label"],
                    palette=color_palette,
                    alpha=0.6,
                    ax=ax,
                )
                ax.set_xscale("log")
                ax.set_yscale("log")
                ax.set_xlabel(f"{feature} : {self.detector_names[0]} [{x_units:P}]")
                ax.set_ylabel(f"{feature} : {self.detector_names[1]} [{y_units:P}]")
                if x_limits:
                    ax.set_xlim([lim.to(x_units).magnitude for lim in x_limits])
                if y_limits:
                    ax.set_ylim([lim.to(y_units).magnitude for lim in y_limits])
                ax.legend()

            plt.tight_layout()
            if show:
                plt.show()

