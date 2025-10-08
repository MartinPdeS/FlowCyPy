#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, Union, List
import pandas as pd
from TypedUnit import ureg, Time
from MPSPlots import helper
import matplotlib.pyplot as plt

from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame


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

    @property
    def number_of_scatterers(self) -> int:
        """
        Returns the number of scatterers sent through the flow cytometer.

        This property calculates the number of scatterers that were sent through the flow cytometer
        during the run. It is determined by the length of the `events` DataFrame, which contains
        information about each scatterer.

        Returns
        -------
        int
            The number of scatterers sent through the flow cytometer.
        """
        return len(self.events)

    @property
    def capture_ratio(self) -> Optional[float]:
        """
        Returns the capture ratio of scatterers to detected events.

        This property calculates the capture ratio, which is the ratio of the number of detected events
        to the number of scatterers sent through the flow cytometer. It provides insight into the efficiency
        of the detection process.

        Returns
        -------
        Optional[float]
            The capture ratio, or None if no events were detected.
        """
        if self.number_of_triggers is not None:
            return self.number_of_triggers / self.number_of_scatterers
        return None

    @property
    def number_of_triggers(self) -> Optional[int]:
        """
        Returns the number of window triggers detected during the run.

        This property calculates the number of window triggers that were detected during the run.
        It is determined by counting the unique segments in the `triggered` DataFrame,
        which contains information about each detected event.

        Returns
        -------
        Optional[int]
            The number of events detected, or None if no events were detected.
        """
        if hasattr(self.signal, "digital"):
            return len(self.signal.digital.groupby("SegmentID"))
        return None

    @property
    def scatterer_rate(self) -> Optional[ureg.Quantity]:
        """
        Returns the rate of scatterers sent through the flow cytometer.

        This property calculates the rate of scatterers that were sent through the flow cytometer
        during the run. It is determined by dividing the number of scatterers by the run time.

        Returns
        -------
        Optional[ureg.Quantity]
            The rate of scatterers sent through the flow cytometer in particles per second,
            or None if the run time is zero.
        """
        return self.number_of_scatterers / self.run_time.to("second")

    @property
    def trigger_rate(self) -> Optional[ureg.Quantity]:
        """
        Returns the rate of triggers during the run.

        This property calculates the rate of triggers that occurred during the run.
        It is determined by dividing the number of detected events by the run time.

        Returns
        -------
        Optional[ureg.Quantity]
            The rate of detections in events per second, or None if no events were detected
            or if the run time is zero.
        """
        if self.number_of_triggers is not None:
            return self.number_of_triggers / self.run_time.to("second")
        return None

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
