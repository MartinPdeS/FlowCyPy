# -*- coding: utf-8 -*-
from typing import List, Mapping

import matplotlib.pyplot as plt
from MPSPlots import helper
import pandas as pd


class TriggerDataFrame(pd.DataFrame):
    """
    DataFrame subclass for triggered analog acquisition data.

    Notes
    -----
    This class does not use pint-pandas.
    Time values are stored as plain numeric magnitudes in the ``"Time"`` column.
    Their unit is stored in:

        self.attrs["units"]["Time"]

    The input ``data_dict["Time"]`` is expected to be a Pint quantity-like object
    exposing both ``.magnitude`` and ``.units``.
    """

    @property
    def _constructor(self) -> type:
        """
        Ensure pandas operations return instances of TriggerDataFrame.
        """
        return self.__class__

    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the TriggerDataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Input dataframe.
        """
        super().__init__(dataframe)

        if "units" not in self.attrs:
            self.attrs["units"] = {}

    def __finalize__(self, other, method=None, **kwargs):
        """
        Finalize the DataFrame after pandas operations and preserve metadata.

        Parameters
        ----------
        other : object
            Source object used by pandas during dataframe propagation.
        method : str, optional
            Finalization method name.
        **kwargs
            Additional keyword arguments forwarded by pandas.

        Returns
        -------
        TriggerDataFrame
            Finalized dataframe with copied unit metadata.
        """
        output = super().__finalize__(other, method=method, **kwargs)

        if hasattr(other, "attrs"):
            output.attrs["units"] = dict(other.attrs.get("units", {}))

        return output

    @classmethod
    def _construct_from_flat_dict(
        cls,
        data_dict: Mapping[str, object],
    ) -> "TriggerDataFrame":
        """
        Convert a flat segmented dictionary into a TriggerDataFrame.

        Expected input format
        ---------------------
        {
            "segment_id": integer_array,
            "Time": time_quantity_array,
            "DetectorA": signal_values,
            "DetectorB": signal_values,
        }

        Each key contains a one dimensional array. All arrays must have the same
        length. The ``"segment_id"`` key identifies which trigger segment each
        sample belongs to.

        The time unit is read from:

            data_dict["Time"].units

        and stored in:

            dataframe.attrs["units"]["Time"]

        Parameters
        ----------
        data_dict : Mapping[str, object]
            Flat mapping containing ``"segment_id"``, ``"Time"``, and one or more
            detector signals.

        Returns
        -------
        TriggerDataFrame
            Triggered acquisition dataframe indexed by ``SegmentID``.
        """
        if len(data_dict) == 0:
            raise ValueError("data_dict must not be empty.")

        if "segment_id" not in data_dict:
            raise ValueError("data_dict must contain a 'segment_id' entry.")

        if "Time" not in data_dict:
            raise ValueError("data_dict must contain a 'Time' entry.")

        if not hasattr(data_dict["Time"], "units"):
            raise ValueError("data_dict['Time'] must have a 'units' attribute.")

        if not hasattr(data_dict["Time"], "magnitude"):
            raise ValueError("data_dict['Time'] must have a 'magnitude' attribute.")

        detector_names = [
            key for key in data_dict.keys() if key not in ["segment_id", "Time"]
        ]

        if len(detector_names) == 0:
            raise ValueError(
                "data_dict must contain at least one detector signal in addition to 'segment_id' and 'Time'."
            )

        segment_ids = data_dict["segment_id"]
        time_quantity = data_dict["Time"]

        expected_length = len(segment_ids)

        if len(time_quantity) != expected_length:
            raise ValueError(
                f"'Time' has length {len(time_quantity)} but 'segment_id' has length {expected_length}."
            )

        for detector_name in detector_names:
            detector_signal = data_dict[detector_name]

            if len(detector_signal) != expected_length:
                raise ValueError(
                    f"Signal '{detector_name}' has length {len(detector_signal)} "
                    f"but 'segment_id' has length {expected_length}."
                )

        trigger_dataframe = pd.DataFrame(
            {
                "SegmentID": segment_ids,
                "Time": time_quantity.magnitude,
                **{
                    detector_name: data_dict[detector_name]
                    for detector_name in detector_names
                },
            }
        )

        trigger_dataframe["Time"] = pd.Series(trigger_dataframe["Time"])

        for detector_name in detector_names:
            trigger_dataframe[detector_name] = pd.Series(
                trigger_dataframe[detector_name]
            )

        trigger_dataframe = trigger_dataframe.set_index("SegmentID")
        trigger_dataframe.index.name = "SegmentID"

        trigger_dataframe = cls(trigger_dataframe)
        trigger_dataframe.attrs["units"]["Time"] = time_quantity.units

        return trigger_dataframe

    @property
    def detector_names(self) -> List[str]:
        """
        Return detector column names.
        """
        return [column for column in self.columns if column != "Time"]

    @property
    def n_segment(self) -> int:
        """
        Return the number of unique trigger segments.
        """
        return len(self.index.unique())

    def get_units(self, column: str):
        """
        Return the stored unit associated with a column.

        Parameters
        ----------
        column : str
            Column name for which unit metadata should be retrieved.

        Returns
        -------
        object
            Stored unit object.

        Raises
        ------
        KeyError
            If no unit metadata exists for the requested column.
        """
        if "units" not in self.attrs:
            raise KeyError("No unit metadata is stored in this TriggerDataFrame.")

        if column not in self.attrs["units"]:
            raise KeyError(f"No unit metadata is stored for column '{column}'.")

        return self.attrs["units"][column]

    def to_compact(self) -> "TriggerDataFrame":
        """
        Rescale the ``Time`` column to a compact unit and update unit metadata.

        This reproduces the behavior conceptually equivalent to:

            self["Time"] = self["Time"].to(self["Time"].max().to_compact().units)

        except that the dataframe stores only plain numeric magnitudes, while the
        unit is stored separately in ``self.attrs["units"]["Time"]``.

        Returns
        -------
        TriggerDataFrame
            The same dataframe instance, modified in place.
        """
        time_unit = self.get_units("Time")
        maximum_time_quantity = self["Time"].max() * time_unit
        compact_unit = maximum_time_quantity.to_compact().units

        self["Time"] = (self["Time"].to_numpy() * time_unit).to(compact_unit).magnitude
        self.attrs["units"]["Time"] = compact_unit

        return self

    @helper.post_mpl_plot
    def plot(self) -> plt.Figure:
        """
        Plot acquisition data for each detector.

        Returns
        -------
        plt.Figure
            Figure containing the detector plots.
        """
        self.to_compact()

        figure, axes = self._get_axes_dict()
        self._add_to_axes(axes=axes)

        return figure

    def _get_axes_dict(self) -> dict[str, plt.Axes]:
        """
        Create one matplotlib axis per detector.

        Returns
        -------
        dict[str, plt.Axes]
            Mapping from detector names to matplotlib axes.
        """
        n_plots = len(self.detector_names)

        figure, axes_array = plt.subplots(
            nrows=n_plots,
            sharex=True,
            sharey=True,
            squeeze=False,
        )

        axes = {name: ax for name, ax in zip(self.detector_names, axes_array.flatten())}

        for ax in axes.values():
            ax.yaxis.tick_right()

        for detector_name in self.detector_names:
            ax = axes[detector_name]
            ax.set_ylabel(detector_name, labelpad=20)

        ax.set_xlabel(f"Time [{self.get_units('Time')}]")

        return figure, axes

    def _add_to_axes(self, axes: dict[str, plt.Axes]) -> None:
        """
        Plot triggered analog signal data for each detector and highlight each segment.

        Parameters
        ----------
        axes : dict[str, plt.Axes]
            Mapping from detector names to axes.
        """
        for detector_name in self.detector_names:
            ax = axes[detector_name]

            for segment_id, group in self.groupby(level="SegmentID"):
                time = group["Time"]
                signal = group[detector_name]

                start_time = time.min()
                end_time = time.max()

                color = plt.cm.tab10(int(segment_id) % 10)

                ax.axvspan(start_time, end_time, facecolor=color, alpha=0.3)
                ax.step(time, signal, where="mid", color="black", linestyle="-")
