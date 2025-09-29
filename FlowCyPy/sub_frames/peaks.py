from typing import Any, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import MPSPlots
import numpy
import pandas as pd
import seaborn as sns
from TypedUnit import ureg

from FlowCyPy.sub_frames import utils
from FlowCyPy.sub_frames.base import BaseSubFrame


class PeakDataFrame(BaseSubFrame):
    """
    A subclass of pandas DataFrame for handling peak data with custom plotting.
    """

    def plot(self, **kwargs) -> Any:
        """
        Dispatch plotting to 2D or 3D methods based on provided kwargs.
        """
        if "z" in kwargs:
            return self.plot_3d(**kwargs)

        if "y" in kwargs:
            return self.plot_2d(**kwargs)

        return self.hist(**kwargs)

    def standard_deviation(
        self, detector_name: str, metrics: str | slice = slice(None)
    ):
        """
        Calculate the standard deviation of the specified detector's signal.

        Parameters
        ----------
        detector_name : str
            The name of the detector for which to calculate the standard deviation.
        metrics : str or slice, optional
            The metrics to consider for the standard deviation calculation. Defaults to all metrics.

        Returns
        -------
        Any
            The standard deviation of the signal in the specified units.
        """
        sub_frame = self.loc[detector_name, metrics]

        return sub_frame.std()

    def robust_standard_deviation(
        self, detector_name: str, metrics: str | slice = slice(None)
    ):
        """
        Calculate the robust standard deviation of the specified detector's signal.

        Parameters
        ----------
        detector_name : str
            The name of the detector for which to calculate the robust standard deviation.
        metrics : str or slice, optional
            The metrics to consider for the standard deviation calculation. Defaults to all metrics.

        Returns
        -------
        Any
            The robust standard deviation of the signal in the specified units.
        """
        sub_frame = self.loc[detector_name, metrics]

        return numpy.abs(sub_frame - sub_frame.median()).median() * 1.4826

    def mean(self, detector_name: str, metrics: str | slice = slice(None)):
        """
        Calculate the mean of the specified detector's signal.

        Parameters
        ----------
        detector_name : str
            The name of the detector for which to calculate the mean.

        Returns
        -------
        Any
            The mean of the signal in the specified units.
        """
        sub_frame = self.loc[detector_name, metrics]
        return sub_frame.mean(axis=0)

    def get_sub_dataframe(
        self, columns: List[str], rows: List[str]
    ) -> Tuple[pd.DataFrame, List[Any]]:
        """
        Extract sub-dataframe for given rows and columns with Pint unit conversion.

        Parameters
        ----------
        columns : list
            List of column names.
        rows : list
            List of row identifiers.

        Returns
        -------
        tuple
            A tuple with the sub-dataframe and a list of units.
        """
        df = self.loc[rows, columns].copy()
        unit_list = []

        for col_name, col_data in df.items():
            if not hasattr(col_data, "pint"):
                df[col_name] = col_data
                unit_list.append("None")
            else:
                unit = col_data.max().to_compact().units
                if unit.dimensionality == ureg.bit_bins.dimensionality:
                    unit = ureg.bit_bins
                # df.loc[:, col_name] = col_data.pint.to(unit)
                df[col_name] = col_data.pint.to(unit)
                unit_list.append(unit)

        return df, unit_list

    @MPSPlots.helper.post_mpl_plot
    def hist(
        self,
        x: tuple[str, str],
        kde: bool = False,
        bins: Optional[int] = "auto",
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, Any]] = None,
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
        x : tuple[str, str]
            The column name to plot (eg. ('forward', 'Height')).
        kde : bool, optional
            Whether to overlay a KDE curve (default: False).
        bins : Optional[int], optional
            Number of bins for the histogram (default: 'auto', letting Seaborn decide).
        color : Optional[Union[str, dict]], optional
            Color specification for the plot (default: None).
        clip_data : Optional[Union[str, Any]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            values above the corresponding quantile (e.g. the top 20% of values) are excluded.
            If a pint.Quantity is given, values above that absolute value are removed.

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        if len(self) == 1:
            return

        detector_name, feature = x

        figure, ax = plt.subplots(ncols=1, nrows=1)

        ax.set_ylabel(f"{detector_name} : {feature}  [count]")

        kde = False

        data = self.loc[x].sort_index()

        data = utils.clip_data(signal=data, clip_value=clip_data)

        sns.histplot(x=data, ax=ax, kde=kde, bins=bins, color=color)

        return figure

    @MPSPlots.helper.post_mpl_plot
    def plot_2d(
        self, x: tuple[str, str], y: tuple[str, str], bandwidth_adjust: float = 0.8
    ) -> plt.Figure:
        """
        Plot the joint KDE distribution of a feature between two detectors.

        Parameters
        ----------
        x : tuple[str, str]
            Detector for the x-axis.
        y : tuple[str, str]
            Detector for the y-axis.
        bandwidth_adjust : float, optional
            KDE bandwidth adjustment (default: 0.8).

        Returns
        -------
        plt.Figure
            The joint KDE plot figure.
        """
        x_detector, x_feature = x
        y_detector, y_feature = y

        features = tuple(set([x_feature, y_feature]))

        df = self.loc[[x_detector, y_detector], features].sort_index()

        grid = sns.jointplot(
            x=df.loc[x],
            y=df.loc[y],
            kind="kde",
            fill=True,
            cmap="Blues",
            joint_kws={"bw_adjust": bandwidth_adjust, "alpha": 0.7},
        )

        grid.figure.suptitle("Peaks properties")
        grid.ax_joint.scatter(df.loc[x], df.loc[y], color="C1", alpha=0.6)

        grid.set_axis_labels(
            f"Detector: {x_detector} : feature: {x_feature}",
            f"Detector: {y_detector} : feature: {y_feature}",
        )
        return grid.figure

    @MPSPlots.helper.post_mpl_plot
    def plot_3d(self, x: str, y: str, z: str) -> plt.Figure:
        """
        Create a 3D scatter plot of a feature across three detectors.

        Parameters
        ----------
        x : str
            Detector for the x-axis.
        y : str
            Detector for the y-axis.
        z : str
            Detector for the z-axis.
        feature : str, optional
            Feature column (default: 'Height').
        ax : matplotlib.axes._subplots.Axes3DSubplot, optional
            A 3D axis to plot on. If None, a new figure and 3D axis are created.

        Returns
        -------
        plt.Figure
            The 3D scatter plot figure.
        """
        figure = plt.figure()
        ax = figure.add_subplot(111, projection="3d")

        x_detector, x_feature = x
        y_detector, y_feature = y
        z_detector, z_feature = z

        df = self.pint.dequantify().astype(float)
        x_series = df.loc[x].values
        y_series = df.loc[y].values
        z_series = df.loc[z].values

        ax.scatter(x_series, y_series, z_series)

        ax.set_xlabel(f"{x_detector} : {x_feature}", labelpad=20)
        ax.set_ylabel(f"{y_detector} : {y_feature}", labelpad=20)
        ax.set_zlabel(f"{z_detector} : {z_feature}", labelpad=20)

        ax.set_title("Peaks Properties")

        return figure
