# -*- coding: utf-8 -*-
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import MPSPlots
import pandas as pd
import pint_pandas
import seaborn as sns
from TypedUnit import Dimensionless, Time, Voltage, ureg

from FlowCyPy.signal_generator import SignalGenerator
from FlowCyPy.sub_frames import utils
from FlowCyPy.sub_frames.base import BaseSubFrame


class BaseAcquisitionDataFrame(BaseSubFrame):
    """
    Base class for acquisition data frames with common plotting and logging functionalities.
    """

    def __init__(self, dataframe: pd.DataFrame):
        super().__init__(dataframe)

    @classmethod
    def _construct_from_signal_generator(
        cls,
        signal_generator: SignalGenerator,
        time_units: Time | str,
        signal_units: Voltage | str,
    ) -> "AcquisitionDataFrame":
        """
        Converts a signal generator's output into a pandas DataFrame.

        Parameters
        ----------
        signal_generator : SignalGenerator
            The signal generator instance containing the generated signals.
        time_units : Time | str
            The units for the time column in the resulting DataFrame.
        signal_units : Voltage | str
            The units for the signal columns in the resulting DataFrame.

        Returns
        -------
        AcquisitionDataFrame
            A DataFrame containing the signals from the signal generator.
        """
        signal_dataframe = pd.DataFrame()

        time = signal_generator.get_time()

        signal_dataframe["Time"] = pd.Series(time, dtype=f"pint[{time_units}]")

        for detector_name in signal_generator._cpp_get_signal_names():
            signal_dataframe[detector_name] = pd.Series(
                signal_generator.get_signal(detector_name),
                dtype=f"pint[{signal_units}]",
            )

        signal_dataframe = cls(signal_dataframe)

        signal_dataframe.normalize_units(signal_units="SI", time_units="SI")

        return signal_dataframe

    def digitalize(self, digitizer: object):
        """
        Convert analog signals to digital signals using the provided digitizer.

        Parameters
        ----------
        digitizer : object
            An instance of a digitizer that implements the `capture_signal` method.

        Returns
        -------
        BaseAcquisitionDataFrame
            A new instance of the class with digitalized signals.
        """
        digital_df = pd.DataFrame(
            index=self.index, columns=self.columns, data=dict(Time=self.Time)
        )

        for detector_name in self.detector_names:
            analog_signal = self[detector_name]
            digitized_signal, _ = digitizer.capture_signal(signal=analog_signal)

            digital_df[detector_name] = pint_pandas.PintArray(
                digitized_signal, ureg.bit_bins
            )

        output = self.__class__(dataframe=digital_df)

        output.normalize_units(signal_units="max", time_units="max")

        return output

    def normalize_units(
        self, signal_units: Voltage | str = None, time_units: Time | str = None
    ) -> None:
        """
        Normalize the DataFrame's signal and time columns to specified units.

        Parameters
        ----------
        signal_units : Voltage
            The units to which the signal columns should be normalized.
        time_units : Time
            The units to which the time column should be normalized.
        """

        if signal_units == "max":
            if self[self.detector_names[0]].size == 0:
                signal_units = 0 * self[self.detector_names[0]].pint.units
            else:
                signal_units = self[self.detector_names[0]].max().to_compact().units

        if signal_units == "SI":
            if (
                self[self.detector_names[0]].pint.units.dimensionality
                == ureg.bit_bins.dimensionality
            ):
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
        This method ensures that the scatterer attribute is retained in the output DataFrame.
        """
        output = super().__finalize__(other, method, **kwargs)

        return output

    @property
    def detector_names(self) -> List[str]:
        """Return a list of unique detector names."""
        return [col for col in self.columns if col != "Time"]

    def _get_axes_dict(self) -> dict[str, plt.Axes]:
        """
        Creates a dictionary of matplotlib Axes for each detector and scatterer.

        This method generates a dictionary where each key is the name of a detector or "scatterer",
        and the corresponding value is a matplotlib Axes object. This is useful for plotting
        multiple signals in a structured manner.

        Returns
        -------
        dict[str, plt.Axes]
            A dictionary mapping detector names and "scatterer" to their respective Axes objects.
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
                rf"{detector_name} [{self.signal_units._repr_latex_()}]", labelpad=20
            )

        ax.set_xlabel(rf"Time [{self.time_units._repr_latex_()}]")

        return figure, axes

    @MPSPlots.helper.post_mpl_plot
    def plot(self) -> None:
        """
        Plot acquisition data for each detector and the scatterer events.
        This method creates a multi-panel plot with each detector's signal and a scatterer event plot.

        Parameters
        ----------
        filter_population : Union[str, List[str]], optional
            If provided, filters the scatterer events to only include those from the specified population(s).
            Can be a single population name or a list of names.

        Returns
        -------
        plt.Figure
            The figure containing the acquisition data plots.

        """
        self.normalize_units(signal_units="max", time_units="max")

        figure, axes = self._get_axes_dict()

        self._add_to_axes(axes=axes)

        return figure

    @MPSPlots.helper.post_mpl_plot
    def hist(
        self,
        kde: bool = False,
        bins: Optional[int] = "auto",
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, Voltage | Dimensionless]] = None,
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
        kde : bool, optional
            Whether to overlay a KDE curve (default: False).
        bins : Optional[int], optional
            Number of bins for the histogram (default: 'auto', letting Seaborn decide).
        color : Optional[Union[str, dict]], optional
            Color specification for the plot (default: None).
        clip_data : Optional[Union[str, units.Quantity]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            the function removes values above the corresponding quantile (e.g., the top 20% of values).
            If a pint.Quantity is given, it removes values above that absolute value.
        save_as : str, optional
            If provided, the figure is saved to this filename.

        Returns
        -------
        plt.Figure
            The figure containing the acquisition data plots.
        """
        if len(self) == 1:
            return

        n_plots = len(self.detector_names)

        figure, axes = plt.subplots(nrows=n_plots, sharex=True, sharey=True)

        for ax, detector_name in zip(axes, self.detector_names):
            ax.set_ylabel(detector_name)

            signal = self[detector_name].pint.quantity.magnitude

            signal = utils.clip_data(signal=signal, clip_value=clip_data)

            sns.histplot(x=signal, ax=ax, kde=kde, bins=bins, color=color)

        return figure


class AcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for continuous (analog) acquisition data.
    """

    def _add_to_axes(self, axes: dict) -> None:
        """
        Plot analog signal data for each detector.
        """
        for detector_name in self.detector_names:
            ax = axes[detector_name]

            time = self["Time"].pint.to(self.time_units).pint.quantity
            signal = self[detector_name].pint.to(self.signal_units).pint.quantity

            ax.plot(time, signal, label="Analog Signal", linestyle="-", color="black")


class TriggerDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for triggered analog acquisition data.
    """

    @property
    def detector_names(self) -> List[str]:
        """Return a list of unique detector names."""
        return [col for col in self.columns if col not in ["Time", "SegmentID"]]

    @property
    def n_segment(self) -> int:
        return len(self.index.get_level_values("SegmentID").unique())

    def _add_to_axes(self, axes: dict) -> None:
        """
        Plot triggered analog signal data for each detector and highlight each SegmentID region
        with a distinct color.
        """
        for detector_name in self.detector_names:
            ax = axes[detector_name]

            for segment_id, group in self.groupby("SegmentID"):
                time = group["Time"].pint.to(self.time_units)
                signal = group[detector_name]
                start_time = time.min()
                end_time = time.max()

                color = plt.cm.tab10(int(segment_id) % 10)

                ax.axvspan(start_time, end_time, facecolor=color, alpha=0.3)

                ax.step(time, signal, where="mid", color="black", linestyle="-")
