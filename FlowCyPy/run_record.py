#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, Union, List, Any
import pandas as pd
from TypedUnit import ureg, Time, Voltage, Dimensionless
from MPSPlots import helper
import matplotlib.pyplot as plt
import seaborn as sns

from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.sub_frames import utils


class NameSpace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class RunRecord:
    """
    A class to store the results of a flow cytometer run.
    This class holds various attributes related to the results of a flow cytometer simulation run,
    including the run time, detected peaks, analog signals, triggered analog signals, and event data.

    Attributes
    ----------
    run_time : Time
        The duration of the acquisition in seconds.
    peaks : Optional[pd.DataFrame]
        A DataFrame containing the detected peaks and their features.
    analog : Optional[AcquisitionDataFrame]
        A structured DataFrame representing the multi-detector analog voltage signals.
    triggered_analog : Optional[AcquisitionDataFrame]
        A structured DataFrame representing the triggered segments of the analog voltage signals.
    events : Optional[pd.DataFrame]
        A DataFrame containing event data for the scatterers.
    """

    signal: NameSpace = None
    events: Optional[pd.DataFrame] = None

    def __init__(
        self,
        detector_names: list[str],
        run_time: Time,
        events: pd.DataFrame,
        analog: AcquisitionDataFrame,
        digital: AcquisitionDataFrame = None,
    ):

        self.detector_names = detector_names
        self.run_time = run_time
        self.events = events

        self.signal = NameSpace(
            analog=analog,
            digital=digital,
        )

    def compute_statistics(self) -> None:
        """
        Computes and prints basic statistics about the run record.

        This method calculates and prints the number of detected peaks, the number of events,
        and the duration of the run time. It provides a quick overview of the run record's contents.
        """
        self.number_of_scatterer_sent = (
            len(self.events) if self.events is not None else 0
        )

        self.rate_of_scatterer = self.number_of_scatterer_sent / self.run_time

        if hasattr(self, "triggered") and self.triggered is not None:
            self.number_of_events_detected = len(self.triggered.groupby("SegmentID"))

    def get_axes_dict(
        self,
        signal_units: ureg.Quantity,
        time_units: ureg.Quantity,
        filter_population: Union[str, List[str]],
    ) -> dict[str, plt.Axes]:
        """
        Creates a dictionary of matplotlib Axes for each detector and scatterer.

        This method generates a dictionary where each key is the name of a detector or "scatterer",
        and the corresponding value is a matplotlib Axes object. This is useful for plotting
        multiple signals in a structured manner.

        Parameters
        ----------
        filter_population : Union[str, List[str]], optional
            Population(s) to filter and highlight in the scatterer plot. Default is None.

        Returns
        -------
        dict[str, plt.Axes]
            A dictionary mapping detector names and "scatterer" to their respective Axes objects.
        """
        n_plots = len(self.detector_names) + 1  # One extra plot for events

        figure, axes_array = plt.subplots(
            nrows=n_plots,
            sharex=True,
            sharey=True,
            gridspec_kw={"height_ratios": [1] * (n_plots - 1) + [0.5]},
        )

        axes = {
            name: ax
            for name, ax in zip(self.detector_names + ["scatterer"], axes_array)
        }

        for _, ax in axes.items():
            ax.yaxis.tick_right()

        for (_, ax), detector_name in zip(axes.items(), self.detector_names):
            ax.set_ylabel(
                rf"{detector_name} [{signal_units._repr_latex_()}]", labelpad=20
            )

        axes["scatterer"].set_xlabel(f"Time [{time_units._repr_latex_()}]")

        self.events._add_event_to_ax(
            ax=axes["scatterer"],
            time_units=time_units,
            filter_population=filter_population,
        )

        return figure, axes

    @helper.post_mpl_plot
    def plot_analog_histogram(
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
        """
        analog = self.signal.analog
        analog.normalize_units(signal_units="max", time_units="max")

        if len(analog) == 1:
            return

        n_plots = len(self.detector_names)

        figure, axes = plt.subplots(nrows=n_plots, sharex=True, sharey=True)

        for ax, detector_name in zip(axes, self.detector_names):
            ax.set_ylabel(detector_name)

            signal = analog[detector_name].pint.quantity.magnitude

            signal = utils.clip_data(signal=signal, clip_value=clip_data)

            sns.histplot(x=signal, ax=ax, kde=kde, bins=bins, color=color)

        return figure

    @helper.post_mpl_plot
    def plot_digital_histogram(
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
        """
        triggered = self.signal.digital
        triggered.normalize_units(time_units="max")

        if len(triggered) == 1:
            return

        n_plots = len(self.detector_names)

        figure, axes = plt.subplots(nrows=n_plots, sharex=True, sharey=True)

        for ax, detector_name in zip(axes, self.detector_names):
            ax.set_ylabel(detector_name)

            signal = triggered[detector_name].pint.quantity.magnitude

            signal = utils.clip_data(signal=signal, clip_value=clip_data)

            sns.histplot(x=signal, ax=ax, kde=kde, bins=bins, color=color)

        return figure

    @helper.post_mpl_plot
    def plot_analog(self, filter_population: Union[str, List[str]] = None) -> None:
        """
        Plots the analog signals.

        This method generates a plot of the analog signals stored in the `analog` attribute.
        It provides a visual representation of the voltage signals over time for each detector.

        Parameters
        ----------
        filter_population : Union[str, List[str]], optional
            Population(s) to filter and highlight in the scatterer plot. Default is None.
        """
        analog = self.signal.analog
        analog.normalize_units(signal_units="max", time_units="max")

        figure, axes = self.get_axes_dict(
            signal_units=analog.signal_units,
            time_units=analog.time_units,
            filter_population=filter_population,
        )

        analog._add_to_axes(axes=axes)

        for (_, ax), detector_name in zip(axes.items(), self.detector_names):
            if not hasattr(self, "triggering_system"):
                break
            if detector_name == self.triggering_system.trigger_detector_name:
                self.triggering_system._add_to_ax(ax, signal_units=analog.signal_units)

        return figure

    @helper.post_mpl_plot
    def plot_digital(self, filter_population: Union[str, List[str]] = None) -> None:
        """
        Plots the triggered digital signals.

        This method generates a plot of the triggered digital signals stored in the `triggered` attribute.
        It provides a visual representation of the segments of the digital voltage signals that were captured
        during the run.

        Parameters
        ----------
        filter_population : Union[str, List[str]], optional
            Population(s) to filter and highlight in the scatterer plot. Default is None.
        """
        digital = self.signal.digital
        digital.normalize_units(time_units="max")

        figure, axes = self.get_axes_dict(
            signal_units=digital.signal_units,
            time_units=digital.time_units,
            filter_population=filter_population,
        )

        digital._add_to_axes(axes=axes)

        return figure
