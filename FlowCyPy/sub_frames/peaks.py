from typing import Any, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import MPSPlots
from MPSPlots import helper
import numpy
import pandas as pd
import seaborn as sns
from TypedUnit import ureg

from MPSPlots.styles import mps
import numpy as np
import pint_pandas
from TypedUnit import Quantity


class PeakDataFrame(pd.DataFrame):
    """
    DataFrame subclass storing detector peak metrics indexed by detector and segment.

    The row index is a three-level ``MultiIndex`` with the levels
    ``("Detector", "SegmentID", "PeakID")``. Columns store peak features such
    as ``Index``, ``Height``, ``Width``, or ``Area``.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of PeakDataFrame."""
        return self.__class__

    def __init__(self, dataframe: pd.DataFrame, **kwargs):
        """Initialize a peak dataframe wrapper.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataframe containing peak metrics indexed by detector, segment, and
            peak identifier.
        **kwargs
            Additional keyword arguments forwarded to ``pandas.DataFrame``.
        """
        super().__init__(dataframe, **kwargs)

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
        Dispatch peak plotting to the appropriate dimensionality.

        Parameters
        ----------
        **kwargs
            Plot arguments forwarded to :meth:`plot_hist`, :meth:`plot_2d`, or
            :meth:`plot_3d`. The presence of ``y`` selects 2D plotting and the
            presence of ``z`` selects 3D plotting.

        Returns
        -------
        Any
            Figure, or figure and axes pair, returned by the selected plotting
            method.
        """
        if "z" in kwargs:
            return self.plot_3d(**kwargs)

        if "y" in kwargs:
            figure, _ = self.plot_2d(**kwargs)
            return figure

        return self.plot_hist(**kwargs)

    def standard_deviation(
        self, detector_name: str, metrics: str | slice = slice(None)
    ):
        """
        Calculate the standard deviation of selected peak metrics.

        Parameters
        ----------
        detector_name : str
            Detector name used to select the peak rows.
        metrics : str or slice, optional
            Metric name or slice selecting the metric columns to aggregate.

        Returns
        -------
        Any
            Standard deviation for the selected metrics.
        """
        sub_frame = self.loc[detector_name, metrics]

        return sub_frame.std()

    def robust_standard_deviation(
        self, detector_name: str, metrics: str | slice = slice(None)
    ):
        """
        Estimate the robust standard deviation of selected peak metrics.

        Parameters
        ----------
        detector_name : str
            Detector name used to select the peak rows.
        metrics : str or slice, optional
            Metric name or slice selecting the metric columns to aggregate.

        Returns
        -------
        Any
            Median absolute deviation scaled to a normal-equivalent standard
            deviation for the selected metrics.
        """
        sub_frame = self.loc[detector_name, metrics]

        return numpy.abs(sub_frame - sub_frame.median()).median() * 1.4826

    def mean(self, detector_name: str, metrics: str | slice = slice(None)):
        """
        Calculate the mean of selected peak metrics.

        Parameters
        ----------
        detector_name : str
            Detector name used to select the peak rows.
        metrics : str or slice, optional
            Metric name or slice selecting the metric columns to aggregate.

        Returns
        -------
        Any
            Mean value for the selected metrics.
        """
        sub_frame = self.loc[detector_name, metrics]
        return sub_frame.mean(axis=0)

    def get_sub_dataframe(
        self, columns: List[str], rows: List[str]
    ) -> Tuple[pd.DataFrame, List[Any]]:
        """
        Extract a detector subset and convert each column to a compact display unit.

        Parameters
        ----------
        columns : list
            Metric columns to keep.
        rows : list
            Detector index entries to keep.

        Returns
        -------
        tuple
            Tuple containing the converted dataframe and the chosen units for
            each selected column.
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

    def _get_axis_label(
        self,
        axis_key: tuple[str, str],
        unit: Any = None,
    ) -> str:
        """Build a display label for a detector-feature axis."""
        detector_name, feature_name = axis_key
        base_label = f"{detector_name} | {feature_name}"

        if unit is None:
            return base_label

        return f"{base_label} [{unit:~P}]"

    def _hide_marginal_axis_ticks(self, ax: plt.Axes) -> None:
        """Hide ticks and tick labels for a marginal histogram axis."""
        ax.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
            length=0,
        )

        for tick_label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
            tick_label.set_visible(False)

        for tick_line in (*ax.get_xticklines(), *ax.get_yticklines()):
            tick_line.set_visible(False)

    def _get_marginal_bins(
        self,
        values: np.ndarray,
        scale: str,
        bin_count: int = 40,
    ) -> np.ndarray | int:
        """Return histogram bins appropriate for linear or log axes."""
        if scale != "log":
            return bin_count

        positive_values = values[values > 0]

        if positive_values.size == 0:
            raise ValueError("No positive data points remain for a log-scaled axis.")

        minimum_value = positive_values.min()
        maximum_value = positive_values.max()

        if np.isclose(minimum_value, maximum_value):
            return np.geomspace(minimum_value / 1.1, maximum_value * 1.1, 3)

        return np.geomspace(minimum_value, maximum_value, bin_count)

    def _get_plot_series(
        self,
        axis_key: tuple[str, str],
        clip_value: str | Quantity = None,
    ) -> tuple[pd.Series, Any]:
        """Return one plotted feature series and its compact display unit."""
        series = self.loc[axis_key].sort_index()
        series = self.clip_data(signal=series, clip_value=clip_value)

        if not hasattr(series, "pint"):
            return series, None

        if len(series) == 0:
            return series, None

        unit = series.max().to_compact().units
        series = series.pint.to(unit)

        return series, unit

    @helper.post_mpl_plot
    def plot_hist(
        self,
        x: tuple[str, str],
        kde: bool = False,
        bins: Optional[int] = 50,
        color: Optional[Union[str, dict]] = None,
        xscale: str = "linear",
        yscale: str = "linear",
        figure_size: tuple[float, float] = (6, 6),
        save_as: str | None = None,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        binrange: Optional[tuple] = None,
        clip_data: Optional[Union[str, Any]] = None,
    ) -> plt.Figure:
        """
        Plot a histogram distribution for one detector-feature pair.

        Parameters
        ----------
        x : tuple[str, str]
            The column name to plot (eg. ('forward', 'Height')).
        kde : bool, optional
            Whether to overlay a KDE curve (default: False).
        bins : int | sequence, default=50
            Histogram bin count or explicit bin edges.
        color : Optional[Union[str, dict]], optional
            Color specification for the plot (default: None).
        xscale, yscale : {"linear", "log"}, default="linear"
            Axis scales used for the histogram.
        figure_size : tuple[float, float], default=(6, 6)
            Figure size in inches.
        save_as : str | None, optional
            Optional output path used to save the figure.
        title, xlabel, ylabel : str | None, optional
            Optional explicit labels overriding the defaults.
        xlim, ylim : tuple[float, float] | None, optional
            Optional axis limits.
        binrange : tuple | None, optional
            Explicit histogram range passed to seaborn.
        clip_data : Optional[Union[str, Any]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            values above the corresponding quantile (e.g. the top 20% of values) are excluded.
            If a pint.Quantity is given, values above that absolute value are removed.

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        with plt.style.context(MPSPlots.styles.scientific):
            figure, ax = plt.subplots(1, 1, figsize=figure_size)

            if xscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported xscale: {xscale!r}. Expected 'linear' or 'log'."
                )

            if yscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported yscale: {yscale!r}. Expected 'linear' or 'log'."
                )

            series, unit = self._get_plot_series(x, clip_value=clip_data)
            values = np.asarray(series, dtype=float)

            valid_mask = np.isfinite(values)

            if xscale == "log":
                valid_mask &= values > 0

            values = values[valid_mask]

            if values.size == 0:
                raise ValueError("No valid data points remain after scale filtering.")

            hist_bins = bins

            if isinstance(bins, int):
                hist_bins = self._get_marginal_bins(values, xscale, bin_count=bins)

            sns.histplot(
                x=values,
                ax=ax,
                kde=kde,
                bins=hist_bins,
                color=color,
                binrange=binrange,
                edgecolor="black",
                linewidth=1.0,
            )

            detector_name, feature_name = x
            ax.set_xlabel(xlabel or self._get_axis_label(x, unit=unit))
            ax.set_ylabel(ylabel or "Counts")
            ax.set_title(title or f"Distribution of {detector_name} | {feature_name}")
            ax.set_xscale(xscale)
            ax.set_yscale(yscale)

            if xlim is not None:
                ax.set_xlim(xlim)

            if ylim is not None:
                ax.set_ylim(ylim)

            if save_as is not None:
                figure.savefig(save_as)

            return figure

    @helper.post_mpl_plot
    def hist(self, *args, **kwargs) -> plt.Figure:
        """Call :meth:`plot_hist` using the legacy histogram API.

        Parameters
        ----------
        *args
            Positional arguments forwarded to :meth:`plot_hist`.
        **kwargs
            Keyword arguments forwarded to :meth:`plot_hist`.

        Returns
        -------
        plt.Figure
            Histogram figure returned by :meth:`plot_hist`.
        """
        return self.plot_hist(*args, **kwargs)

    def plot_2d(
        self,
        x: tuple[str, str],
        y: tuple[str, str],
        alpha: float = 0.8,
        xscale: str = "linear",
        yscale: str = "linear",
        marginal_nbins: int = 40,
        figure_size: tuple[float, float] = (6, 6),
        save_as: str | None = None,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        plot_type: str = "scatter",
        bandwidth_adjust: float = 0.8,
        color_scale: str = "linear",
        figure: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        figsize: tuple[float, float] | None = None,
        show_marginals: bool = True,
        show_colorbar: bool = True,
        show_scatter: bool = False,
        fill: bool = False,
        scatter_alpha: float | None = None,
        scatter_size: float = 20,
        kde_alpha: float = 0.7,
        hexbin_grid_size: int = 30,
        hexbin_min_count: int = 1,
        hexbin_reduce_function=None,
        cmap: str = "Blues",
        clip_data: Optional[Union[str, Any]] = None,
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
        with plt.style.context(MPSPlots.styles.scientific):
            x_channel, x_feature = x
            y_channel, y_feature = y

            if figsize is not None:
                figure_size = figsize

            features = list(dict.fromkeys([x_feature, y_feature]))
            df = self.loc[[x_channel, y_channel], features].sort_index()

            x_series = self.clip_data(signal=df.loc[x], clip_value=clip_data)
            y_series = self.clip_data(signal=df.loc[y], clip_value=clip_data)

            x_unit = None
            y_unit = None

            if hasattr(x_series, "pint") and len(x_series) > 0:
                x_unit = x_series.max().to_compact().units
                x_series = x_series.pint.to(x_unit)

            if hasattr(y_series, "pint") and len(y_series) > 0:
                y_unit = y_series.max().to_compact().units
                y_series = y_series.pint.to(y_unit)

            plot_dataframe = pd.DataFrame(
                {
                    "x": numpy.asarray(x_series, dtype=float),
                    "y": numpy.asarray(y_series, dtype=float),
                }
            )

            current_xlabel = xlabel or self._get_axis_label(x, unit=x_unit)
            current_ylabel = ylabel or self._get_axis_label(y, unit=y_unit)

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

            valid_mask = np.isfinite(plot_dataframe["x"]) & np.isfinite(plot_dataframe["y"])

            if xscale == "log":
                valid_mask &= plot_dataframe["x"] > 0

            if yscale == "log":
                valid_mask &= plot_dataframe["y"] > 0

            plot_dataframe = plot_dataframe.loc[valid_mask].copy()

            if plot_dataframe.empty:
                raise ValueError("No valid data points remain after scale filtering.")

            if marginal_nbins < 1:
                raise ValueError("marginal_nbins must be a positive integer.")

            x_values = plot_dataframe["x"].to_numpy(dtype=float)
            y_values = plot_dataframe["y"].to_numpy(dtype=float)

            effective_scatter_alpha = (
                scatter_alpha if scatter_alpha is not None else alpha
            )

            x_bins = self._get_marginal_bins(
                x_values,
                xscale,
                bin_count=marginal_nbins,
            )
            y_bins = self._get_marginal_bins(
                y_values,
                yscale,
                bin_count=marginal_nbins,
            )

            def draw_main_artist(target_ax: plt.Axes):
                artist = None

                if plot_type == "scatter":
                    artist = target_ax.scatter(
                        x_values,
                        y_values,
                        alpha=effective_scatter_alpha,
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
                            alpha=effective_scatter_alpha,
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
                            alpha=min(effective_scatter_alpha, 0.15),
                            s=max(scatter_size * 0.5, 1),
                            color="black",
                        )

                return artist

            if show_marginals:
                grid = sns.JointGrid(data=plot_dataframe, x="x", y="y")
                grid.figure.set_size_inches(*figure_size)

                main_artist = draw_main_artist(grid.ax_joint)

                sns.histplot(
                    data=plot_dataframe,
                    x="x",
                    ax=grid.ax_marg_x,
                    bins=x_bins,
                    legend=False,
                    edgecolor="black",
                    linewidth=1.0,
                )
                sns.histplot(
                    data=plot_dataframe,
                    y="y",
                    ax=grid.ax_marg_y,
                    bins=y_bins,
                    legend=False,
                    edgecolor="black",
                    linewidth=1.0,
                )

                grid.ax_joint.set_xscale(xscale)
                grid.ax_joint.set_yscale(yscale)
                grid.ax_marg_x.set_xscale(xscale)
                grid.ax_marg_y.set_yscale(yscale)

                if xlim is not None:
                    grid.ax_joint.set_xlim(xlim)
                    grid.ax_marg_x.set_xlim(xlim)

                if ylim is not None:
                    grid.ax_joint.set_ylim(ylim)
                    grid.ax_marg_y.set_ylim(ylim)

                grid.ax_joint.set_xlabel(current_xlabel)
                grid.ax_joint.set_ylabel(current_ylabel)
                grid.ax_joint.tick_params(
                    axis="both",
                    which="both",
                    bottom=True,
                    left=True,
                    top=False,
                    right=False,
                    labelbottom=True,
                    labelleft=True,
                    labeltop=False,
                    labelright=False,
                )
                self._hide_marginal_axis_ticks(grid.ax_marg_x)
                self._hide_marginal_axis_ticks(grid.ax_marg_y)

                if title is not None:
                    grid.figure.suptitle(title)

                if plot_type == "hexbin" and show_colorbar and main_artist is not None:
                    colorbar_label = "log10(count)" if color_scale == "log" else "count"
                    grid.figure.colorbar(
                        main_artist, ax=grid.ax_joint, pad=0.02, label=colorbar_label
                    )

                if save_as is not None:
                    grid.figure.savefig(save_as)

                return grid.figure, grid.ax_joint

            if ax is None:
                figure, ax = plt.subplots(figsize=figure_size)
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
            ax.set_title(title or "")

            if plot_type == "hexbin" and show_colorbar and main_artist is not None:
                colorbar_label = "log10(count)" if color_scale == "log" else "count"
                figure.colorbar(main_artist, ax=ax, pad=0.02, label=colorbar_label)

            if save_as is not None:
                figure.savefig(save_as)

            figure.tight_layout()
            return figure, ax

    @helper.post_mpl_plot
    def plot_3d(self, x: str, y: str, z: str) -> plt.Figure:
        """
        Create a 3D scatter plot of a feature across three detectors.

        Parameters
        ----------
        x : tuple[str, str]
            Tuple ``(detector_name, feature_name)`` used for the x axis.
        y : tuple[str, str]
            Tuple ``(detector_name, feature_name)`` used for the y axis.
        z : tuple[str, str]
            Tuple ``(detector_name, feature_name)`` used for the z axis.

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

    def clip_data(
        self, signal: pint_pandas.PintArray, clip_value: str | Quantity = None
    ) -> pint_pandas.PintArray:
        """
        Remove values above a threshold from a peak metric series.

        If ``clip_value`` is a string ending with ``%``, it is interpreted as a
        top-tail percentage to discard. If it is a quantity, values above that
        absolute threshold are removed. If it is ``None``, the input is returned
        unchanged.

        Parameters
        ----------
        signal : pint_pandas.PintArray
            Series-like pint array to filter.
        clip_value : str or Quantity, optional
            Clipping threshold expressed either as a percentage string or an
            absolute quantity.

        Returns
        -------
        pint_pandas.PintArray
            Filtered signal containing only values at or below the threshold.
        """
        if clip_value is None:
            # If no clip value is provided, return the original signal.
            return signal

        # Remove data above the clip threshold if clip_value is provided.
        if clip_value is not None:
            if isinstance(clip_value, str) and clip_value.endswith("%"):
                # For a percentage clip, compute the threshold quantile.
                percent = float(clip_value.rstrip("%"))
                clip_value = np.percentile(signal, 100 - percent)
            else:
                clip_value = clip_value.to(signal.pint.signal_units).magnitude
            # Remove values above clip_value instead of clipping them.
            signal = signal[signal <= clip_value]

        return signal

    def get_flattened_dataframe(self):
        """Return a flat event-wise dataframe with detector-feature columns.

        Returns
        -------
        pd.DataFrame
            Flattened dataframe where columns are named as
            ``"{detector}-{metric_suffix}"``.

        Notes
        -----
        This representation is convenient for exporting peak tables to tools
        that do not handle multi-indexed columns well.
        """

        df = self.copy().unstack("Detector")

        # Move detector first, metric second
        df.columns = df.columns.swaplevel(0, 1)

        # Sort columns if desired
        df = df.sort_index(axis=1)

        # Rename metrics to short suffixes
        metric_map = {
            "Index": "I",
            "Height": "H",
            "Area": "A",
        }

        # Flatten MultiIndex columns
        df.columns = [
            f"{detector}-{metric_map[metric]}" for detector, metric in df.columns
        ]

        # Optional: bring SegmentID / PeakID back as normal columns
        df = df.reset_index()

        return df
