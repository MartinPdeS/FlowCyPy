import logging
from dataclasses import dataclass, field
from typing import Any
import matplotlib.pyplot as plt
import MPSPlots
import numpy as np
from TypedUnit import Frequency, Time, Voltage
from FlowCyPy.digital_processing import DigitalProcessing
from FlowCyPy.event_collection import EventCollection
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.sub_frames.peaks import PeakDataFrame
from FlowCyPy.sub_frames.triggered import TriggerDataFrame

logger = logging.getLogger(__name__)


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
    run_time : Time
        Acquisition duration.
    event_collection : EventCollection
        Structured event collection used for the run.
    opto_electronics : Any, optional
        Opto electronic configuration used during acquisition.
    digital_processing : Any, optional
        Signal processing configuration used during downstream processing.
    signal : SignalRecord, optional
        Container holding analog and digital signal objects.
    peaks : Any, optional
        Peak level data extracted from triggered digital segments.
    discriminator : Any, optional
        Discriminator object used for triggering.
    """

    run_time: Time
    event_collection: EventCollection
    opto_electronics: Any = None
    digital_processing: Any = None
    signal: SignalRecord = field(default_factory=SignalRecord)
    peaks: Any = None

    _filtered_analog: AcquisitionDataFrame | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def process(self, *, digital_processing: DigitalProcessing) -> "RunRecord":
        """Process this acquisition using the supplied trigger and peak settings.

        Parameters
        ----------
        digital_processing : DigitalProcessing
            Discriminator and optional peak locator to apply.

        Returns
        -------
        RunRecord
            New result with independent digital segments and peak features.
            The analog circuits are applied on the first call. Subsequent calls
            reuse that filtered waveform and the original particle events.
        """
        if self.opto_electronics is None:
            raise ValueError("Processing requires the acquisition's opto_electronics.")
        if self.signal is None or self.signal.analog is None:
            raise ValueError("Processing requires analog signal data.")
        if self._filtered_analog is None:
            if self.opto_electronics.analog_processing:
                filtered = self.opto_electronics.apply_analog_processing(
                    analog_dict=self.signal.analog.raw_data
                )
                self._filtered_analog = AcquisitionDataFrame._construct_from_signal_dict(
                    filtered
                )
            else:
                self._filtered_analog = self.signal.analog
        return self._process_filtered(
            analog=self._filtered_analog, digital_processing=digital_processing
        )

    def _process_filtered(
        self, *, analog: AcquisitionDataFrame, digital_processing: DigitalProcessing
    ) -> "RunRecord":
        """Trigger, digitize and locate peaks on an already filtered waveform."""
        # Plotting can rescale dataframe columns. Give each result its own units
        # and column bindings while sharing the underlying samples.
        analog_view = analog.copy(deep=False)
        run_record = RunRecord(
            run_time=self.run_time,
            event_collection=self.event_collection,
            opto_electronics=self.opto_electronics,
            digital_processing=digital_processing,
            signal=SignalRecord(analog=analog_view),
        )
        run_record._filtered_analog = analog
        triggered_analog_dict = (
            digital_processing.discriminator.run_with_dict(analog.raw_data)
            if digital_processing.discriminator is not None
            else None
        )

        if triggered_analog_dict is None:
            return run_record

        if len(triggered_analog_dict["segment_id"]) == 0:
            logger.debug(
                "No triggers detected. Returning analog signal without digital processing."
            )
            return run_record

        triggered_digital_dict = self.opto_electronics.digitizer.digitize_data_dict(
            triggered_analog_dict
        )

        run_record.signal.digital = TriggerDataFrame._construct_from_flat_dict(
            triggered_digital_dict,
        )

        if digital_processing.peak_locator is not None:
            peaks_dict = digital_processing.peak_locator.run(triggered_digital_dict)

            run_record.peaks = PeakDataFrame._construct_from_dict(peaks_dict)

        return run_record

    @property
    def detector_names(self):
        """
        Return the list of detector names associated with this run.

        Returns
        -------
        list[str]
            List of detector names.
        """
        if self.opto_electronics is None:
            return []
        return [detector.name for detector in self.opto_electronics.detectors]

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
    def number_of_triggers(self) -> int | None:
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
    def capture_ratio(self) -> float | None:
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

    def annotate_detected_events(self):
        """Return simulated events annotated with trigger detection status.

        Detection is determined by matching each event arrival time to a
        digital trigger segment. The method preserves all simulated events,
        including events that were not detected. This is trigger capture, not
        peak-localization success.
        """
        from .analysis import DetectionAnalyzer

        return DetectionAnalyzer().annotate(self)

    def detection_statistics(self, population_name: str) -> dict[str, Any]:
        """Compute trigger-detection statistics for one population.

        Parameters
        ----------
        population_name : str
            Population label to analyze, for example ``"EVs"``.

        Returns
        -------
        dict[str, Any]
            Population name, simulated event count, detected event count, and
            detection efficiency. The result also reports how many detected
            events participated in a multi-event trigger segment and which
            other populations were present. The efficiency is relative to
            events that survived the simulated SEC cutoff.

        Notes
        -----
        The computation is ``DetectedEvents / SimulatedEvents``. An event is
        detected when its arrival time lies inclusively between the first and
        last sample of a digital trigger segment.
        """
        from .analysis import DetectionAnalyzer

        return DetectionAnalyzer.population_statistics(
            events=self.annotate_detected_events(), population_name=population_name
        )

    def coincidence_statistics(self) -> dict[str, Any]:
        """Count trigger segments by the number of assigned simulated arrivals.

        Returns
        -------
        dict[str, Any]
            TotalTriggerSegments counts all digital segments. EmptySegments,
            SingleEventSegments, and CoincidentSegments count segments with
            zero, one, and at least two assigned arrivals, respectively.
            TriggerSegments counts occupied segments and is the denominator
            of CoincidenceRate. PopulationCombinations records which
            populations share coincident segments.
        """
        from .analysis import DetectionAnalyzer

        return DetectionAnalyzer().coincidence_statistics(self)

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
    def trigger_rate(self) -> Frequency | None:
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
        figure_size: tuple[float, float] | None = None,
        include_scatterer: bool = True,
    ) -> tuple[plt.Figure, dict[str, plt.Axes]]:
        """
        Create a figure and one axis per detector, with an optional scatterer axis.

        Parameters
        ----------
        signal_units : Voltage, optional
            Voltage unit used to label detector axes.
        time_units : Time, optional
            Time unit passed to the event collection plotting helper.
        figure_size : tuple[float, float] | None, optional
            Figure size in inches. If ``None``, matplotlib defaults are used.
        include_scatterer : bool, optional
            If ``True``, add the scatterer timeline axis. Defaults to ``True``.

        Returns
        -------
        tuple[matplotlib.figure.Figure, dict[str, matplotlib.axes.Axes]]
            Figure and axis dictionary keyed by detector names and, when
            requested, ``"scatterer"``.
        """
        number_of_plots = len(self.detector_names) + int(include_scatterer)

        figure, axes_array = plt.subplots(
            nrows=number_of_plots,
            sharex=True,
            sharey=False,
            figsize=figure_size,
            gridspec_kw={
                "height_ratios": [1] * len(self.detector_names)
                + ([0.5] if include_scatterer else [])
            },
        )

        axes_array = np.atleast_1d(axes_array)

        axis_names = self.detector_names + (["scatterer"] if include_scatterer else [])

        axes = {
            name: axis
            for name, axis in zip(axis_names, axes_array)
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

        if include_scatterer:
            self.event_collection._add_to_ax(
                ax=axes["scatterer"],
                time_units=time_units,
            )

            axes["scatterer"].set_ylabel("Scatterer", labelpad=20)
            axes["scatterer"].set_yticks([])

        return figure, axes

    def _plot_analog_on_axes(self, axes: dict[str, plt.Axes]) -> None:
        """Draw analog detector signals on the provided axes."""
        time = self.signal.analog["Time"]

        for detector_name in self.detector_names:
            axes[detector_name].plot(
                time,
                self.signal.analog[detector_name],
                label="Analog Signal",
                linestyle="-",
                color="black",
            )

    def _plot_digital_on_axes(self, axes: dict[str, plt.Axes]) -> None:
        """Draw triggered digital segments on the provided axes."""
        for detector_name in self.detector_names:
            axis = axes[detector_name]

            for segment_id, group in self.signal.digital.groupby(level="SegmentID"):
                time = group["Time"]
                signal = group[detector_name]

                axis.axvspan(
                    time.min(),
                    time.max(),
                    facecolor=plt.cm.tab10(int(segment_id) % 10),
                    alpha=0.3,
                )
                axis.step(time, signal, where="mid", color="black", linestyle="-")

    def plot_analog(
        self,
        figure_size: tuple[float, float] | None = None,
        save_as: str | None = None,
        title: str | None = None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        include_scatterer: bool = True,
    ) -> plt.Figure:
        """
        Plot the analog detector signals together with the event timeline.

        Parameters
        ----------
        figure_size : tuple[float, float] | None, optional
            Figure size in inches. If ``None``, matplotlib defaults are used.
        save_as : str | None, optional
            Optional output path used to save the figure.
        title : str | None, optional
            Optional figure title.
        xlim : tuple[float, float] | None, optional
            Optional x-axis limits applied to the shared time axis.
        ylim : tuple[float, float] | None, optional
            Optional y-axis limits applied to detector axes.
        include_scatterer : bool, optional
            If ``True``, include the scatterer timeline subplot. Defaults to
            ``True``.

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

        with plt.style.context(MPSPlots.styles.scientific):
            self.signal.analog.normalize_units(signal_units="max", time_units="max")

            figure, axes = self.get_axes_dict(
                signal_units=self.signal.analog.signal_units,
                time_units=self.signal.analog.time_units,
                figure_size=figure_size,
                include_scatterer=include_scatterer,
            )

            self._plot_analog_on_axes(axes=axes)

            if (
                self.digital_processing is not None
                and self.digital_processing.discriminator is not None
            ):
                self.digital_processing.discriminator._add_to_ax(
                    axes[self.digital_processing.discriminator.trigger_channel],
                    signal_units=self.signal.analog.signal_units,
                )

            if title is not None:
                figure.suptitle(title)

            if xlim is not None:
                for axis in axes.values():
                    axis.set_xlim(xlim)

            if ylim is not None:
                for detector_name in self.detector_names:
                    axes[detector_name].set_ylim(ylim)

            figure.tight_layout(rect=(0, 0, 1, 0.98) if title is not None else None)

            if save_as is not None:
                figure.savefig(save_as, bbox_inches="tight")

            return figure

    def plot_digital(
        self,
        figure_size: tuple[float, float] | None = None,
        save_as: str | None = None,
        title: str | None = None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        include_scatterer: bool = True,
    ) -> plt.Figure:
        """
        Plot the triggered digital segments together with the event timeline.

        Parameters
        ----------
        figure_size : tuple[float, float] | None, optional
            Figure size in inches. If ``None``, matplotlib defaults are used.
        save_as : str | None, optional
            Optional output path used to save the figure.
        title : str | None, optional
            Optional figure title.
        xlim : tuple[float, float] | None, optional
            Optional x-axis limits applied to the shared time axis.
        ylim : tuple[float, float] | None, optional
            Optional y-axis limits applied to detector axes.
        include_scatterer : bool, optional
            If ``True``, include the scatterer timeline subplot. Defaults to
            ``True``.

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

        with plt.style.context(MPSPlots.styles.scientific):
            self.signal.digital.to_compact()

            time_units = self.signal.digital.attrs["units"]["Time"]

            figure, axes = self.get_axes_dict(
                time_units=time_units,
                figure_size=figure_size,
                include_scatterer=include_scatterer,
            )

            self._plot_digital_on_axes(axes=axes)

            if title is not None:
                figure.suptitle(title)

            if xlim is not None:
                for axis in axes.values():
                    axis.set_xlim(xlim)

            if ylim is not None:
                for detector_name in self.detector_names:
                    axes[detector_name].set_ylim(ylim)

            figure.tight_layout(rect=(0, 0, 1, 0.98) if title is not None else None)

            if save_as is not None:
                figure.savefig(save_as, bbox_inches="tight")

            return figure

    def plot_peaks(
        self,
        x: tuple[str, str] | None = None,
        y: tuple[str, str] | None = None,
        z: tuple[str, str] | None = None,
        **kwargs,
    ) -> plt.Figure:
        """Plot peak features using the run peak dataframe.

        Parameters
        ----------
        x, y, z : tuple[str, str] | None
            Peak coordinates expressed as ``(detector_name, feature_name)``.
            The provided axis combination selects a 1D histogram, 2D plot, or
            3D plot.
        **kwargs
            Additional keyword arguments forwarded to the underlying peak plot
            helper.

        Returns
        -------
        matplotlib.figure.Figure
            Generated figure.

        Raises
        ------
        ValueError
            If no peak dataframe is available or the requested axis combination
            is invalid.
        """
        if self.peaks is None:
            raise ValueError("No peak dataframe is available in this run record.")

        if x and not y and not z:
            return self.peaks.plot_hist(x=x, **kwargs)

        if x and y and not z:
            figure, _ = self.peaks.plot_2d(x=x, y=y, **kwargs)
            return figure

        if x and y and z:
            return self.peaks.plot_3d(x=x, y=y, z=z, **kwargs)

        raise ValueError(
            "At least one of 'x', 'y', or 'z' must be provided for plotting."
        )

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
