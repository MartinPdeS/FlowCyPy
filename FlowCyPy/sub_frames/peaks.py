from typing import Any, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
from MPSPlots import helper
import numpy
import pandas as pd
import seaborn as sns
from TypedUnit import ureg

from FlowCyPy.sub_frames import utils
from MPSPlots.styles import scientific


class PeakDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame for handling peak data with custom plotting.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of PeakDataFrame."""
        return self.__class__

    def __init__(self, dataframe: pd.DataFrame):
        super().__init__(dataframe)

    @classmethod
    def _construct_from_dict(
        cls,
        peak_dictionary: dict[int, dict[str, dict[str, list[float]]]],
    ) -> "PeakDataFrame":
        """
        Construct a PeakDataFrame from the nested dictionary returned by the C++
        peak locator.

        The expected input structure is

            {
                segment_id: {
                    channel_name: {
                        "Index":  [...],
                        "Height": [...],
                        "Width":  [...],   # optional
                        "Area":   [...],   # optional
                    },
                    ...
                },
                ...
            }

        The resulting dataframe uses a three level row MultiIndex:

            ("Detector", "SegmentID", "PeakID")

        and stores the peak metrics in the dataframe columns.

        Parameters
        ----------
        peak_dictionary : dict[int, dict[str, dict[str, list[float]]]]
            Nested dictionary of peak metrics indexed by segment id, then channel
            name, then metric name.

        Returns
        -------
        PeakDataFrame
            Peak dataframe with MultiIndex rows and metric columns.

        Raises
        ------
        TypeError
            If the nested structure is malformed.
        ValueError
            If metric vectors of a given channel do not all have the same length.
        """
        if peak_dictionary is None:
            raise TypeError("peak_dictionary must not be None.")

        if not isinstance(peak_dictionary, dict):
            raise TypeError(
                f"peak_dictionary must be a dict, received {type(peak_dictionary).__name__!r}."
            )

        preferred_metric_order = ["Index", "Height", "Width", "Area"]

        row_tuples: list[tuple[str, int, int]] = []
        row_records: list[dict[str, float]] = []
        discovered_metric_names: list[str] = []

        for segment_id, segment_dictionary in peak_dictionary.items():
            if not isinstance(segment_dictionary, dict):
                raise TypeError(
                    f"Each segment entry must be a dict. Segment {segment_id!r} "
                    f"contains {type(segment_dictionary).__name__!r}."
                )

            for channel_name, metric_dictionary in segment_dictionary.items():
                if not isinstance(metric_dictionary, dict):
                    raise TypeError(
                        f"Each channel entry must be a dict. Segment {segment_id!r}, "
                        f"channel {channel_name!r} contains "
                        f"{type(metric_dictionary).__name__!r}."
                    )

                if len(metric_dictionary) == 0:
                    continue

                metric_lengths = {}
                for metric_name, metric_values in metric_dictionary.items():
                    if not isinstance(metric_values, (list, tuple, numpy.ndarray)):
                        raise TypeError(
                            f"Metric {metric_name!r} for segment {segment_id!r}, "
                            f"channel {channel_name!r} must be array-like."
                        )

                    metric_lengths[metric_name] = len(metric_values)

                    if metric_name not in discovered_metric_names:
                        discovered_metric_names.append(metric_name)

                unique_lengths = set(metric_lengths.values())
                if len(unique_lengths) != 1:
                    raise ValueError(
                        f"All metric vectors must have the same length for "
                        f"segment {segment_id!r}, channel {channel_name!r}. "
                        f"Received lengths: {metric_lengths}."
                    )

                peak_count = unique_lengths.pop()

                for peak_id in range(peak_count):
                    row_tuples.append(
                        (str(channel_name), int(segment_id), int(peak_id))
                    )

                    row_records.append(
                        {
                            metric_name: float(metric_values[peak_id])
                            for metric_name, metric_values in metric_dictionary.items()
                        }
                    )

        ordered_metric_names = [
            metric_name
            for metric_name in preferred_metric_order
            if metric_name in discovered_metric_names
        ] + [
            metric_name
            for metric_name in discovered_metric_names
            if metric_name not in preferred_metric_order
        ]

        if len(row_tuples) == 0:
            empty_index = pd.MultiIndex.from_tuples(
                [],
                names=["Detector", "SegmentID", "PeakID"],
            )
            empty_dataframe = pd.DataFrame(
                columns=ordered_metric_names, index=empty_index
            )
            return cls(empty_dataframe)

        multi_index = pd.MultiIndex.from_tuples(
            row_tuples,
            names=["Detector", "SegmentID", "PeakID"],
        )

        dataframe = pd.DataFrame(row_records, index=multi_index)

        if ordered_metric_names:
            dataframe = dataframe.reindex(columns=ordered_metric_names)

        dataframe = dataframe.sort_index()

        return cls(dataframe)

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

    @helper.post_mpl_plot
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

    def plot_2d(
        self,
        x: tuple[str, str],
        y: tuple[str, str],
        plot_type: str = "scatter",
        bandwidth_adjust: float = 0.8,
        xscale: str = "linear",
        yscale: str = "linear",
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        color_scale: str = "linear",
        figure: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        figsize: tuple[float, float] = (9, 8),
        show_marginals: bool = False,
        show_colorbar: bool = True,
        show_scatter: bool = False,
        fill: bool = False,
        scatter_alpha: float = 0.5,
        scatter_size: float = 20,
        kde_alpha: float = 0.7,
        hexbin_grid_size: int = 30,
        hexbin_min_count: int = 1,
        hexbin_reduce_function=None,
        cmap: str = "Blues",
        title: str = "",
        xlabel: str | None = None,
        ylabel: str | None = None,
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the joint distribution of one feature against another for two channels.

        Parameters
        ----------
        x : tuple[str, str]
            Tuple ``(channel_name, feature_name)`` used for the x axis.
        y : tuple[str, str]
            Tuple ``(channel_name, feature_name)`` used for the y axis.
        plot_type : str, optional
            Type of 2D rendering. Supported values are ``"scatter"``, ``"kde"``,
            and ``"hexbin"``.
        bandwidth_adjust : float, optional
            Bandwidth scaling factor passed to the KDE estimator.
        xscale : str, optional
            Scale used for the x axis. Typical values are ``"linear"`` and ``"log"``.
        yscale : str, optional
            Scale used for the y axis. Typical values are ``"linear"`` and ``"log"``.
        xlim : tuple[float, float] | None, optional
            Limits for the x axis.
        ylim : tuple[float, float] | None, optional
            Limits for the y axis.
        color_scale : str, optional
            Color scaling used for hexbin counts. Supported values are ``"linear"``
            and ``"log"``.
        figure : matplotlib.figure.Figure | None, optional
            Existing figure to use. If omitted, a new figure is created.
        ax : matplotlib.axes.Axes | None, optional
            Existing axes to use. If omitted, new axes are created.
        figsize : tuple[float, float], optional
            Figure size used when a new figure is created.
        show_marginals : bool, optional
            If ``True``, use a seaborn joint layout with marginal histograms.
        show_colorbar : bool, optional
            If ``True``, add a colorbar for hexbin density.
        show_scatter : bool, optional
            If ``True``, overlay raw points on top of the main rendering.
        fill : bool, optional
            If ``True``, fill the KDE contours.
        scatter_alpha : float, optional
            Transparency of the scatter overlay.
        scatter_size : float, optional
            Marker size of the scatter overlay.
        kde_alpha : float, optional
            Transparency of the KDE layer.
        hexbin_grid_size : int, optional
            Number of hexagons in the x direction used by ``hexbin``.
        hexbin_min_count : int, optional
            Minimum number of points required for a hexbin cell to be colored.
        hexbin_reduce_function : callable | None, optional
            Reduction function used by ``hexbin``. If ``None``, point counts are used.
        cmap : str, optional
            Colormap used for KDE or hexbin.
        title : str, optional
            Figure title.
        xlabel : str | None, optional
            Custom x label.
        ylabel : str | None, optional
            Custom y label.

        Returns
        -------
        tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
            The created or reused figure and main axes.
        """
        with plt.style.context(scientific):
            x_channel, x_feature = x
            y_channel, y_feature = y

            features = list(dict.fromkeys([x_feature, y_feature]))
            df = self.loc[[x_channel, y_channel], features].sort_index()

            x_values = numpy.asarray(df.loc[x], dtype=float)
            y_values = numpy.asarray(df.loc[y], dtype=float)

            current_xlabel = (
                xlabel if xlabel is not None else f"{x_channel} | {x_feature}"
            )
            current_ylabel = (
                ylabel if ylabel is not None else f"{y_channel} | {y_feature}"
            )

            if xscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported xscale: {xscale!r}. Expected 'linear' or 'log'."
                )

            if yscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported yscale: {yscale!r}. Expected 'linear' or 'log'."
                )

            if plot_type not in {"scatter", "kde", "hexbin"}:
                raise ValueError(
                    f"Unsupported plot_type: {plot_type!r}. "
                    "Expected 'scatter', 'kde', or 'hexbin'."
                )

            if color_scale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported color_scale: {color_scale!r}. "
                    "Expected 'linear' or 'log'."
                )

            if xscale == "log":
                valid = x_values > 0
                x_values = x_values[valid]
                y_values = y_values[valid]

            if yscale == "log":
                valid = y_values > 0
                x_values = x_values[valid]
                y_values = y_values[valid]

            if x_values.size == 0 or y_values.size == 0:
                raise ValueError("No valid data points remain after scale filtering.")

            def draw_main_artist(target_ax: plt.Axes):
                artist = None

                if plot_type == "scatter":
                    artist = target_ax.scatter(
                        x_values,
                        y_values,
                        alpha=scatter_alpha,
                        s=scatter_size,
                        color="C1",
                    )

                elif plot_type == "kde":
                    sns.kdeplot(
                        x=x_values,
                        y=y_values,
                        ax=target_ax,
                        fill=fill,
                        cmap=cmap,
                        bw_adjust=bandwidth_adjust,
                        alpha=kde_alpha,
                    )
                    artist = None

                    if show_scatter:
                        target_ax.scatter(
                            x_values,
                            y_values,
                            alpha=scatter_alpha,
                            s=scatter_size,
                            color="C1",
                        )

                elif plot_type == "hexbin":
                    hexbin_kwargs = dict(
                        x=x_values,
                        y=y_values,
                        gridsize=hexbin_grid_size,
                        cmap=cmap,
                        mincnt=hexbin_min_count,
                        reduce_C_function=hexbin_reduce_function,
                        linewidths=0.0,
                        xscale=xscale,
                        yscale=yscale,
                    )

                    if color_scale == "log":
                        hexbin_kwargs["bins"] = "log"

                    artist = target_ax.hexbin(**hexbin_kwargs)

                    if show_scatter:
                        target_ax.scatter(
                            x_values,
                            y_values,
                            alpha=min(scatter_alpha, 0.15),
                            s=max(scatter_size * 0.5, 1),
                            color="black",
                        )

                return artist

            if show_marginals:
                grid = sns.JointGrid(x=x_values, y=y_values, height=figsize[0])

                main_artist = draw_main_artist(grid.ax_joint)

                sns.histplot(x=x_values, ax=grid.ax_marg_x, bins=40)
                sns.histplot(y=y_values, ax=grid.ax_marg_y, bins=40)

                grid.ax_joint.set_xscale(xscale)
                grid.ax_joint.set_yscale(yscale)

                if xlim is not None:
                    grid.ax_joint.set_xlim(xlim)

                if ylim is not None:
                    grid.ax_joint.set_ylim(ylim)

                grid.ax_joint.set_xlabel(current_xlabel)
                grid.ax_joint.set_ylabel(current_ylabel)
                grid.ax_joint.set_title(title)

                grid.ax_marg_x.tick_params(
                    axis="both",
                    which="both",
                    bottom=False,
                    top=False,
                    left=False,
                    right=False,
                    labelbottom=False,
                    labelleft=False,
                )
                grid.ax_marg_y.tick_params(
                    axis="both",
                    which="both",
                    bottom=False,
                    top=False,
                    left=False,
                    right=False,
                    labelbottom=False,
                    labelleft=False,
                )

                grid.ax_marg_x.set_xlabel("")
                grid.ax_marg_x.set_ylabel("")
                grid.ax_marg_y.set_xlabel("")
                grid.ax_marg_y.set_ylabel("")

                if plot_type == "hexbin" and show_colorbar and main_artist is not None:
                    colorbar_label = "log10(count)" if color_scale == "log" else "count"
                    grid.figure.colorbar(
                        main_artist, ax=grid.ax_joint, pad=0.02, label=colorbar_label
                    )

                grid.figure.tight_layout()
                return grid.figure, grid.ax_joint

            if ax is None:
                figure, ax = plt.subplots(figsize=figsize)
            else:
                figure = ax.figure if figure is None else figure

            main_artist = draw_main_artist(ax)

            ax.set_xscale(xscale)
            ax.set_yscale(yscale)

            if xlim is not None:
                ax.set_xlim(xlim)

            if ylim is not None:
                ax.set_ylim(ylim)

            ax.set_xlabel(current_xlabel)
            ax.set_ylabel(current_ylabel)
            ax.set_title(title)

            if plot_type == "hexbin" and show_colorbar and main_artist is not None:
                colorbar_label = "log10(count)" if color_scale == "log" else "count"
                figure.colorbar(main_artist, ax=ax, pad=0.02, label=colorbar_label)

            figure.tight_layout()
            return figure, ax

    # def plot_2d(
    #     self,
    #     x: tuple[str, str],
    #     y: tuple[str, str],
    #     bandwidth_adjust: float = 0.8,
    #     xscale: str = "linear",
    #     yscale: str = "linear",
    #     xlim: tuple[float, float] | None = None,
    #     ylim: tuple[float, float] | None = None,
    #     figure: plt.Figure | None = None,
    #     ax: plt.Axes | None = None,
    #     figsize: tuple[float, float] = (9, 8),
    #     show_scatter: bool = True,
    #     show_kde: bool = False,
    #     fill: bool = False,
    #     show_marginals: bool = False,
    #     scatter_alpha: float = 0.5,
    #     scatter_size: float = 20,
    #     kde_alpha: float = 0.7,
    #     cmap: str = "Blues",
    #     title: str = "",
    #     xlabel: str | None = None,
    #     ylabel: str | None = None,
    # ) -> tuple[plt.Figure, plt.Axes]:
    #     """
    #     Plot the joint distribution of one feature against another for two detectors.

    #     Parameters
    #     ----------
    #     x : tuple[str, str]
    #         Tuple ``(detector_name, feature_name)`` used for the x axis.
    #     y : tuple[str, str]
    #         Tuple ``(detector_name, feature_name)`` used for the y axis.
    #     bandwidth_adjust : float, optional
    #         Bandwidth scaling factor passed to the KDE estimator.
    #     xscale : str, optional
    #         Scale used for the x axis. Typical values are ``"linear"`` and ``"log"``.
    #     yscale : str, optional
    #         Scale used for the y axis. Typical values are ``"linear"`` and ``"log"``.
    #     figure : matplotlib.figure.Figure, optional
    #         Existing figure to use. If omitted, a new figure is created.
    #     ax : matplotlib.axes.Axes, optional
    #         Existing axes to use. If omitted, new axes are created.
    #     figsize : tuple[float, float], optional
    #         Figure size used when a new figure is created.
    #     show_scatter : bool, optional
    #         If ``True``, overlay the raw data points.
    #     show_kde : bool, optional
    #         If ``True``, draw the 2D KDE.
    #     fill : bool, optional
    #         If ``True``, fill the KDE contours.
    #     show_marginals : bool, optional
    #         If ``True``, use a seaborn joint layout with marginal distributions.
    #         In this mode, a dedicated figure layout is created and the provided
    #         ``figure`` and ``ax`` are ignored.
    #     scatter_alpha : float, optional
    #         Transparency of the scatter points.
    #     scatter_size : float, optional
    #         Marker size of the scatter points.
    #     kde_alpha : float, optional
    #         Transparency of the KDE layer.
    #     cmap : str, optional
    #         Colormap used for the KDE.
    #     title : str, optional
    #         Figure title.
    #     xlabel : str, optional
    #         Custom x axis label. If omitted, an automatic label is generated.
    #     ylabel : str, optional
    #         Custom y axis label. If omitted, an automatic label is generated.

    #     Returns
    #     -------
    #     tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
    #         The created or reused figure and main axes.

    #     Notes
    #     -----
    #     The dataframe is expected to be indexed by ``(detector_name, feature_name)``
    #     pairs so that ``df.loc[x]`` and ``df.loc[y]`` return the corresponding
    #     feature vectors.
    #     """
    #     with plt.style.context(scientific):
    #         x_detector, x_feature = x
    #         y_detector, y_feature = y

    #         features = list(dict.fromkeys([x_feature, y_feature]))
    #         df = self.loc[[x_detector, y_detector], features].sort_index()

    #         x_values = df.loc[x]
    #         y_values = df.loc[y]

    #         current_xlabel = xlabel if xlabel is not None else f"Channel: {x_detector} | {x_feature}"
    #         current_ylabel = ylabel if ylabel is not None else f"Channel: {y_detector} | {y_feature}"

    #         if show_marginals:
    #             grid = sns.JointGrid(x=x_values, y=y_values, height=figsize[0])

    #             if show_kde:
    #                 sns.kdeplot(
    #                     x=x_values,
    #                     y=y_values,
    #                     ax=grid.ax_joint,
    #                     fill=fill,
    #                     cmap=cmap,
    #                     bw_adjust=bandwidth_adjust,
    #                     alpha=kde_alpha,
    #                 )

    #             if show_scatter:
    #                 grid.ax_joint.scatter(
    #                     x_values,
    #                     y_values,
    #                     alpha=scatter_alpha,
    #                     s=scatter_size,
    #                     color="C1",
    #                 )

    #             sns.histplot(x=x_values, ax=grid.ax_marg_x, bins=40)
    #             sns.histplot(y=y_values, ax=grid.ax_marg_y, bins=40)

    #             grid.ax_joint.set_xscale(xscale)
    #             grid.ax_joint.set_yscale(yscale)
    #             if xlim is not None:
    #                 grid.ax_joint.set_xlim(xlim)

    #             if ylim is not None:
    #                 grid.ax_joint.set_ylim(ylim)

    #             grid.ax_joint.set_xlabel(current_xlabel)
    #             grid.ax_joint.set_ylabel(current_ylabel)

    #             grid.ax_marg_x.tick_params(
    #                 axis="both",
    #                 which="both",
    #                 bottom=False,
    #                 top=False,
    #                 left=False,
    #                 right=False,
    #                 labelbottom=False,
    #                 labelleft=False,
    #             )
    #             grid.ax_marg_y.tick_params(
    #                 axis="both",
    #                 which="both",
    #                 bottom=False,
    #                 top=False,
    #                 left=False,
    #                 right=False,
    #                 labelbottom=False,
    #                 labelleft=False,
    #             )

    #             grid.ax_marg_x.set_xlabel("")
    #             grid.ax_marg_x.set_ylabel("")
    #             grid.ax_marg_y.set_xlabel("")
    #             grid.ax_marg_y.set_ylabel("")
    #             grid.ax_joint.set_title(title)

    #             grid.figure.tight_layout()

    #             return grid.figure, grid.ax_joint

    #         if ax is None:
    #             figure, ax = plt.subplots(figsize=figsize)
    #         else:
    #             figure = ax.figure if figure is None else figure

    #         if show_kde:
    #             sns.kdeplot(
    #                 x=x_values,
    #                 y=y_values,
    #                 ax=ax,
    #                 fill=fill,
    #                 cmap=cmap,
    #                 bw_adjust=bandwidth_adjust,
    #                 alpha=kde_alpha,
    #             )

    #         if show_scatter:
    #             ax.scatter(
    #                 x_values,
    #                 y_values,
    #                 alpha=scatter_alpha,
    #                 s=scatter_size,
    #                 color="C1",
    #             )

    #         ax.set_xscale(xscale)
    #         ax.set_yscale(yscale)

    #         if xlim is not None:
    #             ax.set_xlim(xlim)

    #         if ylim is not None:
    #             ax.set_ylim(ylim)

    #         ax.set_xlabel(current_xlabel)
    #         ax.set_ylabel(current_ylabel)
    #         ax.set_title(title)
    #         plt.tight_layout()

    #         return figure, ax

    @helper.post_mpl_plot
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
