#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from MPSPlots import helper

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
        return iter(self.events_list)

    def __len__(self) -> int:
        return len(self.events_list)

    def __getitem__(self, index: int) -> PopulationEvents:
        return self.events_list[index]

    def append(self, events: PopulationEvents) -> None:
        self.events_list.append(events)

    @property
    def empty(self) -> bool:
        return all(events.empty for events in self.events_list)

    def copy(self) -> "EventCollection":
        return EventCollection(
            events_list=[events.copy() for events in self.events_list]
        )

    def to_dataframes(
        self,
        include_metadata_in_attrs: bool = True,
    ) -> list[EventDataFrame]:
        return [
            events.to_dataframe(include_metadata_in_attrs=include_metadata_in_attrs)
            for events in self.events_list
        ]

    def get_population_events(
        self,
        population_name: str,
    ) -> Optional[PopulationEvents]:
        for events in self.events_list:
            if events.name == population_name:
                return events

        return None

    def _get_selected_events(
        self,
        filter_population: Optional[List[str]] = None,
    ) -> list[PopulationEvents]:
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
        unit = target_units.get(column_name, None)

        if unit is None:
            return column_name

        return f"{column_name} [{unit:~P}]"

    def _get_population_weight_map(
        self,
        filter_population: Optional[List[str]] = None,
    ) -> dict[str, float]:
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
        palette = sns.color_palette("tab10", len(selected_events))

        return {
            events.population.name: color
            for events, color in zip(selected_events, palette)
        }

    def _add_to_ax(
        self,
        ax,
        time_units: str,
        filter_population: Optional[List[str]] = None,
    ) -> None:
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
        population_dataframe, target_units = self._build_dataframe_and_units(
            filter_population=filter_population
        )

        figure, ax = plt.subplots(1, 1)

        if len(population_dataframe) == 0:
            ax.set(
                xlabel=x,
                title=f"Distribution of {x}",
            )
            return figure

        dataframe = population_dataframe.reset_index("Population")
        dataframe[x] = dataframe[x].to_numpy(dtype=float)

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

        sns.histplot(
            data=dataframe,
            x=x,
            ax=ax,
            kde=kde,
            bins=bins,
            hue="Population",
            color=color,
            binrange=binrange,
            common_norm=common_norm,
            common_bins=common_bins,
            weights=dataframe["Weight"],
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

        ax.set(
            xlabel=x_label,
            ylabel=y_label,
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
        population_dataframe, target_units = self._build_dataframe_and_units(
            filter_population=filter_population
        )

        dataframe = population_dataframe.reset_index()

        grid = sns.jointplot(
            data=dataframe,
            x=x,
            y=y,
            hue="Population",
            kind="scatter",
            alpha=alpha,
            marginal_kws={"bw_adjust": bandwidth_adjust},
        )

        grid.ax_joint.set_xlabel(
            self._get_axis_label(column_name=x, target_units=target_units)
        )
        grid.ax_joint.set_ylabel(
            self._get_axis_label(column_name=y, target_units=target_units)
        )
        grid.figure.suptitle("Scatterer Sampling Distribution")

        return grid.figure

    @helper.post_mpl_plot
    def plot_3d(
        self,
        x: str,
        y: str,
        z: str,
        hue: str = "Population",
        alpha: float = 0.8,
        filter_population: Optional[List[str]] = None,
    ) -> plt.Figure:
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
        ax.fill_between(
            x=events.metadata["TimeTrace"].to(time_units),
            y1=0,
            y2=events.metadata["ParticleTrace"],
            label=events.population.name,
            color=color,
            alpha=0.5,
        )
