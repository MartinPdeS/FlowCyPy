#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

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
    population_type : str
        Concrete class name of the population.
    scatterer_type : str
        Scatterer type label associated with the population.
    metadata : dict[str, Any], optional
        Additional population level metadata.
    """

    dataframe: pd.DataFrame
    population: object
    sampling_method: object
    name: str
    population_type: str
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
            population_type=self.population_type,
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
        dataframe.attrs["PopulationType"] = self.population_type
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
