#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
import pandas as pd
from TypedUnit import ureg, Time, Voltage, Frequency
from MPSPlots import helper
import matplotlib.pyplot as plt


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
    event_collection : Optional[pd.DataFrame]
        A DataFrame containing event data for the scatterers.
    """

    signal: NameSpace = None
    event_collection: Optional[pd.DataFrame] = None

    def __init__(
        self,
        detector_names: list[str],
        run_time: Time,
        event_collection: pd.DataFrame,
    ):

        self.detector_names = detector_names
        self.run_time = run_time
        self.event_collection = event_collection

        self.signal = NameSpace()

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
        return np.sum(len(event) for event in self.event_collection)

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
    def trigger_rate(self) -> Optional[Frequency]:
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
        signal_units: Voltage = None,
        time_units: Time = None,
    ) -> dict[str, plt.Axes]:
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
        n_plots = len(self.detector_names) + 1  # One extra plot for events

        figure, axes_array = plt.subplots(
            nrows=n_plots,
            sharex=True,
            sharey=False,
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
                (
                    rf"{detector_name} [{signal_units._repr_latex_()}]"
                    if signal_units is not None
                    else detector_name
                ),
                labelpad=20,
            )

        self.event_collection._add_to_ax(
            ax=axes["scatterer"],
            time_units=time_units,
        )

        axes["scatterer"].set_ylabel("Scatterer", labelpad=20)

        return figure, axes

    @helper.post_mpl_plot
    def plot_analog(self) -> None:
        """
        Plots the analog signals.

        This method generates a plot of the analog signals stored in the `analog` attribute.
        It provides a visual representation of the voltage signals over time for each detector.

        """
        self.signal.analog.normalize_units(signal_units="max", time_units="max")

        figure, axes = self.get_axes_dict(
            signal_units=self.signal.analog.signal_units,
            time_units=self.signal.analog.time_units,
        )

        self.signal.analog._add_to_axes(axes=axes)

        if hasattr(self, "discriminator"):
            self.discriminator._add_to_ax(
                axes[self.discriminator.trigger_channel],
                signal_units=self.signal.analog.signal_units,
            )

        return figure

    @helper.post_mpl_plot
    def plot_digital(self) -> None:
        """
        Plots the triggered digital signals.

        This method generates a plot of the triggered digital signals stored in the `triggered` attribute.
        It provides a visual representation of the segments of the digital voltage signals that were captured
        during the run.

        """
        time_units = self.signal.digital["Time"].max().to_compact().units

        figure, axes = self.get_axes_dict(
            time_units=time_units,
        )

        self.signal.digital._add_to_axes(axes=axes, time_units=time_units)

        return figure
