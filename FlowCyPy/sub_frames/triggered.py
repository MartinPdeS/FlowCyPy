# -*- coding: utf-8 -*-
from typing import List, Mapping

import matplotlib.pyplot as plt
from MPSPlots import helper
import pandas as pd

from FlowCyPy.sub_frames.base import BaseSubFrame


class TriggerDataFrame(BaseSubFrame):
    """
    DataFrame subclass for triggered analog acquisition data.
    """

    def __init__(self, dataframe: pd.DataFrame):
        super().__init__(dataframe)

    @property
    def detector_names(self) -> List[str]:
        """
        Return detector column names.
        """
        return [col for col in self.columns if col != "Time"]

    def __finalize__(self, other, method=..., **kwargs):
        """
        Finalize the DataFrame after operations, preserving scatterer attributes.
        """
        output = super().__finalize__(other, method, **kwargs)

        return output

    @classmethod
    def _construct_from_segment_dict(
        cls,
        segment_dict: Mapping[object, Mapping[str, object]],
    ) -> "TriggerDataFrame":
        """
        Convert a nested segment dictionary into a TriggerDataFrame.

        Expected input format
        ---------------------
        {
            0: {
                "Time": time_values_for_segment_0,
                "DetectorA": signal_values_for_segment_0,
                "DetectorB": signal_values_for_segment_0,
            },
            1: {
                "Time": time_values_for_segment_1,
                "DetectorA": signal_values_for_segment_1,
                "DetectorB": signal_values_for_segment_1,
            },
        }

        Each segment dictionary must contain a ``"Time"`` entry and one or more
        detector entries. All arrays inside a given segment must have the same
        length. All segments must share the same detector names.

        Parameters
        ----------
        segment_dict : Mapping[object, Mapping[str, object]]
            Nested mapping from segment identifier to a dictionary containing
            ``"Time"`` and detector signals.

        Returns
        -------
        TriggerDataFrame
            Triggered acquisition dataframe indexed by ``SegmentID``.
        """
        if len(segment_dict) == 0:
            raise ValueError("segment_dict must not be empty.")

        rows = []
        expected_detector_names = None

        for raw_segment_id, signal_dict in segment_dict.items():
            if "Time" not in signal_dict:
                raise ValueError(
                    f"Segment '{raw_segment_id}' must contain a 'Time' entry."
                )

            if len(signal_dict) < 2:
                raise ValueError(
                    f"Segment '{raw_segment_id}' must contain 'Time' and at least one detector signal."
                )

            detector_names = [key for key in signal_dict.keys() if key != "Time"]

            if expected_detector_names is None:
                expected_detector_names = detector_names
            elif detector_names != expected_detector_names:
                raise ValueError(
                    f"Segment '{raw_segment_id}' does not have the same detector names "
                    f"as previous segments. Expected {expected_detector_names}, got {detector_names}."
                )

            time_values = signal_dict["Time"]
            expected_length = len(time_values)

            for detector_name in detector_names:
                detector_signal = signal_dict[detector_name]

                if len(detector_signal) != expected_length:
                    raise ValueError(
                        f"Segment '{raw_segment_id}', signal '{detector_name}' has length "
                        f"{len(detector_signal)} but 'Time' has length {expected_length}."
                    )

            for sample_index in range(expected_length):
                row = {
                    "SegmentID": raw_segment_id,
                    "Time": time_values[sample_index],
                }

                for detector_name in detector_names:
                    row[detector_name] = signal_dict[detector_name][sample_index]

                rows.append(row)

        trigger_dataframe = pd.DataFrame(rows)

        trigger_dataframe["Time"] = pd.Series(
            trigger_dataframe["Time"],
            dtype="pint[second]",
        )

        for detector_name in expected_detector_names:
            trigger_dataframe[detector_name] = pd.Series(
                trigger_dataframe[detector_name],
            )

        trigger_dataframe = trigger_dataframe.set_index("SegmentID")
        trigger_dataframe.index.name = "SegmentID"

        trigger_dataframe = cls(trigger_dataframe)

        return trigger_dataframe

    @property
    def detector_names(self) -> List[str]:
        """
        Return detector column names.
        """
        return [col for col in self.columns if col not in ["Time", "SegmentID"]]

    @property
    def n_segment(self) -> int:
        """
        Return the number of unique trigger segments.
        """
        return len(self.index.get_level_values("SegmentID").unique())

    @helper.post_mpl_plot
    def plot(self) -> None:
        """
        Plot acquisition data for each detector.

        Returns
        -------
        plt.Figure
            Figure containing the detector plots.
        """
        self.normalize_units(signal_units="max", time_units="max")

        figure, axes = self._get_axes_dict()
        self._add_to_axes(axes=axes)

        return figure

    def _get_axes_dict(self) -> dict[str, plt.Axes]:
        """
        Create one matplotlib axis per detector.

        Returns
        -------
        tuple[plt.Figure, dict[str, plt.Axes]]
            Figure and mapping from detector names to axes.
        """
        n_plots = len(self.detector_names)

        figure, axes_array = plt.subplots(
            nrows=n_plots,
            sharex=True,
            sharey=True,
            squeeze=False,
        )

        axes = {name: ax for name, ax in zip(self.detector_names, axes_array.flatten())}

        for _, ax in axes.items():
            ax.yaxis.tick_right()

        for detector_name in self.detector_names:
            ax = axes[detector_name]
            ax.set_ylabel(
                rf"{detector_name} [{self.signal_units._repr_latex_()}]",
                labelpad=20,
            )

        ax.set_xlabel(rf"Time [{self.time_units._repr_latex_()}]")

        return figure, axes

    def _add_to_axes(self, axes: dict, time_units: object) -> None:
        """
        Plot triggered analog signal data for each detector and highlight each segment.
        """
        # time_units = self["Time"].max().to_compact().units

        self["Time"] = self["Time"].pint.to(time_units)

        for detector_name in self.detector_names:
            ax = axes[detector_name]

            for segment_id, group in self.groupby("SegmentID"):
                time = group["Time"]

                signal = group[detector_name]

                start_time = time.min()
                end_time = time.max()

                color = plt.cm.tab10(int(segment_id) % 10)

                ax.axvspan(start_time, end_time, facecolor=color, alpha=0.3)
                ax.step(time, signal, where="mid", color="black", linestyle="-")
