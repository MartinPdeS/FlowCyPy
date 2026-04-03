#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from typing import List, Optional, Union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from MPSPlots import helper
import seaborn as sns
import pint_pandas

from .populations import ExplicitModel, GammaModel

import pandas as pd
from pint_pandas import PintArray


@dataclass
class PopulationEvents:
    """
    Structured container storing all event level data for one population.

    This class is the canonical internal event representation used by the
    simulation pipeline. It separates three categories of information:

    1. Event level tabular data
       Stored in ``dataframe``. These are per event quantities such as time,
       position, velocity, and detector specific amplitudes.

    2. Semantic simulation objects
       Stored explicitly in ``population`` and ``sampling_method``.

    3. Population level metadata
       Stored in ``metadata``. These are scalar or aggregate quantities such as
       mean velocity, expected occupancy per time bin, or diagnostic traces.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Event level table.
    population : object
        Population object that generated the events.
    sampling_method : object
        Sampling method used to generate the event block.
    name : str
        Population name.
    scatterer_type : str
        Scatterer type label associated with the population.
    metadata : dict[str, Any], optional
        Additional population level metadata.
    """

    dataframe: pd.DataFrame
    population: object
    sampling_method: object
    name: str
    scatterer_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """
        Return the number of stored events.

        Returns
        -------
        int
            Number of rows in the underlying dataframe.
        """
        return len(self.dataframe)

    def __getitem__(self, key: str) -> pd.Series:
        """
        Return one dataframe column.

        Parameters
        ----------
        key : str
            Column name.

        Returns
        -------
        pandas.Series
            Requested column.
        """
        return self.dataframe[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Assign one dataframe column.

        Parameters
        ----------
        key : str
            Column name.
        value : Any
            Values to assign.
        """
        self.dataframe[key] = value

    @property
    def empty(self) -> bool:
        """
        Whether this event block is empty.

        Returns
        -------
        bool
            ``True`` if the dataframe has no rows.
        """
        return self.dataframe.empty

    @property
    def columns(self):
        """
        Return dataframe columns.

        Returns
        -------
        pandas.Index
            Column index.
        """
        return self.dataframe.columns

    def copy(self) -> "PopulationEvents":
        """
        Return a deep copy of this event block.

        Returns
        -------
        PopulationEvents
            Copied event container.
        """
        return PopulationEvents(
            dataframe=self.dataframe.copy(deep=True),
            population=self.population,
            sampling_method=self.sampling_method,
            name=self.name,
            scatterer_type=self.scatterer_type,
            metadata=dict(self.metadata),
        )

    def get_quantity(self, column_name: str):
        """
        Return a Pint quantity stored in a Pint backed column.

        Parameters
        ----------
        column_name : str
            Target column name.

        Returns
        -------
        pint.Quantity
            Quantity stored in the specified column.
        """
        return self.dataframe[column_name].pint.quantity

    def set_quantity_column(self, column_name: str, value) -> None:
        """
        Store a Pint quantity in the dataframe using PintArray.

        Parameters
        ----------
        column_name : str
            Name of the target column.
        value : pint.Quantity
            Quantity to store.
        """
        self.dataframe[column_name] = PintArray(value, dtype=value.units)

    def to_dataframe(self, include_metadata_in_attrs: bool = True) -> pd.DataFrame:
        """
        Export this event block as a standalone dataframe.

        Parameters
        ----------
        include_metadata_in_attrs : bool, default=True
            Whether to copy metadata into ``DataFrame.attrs`` on export.

        Returns
        -------
        pandas.DataFrame
            Exported dataframe copy.
        """
        dataframe = self.dataframe.copy(deep=True)

        dataframe.attrs["Name"] = self.name
        dataframe.attrs["PopulationType"] = self.scatterer_type
        dataframe.attrs["ScattererType"] = self.scatterer_type
        dataframe.attrs["SamplingMethod"] = self.sampling_method.__class__.__name__

        if include_metadata_in_attrs:
            for key, value in self.metadata.items():
                dataframe.attrs[key] = value

        return dataframe


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
        """
        Iterate over stored event blocks.

        Returns
        -------
        Iterator[PopulationEvents]
            Iterator over the collection.
        """
        return iter(self.events_list)

    def __len__(self) -> int:
        """
        Return the number of population blocks.

        Returns
        -------
        int
            Number of stored blocks.
        """
        return len(self.events_list)

    def __getitem__(self, index: int) -> PopulationEvents:
        """
        Return one population block by index.

        Parameters
        ----------
        index : int
            Block index.

        Returns
        -------
        PopulationEvents
            Requested block.
        """
        return self.events_list[index]

    def append(self, events: PopulationEvents) -> None:
        """
        Append one population event block.

        Parameters
        ----------
        events : PopulationEvents
            Event block to append.
        """
        self.events_list.append(events)

    @property
    def empty(self) -> bool:
        """
        Whether the whole collection is empty.

        Returns
        -------
        bool
            ``True`` if every population block is empty.
        """
        return all(events.empty for events in self.events_list)

    def copy(self) -> "EventCollection":
        """
        Return a deep copy of the full event collection.

        Returns
        -------
        EventCollection
            Copied event collection.
        """
        return EventCollection(
            events_list=[events.copy() for events in self.events_list]
        )

    def to_dataframes(
        self, include_metadata_in_attrs: bool = True
    ) -> list[pd.DataFrame]:
        """
        Export all event blocks as standalone dataframes.

        Parameters
        ----------
        include_metadata_in_attrs : bool, default=True
            Whether metadata should be copied into dataframe attrs.

        Returns
        -------
        list[pandas.DataFrame]
            Exported dataframe copies.
        """
        return [
            events.to_dataframe(include_metadata_in_attrs=include_metadata_in_attrs)
            for events in self.events_list
        ]

    def get_population_events(self, population_name: str) -> Optional[PopulationEvents]:
        """
        Return one event block by population name.

        Parameters
        ----------
        population_name : str
            Population name.

        Returns
        -------
        PopulationEvents or None
            Matching block if found, otherwise ``None``.
        """
        for events in self.events_list:
            if events.name == population_name:
                return events

        return None

    def _add_to_ax(
        self, ax, time_units: str, filter_population: Optional[List[str]] = None
    ) -> None:
        """
        Internal method to add population events to a matplotlib axis.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to add the events to.
        filter_population : List[str], optional
            List of population names to include. If None, includes all populations.
        time_units : str, optional
            Units for the time axis (default is 'second').
        """
        palette = "tab10"
        color_mapping = dict(
            zip(
                [event.population.name for event in self],
                sns.color_palette(palette, len(self)),
            )
        )

        for events in self.events_list:
            if (
                filter_population is not None
                and events.population.name not in filter_population
            ):
                continue
            if isinstance(events.sampling_method, ExplicitModel):
                self._add_explicit_model_to_ax(
                    events,
                    ax,
                    color=color_mapping[events.population.name],
                    time_units=time_units,
                )
            if isinstance(events.sampling_method, GammaModel):
                self._add_gamma_model_to_ax(
                    events,
                    ax,
                    color=color_mapping[events.population.name],
                    time_units=time_units,
                )

        ax.set_xlabel(f"Time [{time_units}]")
        handles, labels = ax.get_legend_handles_labels()

        if handles:
            ax.legend()

    def get_concatenated_dataframe(
        self, filter_population: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Concatenate all non empty population event DataFrames into one MultiIndex DataFrame.

        Parameters
        ----------
        filter_population : Optional[List[str]], optional
            List of population names to include. If None, all populations are included.

        Returns
        -------
        pd.DataFrame
            Concatenated DataFrame with a first index level named ``Population``.
        """
        selected_events = []

        for events in self.events_list:
            if events.empty:
                continue

            if filter_population is not None and events.name not in filter_population:
                continue

            dataframe = events.dataframe.copy(deep=True)

            for column_name in dataframe.columns:
                series = dataframe[column_name]

                if not hasattr(series, "pint"):
                    continue

                try:
                    quantity = series.pint.quantity.to_reduced_units()
                    dataframe[column_name] = pint_pandas.PintArray(
                        quantity.magnitude,
                        dtype=quantity.units,
                    )
                except Exception:
                    continue

            selected_events.append((events.name, dataframe))

        if not selected_events:
            return pd.DataFrame(
                index=pd.MultiIndex(
                    levels=[[]],
                    codes=[[]],
                    names=["Population"],
                )
            )

        population_event = pd.concat(
            [dataframe for _, dataframe in selected_events],
            keys=[name for name, _ in selected_events],
            names=["Population"],
        )

        for column_name in population_event.columns:
            series = population_event[column_name]

            if not hasattr(series, "pint"):
                continue

            try:
                # base_unit = (1 * series.pint.units).to_base_units().units
                base_unit = series.pint.units

                population_event[column_name] = series.pint.to(base_unit)
            except Exception:
                continue

        return population_event

    def plot(self, x: str = None, y: str = None, z: str = None, **kwargs) -> plt.Figure:
        """
        Dispatch plotting to 2D or 3D methods based on provided kwargs.
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

    @helper.post_mpl_plot
    def plot_hist(
        self,
        x: str = "Diameter",
        kde: bool = False,
        bins: Optional[int] = 50,
        color: Optional[Union[str, dict]] = None,
        filter_population: Optional[List[str]] = None,
        binrange: Optional[tuple] = None,
        common_norm: bool = False,
        common_bins: bool = False,
        scale_by_concentration: bool = False,
        scale_by_bin: bool = False,
    ) -> plt.Figure:
        """
        Plot a population resolved histogram for a chosen variable.

        The histogram can be optionally scaled to reflect physical concentration.
        Two scaling modes are supported:

            1. particle per milliliter (default)
            2. particle per (milliliter * bin) if `scale_by_bin=True`

        Parameters
        ----------
        x : str
            Column name to plot.
        kde : bool
            Whether to overlay a kernel density estimate.
        bins : int or sequence
            Number of bins or explicit bin edges.
        color : str or dict
            Color specification.
        filter_population : list or None
            Which populations to include.
        binrange : tuple or None
            Range for the histogram.
        common_norm : bool
            Forwarded to seaborn.
        common_bins : bool
            Forwarded to seaborn.
        scale_by_concentration : bool
            Scale histogram by population level concentration.
        scale_by_bin : bool
            If True, divides weights by the bin width to display densities
            in particle/(milliliter * bin).

        Returns
        -------
        matplotlib.figure.Figure
        """

        population_event = self.get_concatenated_dataframe(filter_population)
        figure, ax = plt.subplots(1, 1)

        if len(population_event) == 0:
            ax.set(xlabel=f"{x}", title=f"Distribution of {x}")
            return figure

        # Convert to plain numeric columns
        df = population_event.reset_index("Population")

        x_units = df[x].max().to_compact().units

        df[x] = df[x].pint.to(x_units)

        df = df.pint.dequantify().droplevel("unit", axis=1)

        # ------------------------------------------------------------
        # Construct per population weights
        # ------------------------------------------------------------
        if scale_by_concentration:
            population_weight_map = {
                event.metadata["Name"]: event.metadata["ParticleCount"]
                .to("particle/milliliter")
                .magnitude
                for event in self
            }
            df["Weight"] = df["Population"].map(population_weight_map)
        else:
            df["Weight"] = 1.0

        # ------------------------------------------------------------
        # Compute bin width if user wants particle/(milliliter * bin)
        # ------------------------------------------------------------
        if scale_by_bin:
            # Determine edges
            if binrange is None:
                xmin = df[x].min()
                xmax = df[x].max()
            else:
                xmin, xmax = binrange

            if isinstance(bins, int):
                bin_edges = np.linspace(xmin, xmax, bins + 1)
            else:
                bin_edges = np.asarray(bins)

            bin_width = np.diff(bin_edges)[0]

            # Scaling population weights by bin width
            # This changes units from particle/mL to particle/(mL * bin)
            df["Weight"] = df["Weight"] / bin_width
        else:
            bin_width = None  # not used

        # ------------------------------------------------------------
        # Plot histogram
        # ------------------------------------------------------------
        sns.histplot(
            data=df,
            x=x,
            ax=ax,
            kde=kde,
            bins=bins,
            hue="Population",
            color=color,
            binrange=binrange,
            common_norm=common_norm,
            common_bins=common_bins,
            weights=df["Weight"],
        )

        # ------------------------------------------------------------
        # Axis labels
        # ------------------------------------------------------------
        if scale_by_concentration and not scale_by_bin:
            ylabel = "particle per milliliter"
        elif scale_by_concentration and scale_by_bin:
            ylabel = f"Particle (mL {x_units:~P})$^{{-1}}$"
        else:
            ylabel = "Counts"

        ax.set(
            xlabel=f"{x} [{x_units:~P}]",
            ylabel=ylabel,
            title=f"Distribution of {x}",
        )

        return figure

    @helper.post_mpl_plot
    def plot_2d(
        self,
        x: str,
        y: str,
        alpha: float = 0.8,
        bandwidth_adjust: float = 1.0,
        filter_population: Optional[List[str]] = None,
    ) -> plt.Figure:
        """
        Plots the scatterer sampling distribution using seaborn's jointplot.
        Parameters
        ----------
        x : str
            The column name for the x-axis.
        y : str
            The column name for the y-axis.
        alpha : float, optional
            The transparency level for the scatter points (default is 0.8).
        bandwidth_adjust : float, optional
            Adjustment factor for the bandwidth of the marginal distributions (default is 1.0).
        filter_population : Optional[List[str]], optional
            List of population names to include. If None, includes all populations.

        Returns
        -------
        plt.Figure
            The matplotlib Figure object containing the plot.
        """
        population_event = self.get_concatenated_dataframe(filter_population)

        grid = sns.jointplot(
            data=population_event,
            x=x,
            y=y,
            hue="Population",
            kind="scatter",
            alpha=alpha,
            marginal_kws={"bw_adjust": bandwidth_adjust},
        )

        grid.figure.suptitle("Scatterer Sampling Distribution")
        grid.ax_joint.set_xlabel(f"{x} [{population_event[x].pint.units:~P}]")
        grid.ax_joint.set_ylabel(f"{y} [{population_event[y].pint.units:~P}]")
        return grid.figure

    @helper.post_mpl_plot
    def plot_3d(
        self,
        x: str,
        y: str,
        z: str = None,
        hue: str = "Population",
        alpha: float = 0.8,
        filter_population: Optional[List[str]] = None,
    ) -> plt.Figure:
        """
        Visualize a 3D scatter plot of scatterer properties.

        Parameters
        ----------
        ax : plt.Axes
            A matplotlib 3D axis to plot on.
        x : str, optional
            Column for the x-axis (default: 'Diameter').
        y : str, optional
            Column for the y-axis (default: 'RefractiveIndex').
        z : str, optional
            Column for the z-axis (default: 'Density').
        hue : str, optional
            Column used for grouping/coloring (default: 'Population').
        alpha : float, optional
            Transparency for scatter points (default: 0.8).
        filter_population : Optional[List[str]], optional
            List of population names to include. If None, includes all populations.

        Returns
        -------
        plt.Figure
            The figure containing the 3D scatter plot.
        """
        population_event = self.get_concatenated_dataframe(filter_population)

        figure = plt.figure()
        ax = figure.add_subplot(111, projection="3d")

        # df, (x_unit, y_unit, z_unit) = self.get_sub_dataframe(x, y, z)

        for population, group in (
            population_event.pint.dequantify().astype(float).groupby(hue)
        ):
            ax.scatter(group[x], group[y], group[z], label=population, alpha=alpha)

        ax.set_xlabel(f"{x} [{population_event[x].pint.units:~P}]", labelpad=20)
        ax.set_ylabel(f"{y} [{population_event[y].pint.units:~P}]", labelpad=20)
        ax.set_zlabel(f"{z} [{population_event[z].pint.units:~P}]", labelpad=20)
        ax.set_title("Scatterer Sampling Distribution")
        return figure

    def _add_explicit_model_to_ax(
        self, events, ax, color, time_units: str = "second"
    ) -> None:
        """
        Internal method to add explicit model events to a matplotlib axis.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to add the events to.
        time_units : str, optional
            Units for the time axis (default is 'second').
        """
        if events.empty:
            return

        ax.vlines(
            events.dataframe.Time.pint.to(time_units).pint.quantity,
            ymin=0,
            ymax=1,
            transform=ax.get_xaxis_transform(),
            label=events.population.name,
            color=color,
        )

    def _add_gamma_model_to_ax(
        self, events, ax, color, time_units: str = "second"
    ) -> None:
        """
        Internal method to add gamma model events to a matplotlib axis.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to add the events to.
        time_units : str, optional
            Units for the time axis (default is 'second').
        """
        ax.fill_between(
            x=events.metadata["TimeTrace"].to(time_units),
            y1=0,
            y2=events.metadata["ParticleTrace"],
            label=events.population.name,
            color=color,
            alpha=0.5,
        )
