# -*- coding: utf-8 -*-
from typing import List, Mapping

import matplotlib.pyplot as plt
from MPSPlots import helper
import pandas as pd
from TypedUnit import Time, Voltage, ureg


class AcquisitionDataFrame(pd.DataFrame):
    """
    DataFrame subclass for continuous analog acquisition data.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of PeakDataFrame."""
        return self.__class__

    def __init__(self, dataframe: pd.DataFrame):
        super().__init__(dataframe)

    @classmethod
    def _construct_from_signal_dict(
        cls,
        signal_dict: Mapping[str, object],
    ) -> "AcquisitionDataFrame":
        """
        Convert a dictionary of time and detector signals into a pandas DataFrame.

        The input dictionary must contain a ``"Time"`` entry and one or more detector
        entries. The ``"Time"`` entry is stored as a Pint time series in seconds.
        All other entries are interpreted as detector signals and stored as Pint
        voltage series.

        Parameters
        ----------
        signal_dict : Mapping[str, object]
            Dictionary containing the acquisition data. It must contain the key
            ``"Time"`` and all arrays must have the same length.

        Returns
        -------
        AcquisitionDataFrame
            A DataFrame containing the time axis and detector signals.
        """
        cls.raw_data = signal_dict
        if "Time" not in signal_dict:
            raise ValueError("signal_dict must contain a 'Time' entry.")

        if len(signal_dict) < 2:
            raise ValueError(
                "signal_dict must contain at least 'Time' and one detector signal."
            )

        time_values = signal_dict["Time"]
        expected_length = len(time_values)

        signal_dataframe = pd.DataFrame()

        signal_dataframe["Time"] = pd.Series(
            time_values,
            dtype="pint[second]",
        )

        for detector_name, detector_signal in signal_dict.items():
            if detector_name == "Time":
                continue

            if len(detector_signal) != expected_length:
                raise ValueError(
                    f"Signal '{detector_name}' has length {len(detector_signal)} but "
                    f"'Time' has length {expected_length}."
                )

            signal_dataframe[detector_name] = pd.Series(
                detector_signal,
                dtype="pint[volt]",
            )

        signal_dataframe = cls(signal_dataframe)
        signal_dataframe.normalize_units(signal_units="SI", time_units="SI")

        return signal_dataframe

    def normalize_units(
        self, signal_units: Voltage | str = None, time_units: Time | str = None
    ) -> None:
        """
        Normalize the DataFrame's signal and time columns to specified units.

        Parameters
        ----------
        signal_units : Voltage | str
            The units to which the signal columns should be normalized.
        time_units : Time | str
            The units to which the time column should be normalized.
        """
        name = f"{self.detector_names[0]}"

        if signal_units == "max":
            if self[name].size == 0:
                signal_units = 0 * self[name].pint.units
            else:
                signal_units = self[name].max().to_compact().units

        if signal_units == "SI":
            if self[name].pint.units.dimensionality == ureg.bit_bins.dimensionality:
                signal_units = ureg.bit_bins
            else:
                signal_units = ureg.volt

        if time_units == "max":
            if self["Time"].size == 0:
                time_units = 0 * ureg.second
            else:
                time_units = self["Time"].max().to_compact().units

        if time_units == "SI":
            time_units = ureg.second

        for columns in self.columns:
            if columns == "Time" and time_units is not None:
                self.time_units = time_units
                self[columns] = self[columns].pint.to(time_units)

            if columns != "Time" and signal_units is not None:
                self.signal_units = signal_units
                self[columns] = self[columns].pint.to(signal_units)

        return self

    def __finalize__(self, other, method=..., **kwargs):
        """
        Finalize the DataFrame after operations, preserving scatterer attributes.
        """
        output = super().__finalize__(other, method, **kwargs)

        return output

    @property
    def detector_names(self) -> List[str]:
        """
        Return detector column names.
        """
        return [col for col in self.columns if col != "Time"]

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

    def _add_to_axes(self, axes: dict) -> None:
        """
        Plot analog signal data for each detector.
        """
        for detector_name in self.detector_names:
            ax = axes[detector_name]

            time = self["Time"].pint.to(self.time_units).pint.quantity
            signal = self[detector_name]

            if hasattr(signal, "pint"):
                signal = signal.pint.to(self.signal_units).pint.quantity

            ax.plot(time, signal, label="Analog Signal", linestyle="-", color="black")
