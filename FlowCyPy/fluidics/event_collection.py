#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utilities for managing and visualizing collections of simulated events.

This module defines :class:`EventCollection`, the high-level container used to
group multiple :class:`PopulationEvents` blocks produced during a single
acquisition. The collection exposes helpers to:

- iterate over population-specific event blocks,
- normalize units across populations,
- concatenate event tables into one dataframe,
- generate 1D, 2D, and 3D visualizations with consistent styling.

The class is intentionally lightweight: it stores the population event blocks
and computes derived dataframes or figures on demand.
"""

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any, Iterator, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import MPSPlots

from FlowCyPy.sub_frames.events import EventDataFrame
from .populations import ExplicitModel, GammaModel
from .population_events import PopulationEvents


@dataclass
class EventCollection:
    """
    Container storing all population event blocks for one acquisition.

    Parameters
    ----------
    events_list : list[PopulationEvents], optional
        Population specific event containers.
    """

    events_list: list[PopulationEvents] = field(default_factory=list)

    def __iter__(self) -> Iterator[PopulationEvents]:
        """Iterate over the stored population event blocks."""
        return iter(self.events_list)

    def __len__(self) -> int:
        """Return the number of stored population event blocks."""
        return len(self.events_list)

    def __getitem__(self, index: int) -> PopulationEvents:
        """Return one population event block by index."""
        return self.events_list[index]

    def append(self, events: PopulationEvents) -> None:
        """Append a population event block to the collection.

        Parameters
        ----------
        events : PopulationEvents
            Population-specific event block to append.
        """
        self.events_list.append(events)

    @property
    def empty(self) -> bool:
        """Return ``True`` when all stored event blocks are empty."""
        return all(events.empty for events in self.events_list)

    def copy(self) -> "EventCollection":
        """Return a detached copy of the event collection.

        Returns
        -------
        EventCollection
            New collection containing copied population event blocks.
        """
        return EventCollection(
            events_list=[events.copy() for events in self.events_list]
        )

    def convert_units(
        self,
        column_units: dict[str, Any],
        inplace: bool = True,
    ) -> "EventCollection":
        """
        Convert stored dataframe columns to the requested units.

        Parameters
        ----------
        column_units : dict[str, Any]
            Mapping from column name to target unit.
        inplace : bool, default=True
            If ``True``, update this collection in place. Otherwise return a copy.

        Returns
        -------
        EventCollection
            Converted collection.

        Raises
        ------
        TypeError
            If ``column_units`` is not a mapping from column names to target units.
        """
        if not isinstance(column_units, Mapping):
            raise TypeError(
                "column_units must be a mapping of column names to target units, "
                "for example {'Diameter': 'nanometer'}."
            )

        converted_collection = self if inplace else self.copy()

        for events in converted_collection.events_list:
            converted_dataframe = self._convert_events_to_target_units(
                events=events,
                target_units=column_units,
            )
            converted_dataframe.scatterer_type = events.scatterer_type
            events.dataframe = converted_dataframe

        return converted_collection

    def to_dataframes(
        self,
        include_metadata_in_attrs: bool = True,
    ) -> list[EventDataFrame]:
        """Export each population block as a standalone dataframe.

        Parameters
        ----------
        include_metadata_in_attrs : bool, default=True
            If ``True``, copy population metadata into ``DataFrame.attrs`` for
            each exported dataframe.

        Returns
        -------
        list[EventDataFrame]
            One dataframe per stored population event block.
        """
        return [
            events.to_dataframe(include_metadata_in_attrs=include_metadata_in_attrs)
            for events in self.events_list
        ]

    def get_population_events(
        self,
        population_name: str,
    ) -> Optional[PopulationEvents]:
        """Return the event block matching a population name.

        Parameters
        ----------
        population_name : str
            Name of the target population.

        Returns
        -------
        PopulationEvents | None
            Matching event block, or ``None`` if the population is not present.
        """
        for events in self.events_list:
            if events.name == population_name:
                return events

        return None

    def _get_selected_events(
        self,
        filter_population: Optional[List[str]] = None,
    ) -> list[PopulationEvents]:
        """Return the non-empty event blocks selected for an operation.

        Parameters
        ----------
        filter_population : list[str] | None, optional
            Optional list of population names to keep. If omitted, all non-empty
            populations are returned.

        Returns
        -------
        list[PopulationEvents]
            Selected non-empty population event blocks.
        """
        selected_events = []

        for events in self.events_list:
            if events.empty:
                continue

            if filter_population is not None and events.name not in filter_population:
                continue

            selected_events.append(events)

        return selected_events

    def _get_target_units(
        self,
        selected_events: list[PopulationEvents],
    ) -> dict[str, Any]:
        """Infer a unit map that can be shared across selected populations.

        The first encountered unit for each column is used as the target unit.

        Parameters
        ----------
        selected_events : list[PopulationEvents]
            Population event blocks that will be aligned together.

        Returns
        -------
        dict[str, Any]
            Mapping from column name to target unit.
        """
        target_units: dict[str, Any] = {}

        for events in selected_events:
            for column_name, unit in events.dataframe.units.items():
                if column_name not in target_units:
                    target_units[column_name] = unit

        return target_units

    def _convert_events_to_target_units(
        self,
        events: PopulationEvents,
        target_units: dict[str, Any],
    ) -> EventDataFrame:
        """Convert one population dataframe to a target unit mapping.

        Parameters
        ----------
        events : PopulationEvents
            Event block whose dataframe should be converted.
        target_units : dict[str, Any]
            Mapping from column name to target unit.

        Returns
        -------
        EventDataFrame
            Converted dataframe copy. The original dataframe is left untouched.
        """
        dataframe = events.dataframe.copy(deep=True)
        dataframe.attrs = {
            key: value.copy() if isinstance(value, dict) else value
            for key, value in events.dataframe.attrs.items()
        }

        for column_name, target_unit in target_units.items():
            if column_name not in dataframe.columns:
                continue

            column_unit = dataframe.get_unit(column_name)

            if column_unit is None:
                continue

            quantity = dataframe.get_quantity(column_name).to(target_unit)
            dataframe.set_column(column_name=column_name, values=quantity)

        return dataframe

    def _get_empty_population_dataframe(self) -> pd.DataFrame:
        """Return an empty population-indexed dataframe placeholder.

        Returns
        -------
        pandas.DataFrame
            Empty dataframe with the expected ``Population`` multi-index.
        """
        return pd.DataFrame(
            index=pd.MultiIndex(
                levels=[[]],
                codes=[[]],
                names=["Population"],
            )
        )

    def _build_dataframe_and_units(
        self,
        filter_population: Optional[List[str]] = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Build a population-indexed dataframe aligned in common units.

        Parameters
        ----------
        filter_population : list[str] | None, optional
            Optional subset of population names to include.

        Returns
        -------
        tuple[pandas.DataFrame, dict[str, Any]]
            Concatenated dataframe and the unit mapping applied to it.
        """
        selected_events = self._get_selected_events(filter_population=filter_population)

        if not selected_events:
            return self._get_empty_population_dataframe(), {}

        target_units = self._get_target_units(selected_events=selected_events)

        dataframe_blocks = []
        population_names = []

        for events in selected_events:
            converted_dataframe = self._convert_events_to_target_units(
                events=events,
                target_units=target_units,
            )
            dataframe_blocks.append(pd.DataFrame(converted_dataframe))
            population_names.append(events.name)

        population_dataframe = pd.concat(
            dataframe_blocks,
            keys=population_names,
            names=["Population"],
        )

        return population_dataframe, target_units

    def _get_axis_label(
        self,
        column_name: str,
        target_units: dict[str, Any],
    ) -> str:
        """Build a human-readable axis label for a column.

        Parameters
        ----------
        column_name : str
            Column displayed on the axis.
        target_units : dict[str, Any]
            Unit mapping used for the plotted dataframe.

        Returns
        -------
        str
            Label with compact unit formatting when unit metadata exists.
        """
        unit = target_units.get(column_name, None)

        if unit is None:
            return column_name

        return f"{column_name} [{unit:~P}]"

    def _get_population_weight_map(
        self,
        filter_population: Optional[List[str]] = None,
    ) -> dict[str, float]:
        """Return concentration-based plotting weights by population.

        Parameters
        ----------
        filter_population : list[str] | None, optional
            Optional subset of populations to include.

        Returns
        -------
        dict[str, float]
            Population name to particle concentration in
            ``particle / milliliter``.
        """
        return {
            events.name: events.metadata["ParticleCount"]
            .to("particle / milliliter")
            .magnitude
            for events in self._get_selected_events(filter_population=filter_population)
        }

    def _get_color_mapping(
        self,
        selected_events: list[PopulationEvents],
    ) -> dict[str, Any]:
        """Assign a display color to each selected population.

        Parameters
        ----------
        selected_events : list[PopulationEvents]
            Population blocks that will be plotted.

        Returns
        -------
        dict[str, Any]
            Mapping from population name to matplotlib-compatible color.
        """
        palette = sns.color_palette("tab10", len(selected_events))

        return {
            events.population.name: color
            for events, color in zip(selected_events, palette)
        }

    def _hide_marginal_axis_ticks(self, ax) -> None:
        """Hide ticks and tick labels for a marginal histogram axis.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Marginal axis to clean up.
        """
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
        """Return histogram bins appropriate for linear or log axes.

        Parameters
        ----------
        values : numpy.ndarray
            Values to histogram.
        scale : str
            Axis scale, typically ``"linear"`` or ``"log"``.
        bin_count : int, default=40
            Number of bins to generate.

        Returns
        -------
        numpy.ndarray | int
            Integer bin count for linear scale, or explicit logarithmic bin
            edges for log scale.

        Raises
        ------
        ValueError
            If log-scaled binning is requested but no positive values remain.
        """
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

    def _add_to_ax(
        self,
        ax,
        time_units: str,
        filter_population: Optional[List[str]] = None,
    ) -> None:
        """Draw a time-domain population overview on an existing axis.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Target axis.
        time_units : str
            Units used to display the time axis.
        filter_population : list[str] | None, optional
            Optional subset of populations to include.
        """
        selected_events = self._get_selected_events(filter_population=filter_population)

        color_mapping = self._get_color_mapping(selected_events=selected_events)

        for events in selected_events:
            if isinstance(events.sampling_method, ExplicitModel):
                self._add_explicit_model_to_ax(
                    events=events,
                    ax=ax,
                    color=color_mapping[events.population.name],
                    time_units=time_units,
                )

            elif isinstance(events.sampling_method, GammaModel):
                self._add_gamma_model_to_ax(
                    events=events,
                    ax=ax,
                    color=color_mapping[events.population.name],
                    time_units=time_units,
                )

        ax.set_xlabel(f"Time [{time_units}]")

        handles, _ = ax.get_legend_handles_labels()

        if handles:
            ax.legend()

    def get_concatenated_dataframe(
        self,
        filter_population: Optional[List[str]] = None,
    ) -> EventDataFrame:
        """Return all selected event blocks as one unit-aware dataframe.

        Parameters
        ----------
        filter_population : list[str] | None, optional
            Optional subset of populations to include.

        Returns
        -------
        EventDataFrame
            Concatenated dataframe indexed by population with aligned units.
        """
        population_dataframe, target_units = self._build_dataframe_and_units(
            filter_population=filter_population
        )

        concatenated_dataframe = EventDataFrame(population_dataframe)
        concatenated_dataframe.attrs["units"] = dict(target_units)

        return concatenated_dataframe

    def plot(
        self,
        x: str = None,
        y: str = None,
        z: str = None,
        **kwargs,
    ) -> plt.Figure:
        """Dispatch to a 1D, 2D, or 3D plotting helper.

        Parameters
        ----------
        x, y, z : str | None
            Column names defining the requested projection.
        **kwargs
            Additional keyword arguments forwarded to the selected plotting
            method.

        Returns
        -------
        matplotlib.figure.Figure
            Generated figure.

        Raises
        ------
        ValueError
            If no valid axis combination is provided.
        """
        if x and not y and not z:
            return self.plot_hist(x=x, **kwargs)

        if x and y and not z:
            return self.plot_2d(x=x, y=y, **kwargs)

        if x and y and z:
            return self.plot_3d(x=x, y=y, z=z, **kwargs)

        raise ValueError(
            "At least one of 'x', 'y', or 'z' must be provided for plotting."
        )

    def plot_hist(
        self,
        x: str = "Diameter",
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
        filter_population: Optional[List[str]] = None,
        binrange: Optional[tuple] = None,
        common_norm: bool = False,
        common_bins: bool = False,
        scale_by_concentration: bool = False,
        scale_by_bin: bool = False,
    ) -> plt.Figure:
        """Plot a 1D population distribution.

        Parameters
        ----------
        x : str, default="Diameter"
            Column plotted on the x axis.
        kde : bool, default=False
            If ``True``, overlay a kernel density estimate.
        bins : int | sequence, default=50
            Histogram bin count or explicit bin edges.
        color : str | dict | None, optional
            Optional seaborn/matplotlib color control.
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
        filter_population : list[str] | None, optional
            Optional subset of populations to include.
        binrange : tuple | None, optional
            Explicit histogram range passed to seaborn.
        common_norm : bool, default=False
            Forwarded to seaborn to control normalization across hue levels.
        common_bins : bool, default=False
            Forwarded to seaborn to control shared binning across hue levels.
        scale_by_concentration : bool, default=False
            If ``True``, weight counts by particle concentration.
        scale_by_bin : bool, default=False
            If ``True``, normalize by bin width as well.

        Returns
        -------
        matplotlib.figure.Figure
            Generated histogram figure.
        """
        with plt.style.context(MPSPlots.styles.scientific):
            population_dataframe, target_units = self._build_dataframe_and_units(
                filter_population=filter_population
            )

            figure, ax = plt.subplots(1, 1, figsize=figure_size)

            if len(population_dataframe) == 0:
                ax.set(
                    xlabel=x,
                    title=f"Distribution of {x}",
                )
                return figure

            dataframe = population_dataframe.reset_index("Population")
            dataframe[x] = dataframe[x].to_numpy(dtype=float)

            if xscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported xscale: {xscale!r}. Expected 'linear' or 'log'."
                )

            if yscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported yscale: {yscale!r}. Expected 'linear' or 'log'."
                )

            valid_mask = np.isfinite(dataframe[x])

            if xscale == "log":
                valid_mask &= dataframe[x] > 0

            dataframe = dataframe.loc[valid_mask].copy()

            if dataframe.empty:
                raise ValueError("No valid data points remain after scale filtering.")

            if scale_by_concentration:
                population_weight_map = self._get_population_weight_map(
                    filter_population=filter_population
                )
                dataframe["Weight"] = dataframe["Population"].map(population_weight_map)
            else:
                dataframe["Weight"] = 1.0

            if scale_by_bin:
                if binrange is None:
                    minimum_value = dataframe[x].min()
                    maximum_value = dataframe[x].max()
                else:
                    minimum_value, maximum_value = binrange

                if isinstance(bins, int):
                    bin_edges = np.linspace(minimum_value, maximum_value, bins + 1)
                else:
                    bin_edges = np.asarray(bins)

                bin_width = np.diff(bin_edges)[0]
                dataframe["Weight"] = dataframe["Weight"] / bin_width

            hist_bins = bins

            if isinstance(bins, int):
                hist_bins = self._get_marginal_bins(
                    dataframe[x].to_numpy(dtype=float),
                    xscale,
                    bin_count=bins,
                )

            if isinstance(hist_bins, np.ndarray):
                hist_bins = hist_bins.tolist()

            histplot_kwargs = {}

            if scale_by_concentration or scale_by_bin:
                histplot_kwargs["weights"] = dataframe["Weight"]

            sns.histplot(
                data=dataframe,
                x=x,
                ax=ax,
                kde=kde,
                bins=hist_bins,
                hue="Population",
                color=color,
                binrange=binrange,
                common_norm=common_norm,
                common_bins=common_bins,
                edgecolor="black",
                linewidth=1.0,
                **histplot_kwargs,
            )

            x_label = self._get_axis_label(column_name=x, target_units=target_units)

            if scale_by_concentration and not scale_by_bin:
                y_label = "particle per milliliter"
            elif scale_by_concentration and scale_by_bin:
                x_unit = target_units.get(x, None)

                if x_unit is None:
                    y_label = "particle / (milliliter * bin)"
                else:
                    y_label = f"Particle (mL {x_unit:~P})$^{{-1}}$"
            else:
                y_label = "Counts"

            ax.set_xlabel(xlabel or x_label)
            ax.set_ylabel(ylabel or y_label)
            ax.set_title(title or f"Distribution of {x}")
            ax.set_xscale(xscale)
            ax.set_yscale(yscale)

            if xlim is not None:
                ax.set_xlim(xlim)

            if ylim is not None:
                ax.set_ylim(ylim)

            if save_as is not None:
                figure.savefig(save_as)

            return figure

    def plot_2d(
        self,
        x: str,
        y: str,
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
        filter_population: Optional[List[str]] = None,
    ) -> plt.Figure:
        """Plot a 2D population distribution with marginal histograms.

        Parameters
        ----------
        x, y : str
            Column names plotted on the joint axes.
        alpha : float, default=0.8
            Scatter marker transparency.
        xscale, yscale : {"linear", "log"}, default="linear"
            Axis scales used for the joint and marginal axes.
        marginal_nbins : int, default=40
            Number of bins used for both marginal histograms.
        figure_size : tuple[float, float], default=(6, 6)
            Figure size in inches.
        save_as : str | None, optional
            Optional output path used to save the figure.
        title, xlabel, ylabel : str | None, optional
            Optional explicit labels overriding the defaults.
        xlim, ylim : tuple[float, float] | None, optional
            Optional limits applied to the joint axis and mirrored onto the
            matching marginal axis.
        filter_population : list[str] | None, optional
            Optional subset of populations to include.

        Returns
        -------
        matplotlib.figure.Figure
            Generated joint scatter figure.

        Raises
        ------
        ValueError
            If invalid axis scales are provided or no valid data remain after
            filtering for the requested scales.
        """
        with plt.style.context(MPSPlots.styles.scientific):
            population_dataframe, target_units = self._build_dataframe_and_units(
                filter_population=filter_population
            )

            dataframe = population_dataframe.reset_index()

            if xscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported xscale: {xscale!r}. Expected 'linear' or 'log'."
                )

            if yscale not in {"linear", "log"}:
                raise ValueError(
                    f"Unsupported yscale: {yscale!r}. Expected 'linear' or 'log'."
                )

            valid_mask = np.isfinite(dataframe[x]) & np.isfinite(dataframe[y])

            if xscale == "log":
                valid_mask &= dataframe[x] > 0

            if yscale == "log":
                valid_mask &= dataframe[y] > 0

            dataframe = dataframe.loc[valid_mask].copy()

            if dataframe.empty:
                raise ValueError("No valid data points remain after scale filtering.")

            if marginal_nbins < 1:
                raise ValueError("marginal_nbins must be a positive integer.")

            x_bins = self._get_marginal_bins(
                dataframe[x].to_numpy(dtype=float),
                xscale,
                bin_count=marginal_nbins,
            )
            y_bins = self._get_marginal_bins(
                dataframe[y].to_numpy(dtype=float),
                yscale,
                bin_count=marginal_nbins,
            )

            grid = sns.JointGrid(
                data=dataframe,
                x=x,
                y=y,
            )
            grid.figure.set_size_inches(*figure_size)

            sns.scatterplot(
                data=dataframe,
                x=x,
                y=y,
                hue="Population",
                ax=grid.ax_joint,
                alpha=alpha,
            )

            sns.histplot(
                data=dataframe,
                x=x,
                hue="Population",
                ax=grid.ax_marg_x,
                bins=x_bins,
                legend=False,
                edgecolor="black",
                linewidth=1.0,
            )

            sns.histplot(
                data=dataframe,
                y=y,
                hue="Population",
                ax=grid.ax_marg_y,
                bins=y_bins,
                legend=False,
                edgecolor="black",
                linewidth=1.0,
            )

            grid.ax_joint.set_xlabel(
                xlabel or self._get_axis_label(column_name=x, target_units=target_units)
            )
            grid.ax_joint.set_ylabel(
                ylabel or self._get_axis_label(column_name=y, target_units=target_units)
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

            if save_as is not None:
                grid.figure.savefig(save_as)

            return grid.figure

    def plot_3d(
        self,
        x: str,
        y: str,
        z: str,
        hue: str = "Population",
        alpha: float = 0.8,
        filter_population: Optional[List[str]] = None,
    ) -> plt.Figure:
        """Plot a 3D population scatter distribution.

        Parameters
        ----------
        x, y, z : str
            Column names plotted on the 3D axes.
        hue : str, default="Population"
            Grouping column used to split the concatenated dataframe before
            plotting.
        alpha : float, default=0.8
            Scatter marker transparency.
        filter_population : list[str] | None, optional
            Optional subset of populations to include.

        Returns
        -------
        matplotlib.figure.Figure
            Generated 3D scatter figure.
        """
        with plt.style.context(MPSPlots.styles.scientific):
            population_dataframe, target_units = self._build_dataframe_and_units(
                filter_population=filter_population
            )

            dataframe = population_dataframe.reset_index()

            figure = plt.figure()
            ax = figure.add_subplot(111, projection="3d")

            for population_name, group in dataframe.groupby(hue):
                ax.scatter(
                    group[x].to_numpy(dtype=float),
                    group[y].to_numpy(dtype=float),
                    group[z].to_numpy(dtype=float),
                    label=population_name,
                    alpha=alpha,
                )

            ax.set_xlabel(
                self._get_axis_label(column_name=x, target_units=target_units),
                labelpad=20,
            )
            ax.set_ylabel(
                self._get_axis_label(column_name=y, target_units=target_units),
                labelpad=20,
            )
            ax.set_zlabel(
                self._get_axis_label(column_name=z, target_units=target_units),
                labelpad=20,
            )
            ax.set_title("Scatterer Sampling Distribution")

            return figure

    def _add_explicit_model_to_ax(
        self,
        events: PopulationEvents,
        ax,
        color,
        time_units: str = "second",
    ) -> None:
        """Draw explicit event timestamps as vertical markers.

        Parameters
        ----------
        events : PopulationEvents
            Event block generated by an explicit sampling model.
        ax : matplotlib.axes.Axes
            Target axis.
        color : Any
            Matplotlib-compatible color for the event markers.
        time_units : str, default="second"
            Units used to display the time axis.
        """
        if events.empty:
            return

        time_values = events.get_quantity("Time")

        if not hasattr(time_values, "to"):
            raise ValueError("Column 'Time' is not unit aware.")

        time_values = time_values.to(time_units)

        ax.vlines(
            time_values,
            ymin=0,
            ymax=1,
            transform=ax.get_xaxis_transform(),
            label=events.population.name,
            color=color,
        )

    def _add_gamma_model_to_ax(
        self,
        events: PopulationEvents,
        ax,
        color,
        time_units: str = "second",
    ) -> None:
        """Draw a gamma-model population trace on an existing axis.

        Parameters
        ----------
        events : PopulationEvents
            Event block containing aggregated gamma-model metadata traces.
        ax : matplotlib.axes.Axes
            Target axis.
        color : Any
            Matplotlib-compatible fill color.
        time_units : str, default="second"
            Units used to display the time axis.
        """
        ax.fill_between(
            x=events.metadata["TimeTrace"].to(time_units),
            y1=0,
            y2=events.metadata["ParticleTrace"],
            label=events.population.name,
            color=color,
            alpha=0.5,
        )
