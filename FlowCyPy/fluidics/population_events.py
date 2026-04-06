#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any

from FlowCyPy.sub_frames.events import EventDataFrame


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
    dataframe : EventDataFrame
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

    dataframe: EventDataFrame
    population: object
    sampling_method: object
    name: str
    scatterer_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.dataframe.scatterer_type = self.scatterer_type

        if "units" not in self.dataframe.attrs:
            self.dataframe.attrs["units"] = {}

    def __len__(self) -> int:
        """
        Return the number of stored events.

        Returns
        -------
        int
            Number of rows in the underlying dataframe.
        """
        return len(self.dataframe)

    def __getitem__(self, key: str):
        """
        Return one dataframe column.

        Parameters
        ----------
        key : str
            Column name.

        Returns
        -------
        Any
            Requested column. If the column has a registered unit, a quantity is returned.
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

    def get_quantity(self, column_name: str):
        """
        Return the specified column as a quantity.

        Parameters
        ----------
        column_name : str
            Target column name.

        Returns
        -------
        pint.Quantity or numpy.ndarray
            Column values with units if the column is unit aware.
        """
        return self.dataframe.get_quantity(column_name)

    def set_quantity_column(self, column_name: str, value) -> None:
        """
        Store a quantity column in the underlying unit aware dataframe.

        Parameters
        ----------
        column_name : str
            Name of the target column.
        value : pint.Quantity
            Quantity to store.
        """
        self.dataframe.set_column(column_name=column_name, values=value)

    def to_dataframe(self, include_metadata_in_attrs: bool = True) -> EventDataFrame:
        """
        Export this event block as a standalone dataframe.

        Parameters
        ----------
        include_metadata_in_attrs : bool, default=True
            Whether to copy metadata into ``DataFrame.attrs`` on export.

        Returns
        -------
        EventDataFrame
            Exported dataframe copy.
        """
        dataframe = self.dataframe.copy(deep=True)
        dataframe.attrs = {
            key: value.copy() if isinstance(value, dict) else value
            for key, value in self.dataframe.attrs.items()
        }

        dataframe.scatterer_type = self.scatterer_type
        dataframe.attrs["Name"] = self.name
        dataframe.attrs["PopulationType"] = self.scatterer_type
        dataframe.attrs["ScattererType"] = self.scatterer_type
        dataframe.attrs["SamplingMethod"] = self.sampling_method.__class__.__name__

        if include_metadata_in_attrs:
            for key, value in self.metadata.items():
                dataframe.attrs[key] = value

        return dataframe
