#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np

from MPSPlots import helper
from TypedUnit import Frequency, Time, Voltage, ureg

from FlowCyPy.fluidics.event_collection import EventCollection


@dataclass
class SignalRecord:
    """
    Container grouping the signal representations associated with one run.

    Parameters
    ----------
    analog : Any, optional
        Analog signal representation for the acquisition. This is typically an
        ``AcquisitionDataFrame`` or another structured signal container.
    digital : Any, optional
        Digital triggered signal representation for the acquisition. This is
        typically a ``TriggerDataFrame`` or another structured signal container.
    """

    analog: Any = None
    digital: Any = None


@dataclass
class RunRecord:
    """
    Container storing the outputs and context of one flow cytometry run.

    This class is the main result object returned by the simulation pipeline.
    It stores both the acquisition context and all available downstream data,
    including analog signals, digital triggered segments, and peak features.

    The object is intentionally self descriptive. In particular, it can store
    the ``opto_electronics`` configuration used during acquisition so the run
    may later be processed further without requiring the caller to pass that
    configuration again.

    Parameters
    ----------
    detector_names : list[str]
        Names of the detector channels associated with this run.
    run_time : Time
        Acquisition duration.
    event_collection : EventCollection
        Structured event collection used for the run.
    opto_electronics : Any, optional
        Opto electronic configuration used during acquisition.
    signal_processing : Any, optional
        Signal processing configuration used during downstream processing.
    signal : SignalRecord, optional
        Container holding analog and digital signal objects.
    peaks : Any, optional
        Peak level data extracted from triggered digital segments.
    discriminator : Any, optional
        Discriminator object used for triggering.
    """

    detector_names: list[str]
    run_time: Time
    event_collection: EventCollection
    opto_electronics: Any = None
    signal_processing: Any = None
    signal: SignalRecord = field(default_factory=SignalRecord)
    peaks: Any = None
    discriminator: Any = None

    @property
    def number_of_scatterers(self) -> int:
        """
        Return the total number of simulated scatterers across all populations.

        Returns
        -------
        int
            Total number of event rows across the event collection.
        """
        return int(np.sum(len(events) for events in self.event_collection))

    @property
    def number_of_triggers(self) -> Optional[int]:
        """
        Return the number of triggered segments detected during the run.

        Returns
        -------
        int or None
            Number of unique triggered segments if digital data are available,
            otherwise ``None``.
        """
        if self.signal.digital is None:
            return None

        return len(self.signal.digital.groupby("SegmentID"))

    @property
    def capture_ratio(self) -> Optional[float]:
        """
        Return the ratio of detected triggers to simulated scatterers.

        Returns
        -------
        float or None
            Capture ratio if trigger data are available and at least one
            scatterer exists, otherwise ``None``.
        """
        if self.number_of_triggers is None:
            return None

        if self.number_of_scatterers == 0:
            return None

        return self.number_of_triggers / self.number_of_scatterers

    @property
    def scatterer_rate(self):
        """
        Return the rate of simulated scatterers over the acquisition interval.

        Returns
        -------
        pint.Quantity
            Scatterer rate in particles per second.
        """
        return self.number_of_scatterers / self.run_time.to("second")

    @property
    def trigger_rate(self) -> Optional[Frequency]:
        """
        Return the trigger rate over the acquisition interval.

        Returns
        -------
        pint.Quantity or None
            Trigger rate in events per second if trigger data are available,
            otherwise ``None``.
        """
        if self.number_of_triggers is None:
            return None

        return self.number_of_triggers / self.run_time.to("second")

    def get_axes_dict(
        self,
        signal_units: Voltage = None,
        time_units: Time = None,
    ) -> tuple[plt.Figure, dict[str, plt.Axes]]:
        """
        Create a figure and one axis per detector, plus one scatterer axis.

        Parameters
        ----------
        signal_units : Voltage, optional
            Voltage unit used to label detector axes.
        time_units : Time, optional
            Time unit passed to the event collection plotting helper.

        Returns
        -------
        tuple[matplotlib.figure.Figure, dict[str, matplotlib.axes.Axes]]
            Figure and axis dictionary keyed by detector names plus
            ``"scatterer"``.
        """
        number_of_plots = len(self.detector_names) + 1

        figure, axes_array = plt.subplots(
            nrows=number_of_plots,
            sharex=True,
            sharey=False,
            gridspec_kw={"height_ratios": [1] * (number_of_plots - 1) + [0.5]},
        )

        axes = {
            name: axis
            for name, axis in zip(self.detector_names + ["scatterer"], axes_array)
        }

        for axis in axes.values():
            axis.yaxis.tick_right()

        for detector_name in self.detector_names:
            axis = axes[detector_name]
            axis.set_ylabel(
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
    def plot_analog(self) -> plt.Figure:
        """
        Plot the analog detector signals together with the event timeline.

        Returns
        -------
        matplotlib.figure.Figure
            Generated matplotlib figure.

        Raises
        ------
        ValueError
            If no analog signal is available in the run record.
        """
        if self.signal.analog is None:
            raise ValueError("No analog signal is available in this run record.")

        self.signal.analog.normalize_units(signal_units="max", time_units="max")

        figure, axes = self.get_axes_dict(
            signal_units=self.signal.analog.signal_units,
            time_units=self.signal.analog.time_units,
        )

        self.signal.analog._add_to_axes(axes=axes)

        if self.discriminator is not None:
            self.discriminator._add_to_ax(
                axes[self.discriminator.trigger_channel],
                signal_units=self.signal.analog.signal_units,
            )

        return figure

    @helper.post_mpl_plot
    def plot_digital(self) -> plt.Figure:
        """
        Plot the triggered digital segments together with the event timeline.

        Returns
        -------
        matplotlib.figure.Figure
            Generated matplotlib figure.

        Raises
        ------
        ValueError
            If no digital signal is available in the run record.
        """
        if self.signal.digital is None:
            raise ValueError("No digital signal is available in this run record.")

        self.signal.digital.to_compact()

        time_units = self.signal.digital.attrs["units"]["Time"]

        figure, axes = self.get_axes_dict(
            time_units=time_units,
        )

        self.signal.digital._add_to_axes(axes=axes)

        return figure

    def __repr__(self) -> str:
        """
        Return a concise summary string for the run record.

        Returns
        -------
        str
            Human readable summary of the run.
        """
        return (
            f"RunRecord(run_time={self.run_time}, "
            f"number_of_scatterers={self.number_of_scatterers}, "
            f"number_of_triggers={self.number_of_triggers}, "
            f"scatterer_rate={self.scatterer_rate}, "
            f"trigger_rate={self.trigger_rate})"
        )
