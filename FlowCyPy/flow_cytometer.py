#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional
from TypedUnit import Power, Time, ureg, validate_units

from FlowCyPy.fluidics import Fluidics
from FlowCyPy.fluidics import populations
from FlowCyPy.fluidics.event_collection import EventCollection
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.run_record import RunRecord
from FlowCyPy.digital_processing import DigitalProcessing
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.sub_frames.peaks import PeakDataFrame
from FlowCyPy.sub_frames.triggered import TriggerDataFrame


class FlowCytometer:
    """
    High level orchestrator for the flow cytometry simulation pipeline.

    This class keeps only the persistent fluidic definition and the constant
    optical background level. All other configuration objects are passed
    explicitly to the methods that use them.

    This design keeps the workflow fully visible to the caller and avoids any
    ambiguity about which opto electronic or signal processing configuration is
    active for a given computation.

    Parameters
    ----------
    fluidics : Fluidics
        Fluidic subsystem, including flow cell and population definitions.
    background_power : pint.Quantity, optional
        Constant optical background added to every detector channel.
    """

    @validate_units
    def __init__(
        self,
        fluidics: Fluidics,
        background_power: Optional[Power] = 0 * ureg.milliwatt,
    ):
        self.fluidics = fluidics
        self.background_power = background_power

    def _add_explicit_model_signals(
        self,
        event_collection: EventCollection,
        signal_dict: dict,
        opto_electronics: OptoElectronics,
    ) -> None:
        """
        Add explicit model detector signals to the optical power dictionary.

        Parameters
        ----------
        event_collection : EventCollection
            Population event blocks.
        signal_dict : dict
            Optical power signal dictionary updated in place.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        """
        for events in event_collection:
            if not isinstance(events.sampling_method, populations.ExplicitModel):
                continue

            if events.empty:
                continue

            for detector in opto_electronics.detectors:
                generated_pulse_signal = opto_electronics.source.generate_pulses(
                    velocities=events.get_quantity("Velocity"),
                    pulse_centers=events.get_quantity("Time"),
                    pulse_amplitudes=events.get_quantity(detector.name),
                    time_array=signal_dict["Time"],
                    base_level=0 * ureg.watt,
                )

                signal_dict[detector.name] += generated_pulse_signal

    def _add_gamma_model_signals(
        self,
        event_collection: EventCollection,
        signal_dict: dict,
        opto_electronics: OptoElectronics,
    ) -> None:
        """
        Add gamma model detector signals to the optical power dictionary.

        Parameters
        ----------
        event_collection : EventCollection
            Population event blocks.
        signal_dict : dict
            Optical power signal dictionary updated in place.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        """
        for events in event_collection:
            if not isinstance(events.sampling_method, populations.GammaModel):
                continue

            if events.empty:
                continue

            expected_number_of_particles = events.metadata["ExpectedNumberOfParticles"]

            if expected_number_of_particles == 0:
                continue

            if len(opto_electronics.detectors) == 0:
                raise ValueError("opto_electronics must contain at least one detector.")

            reference_detector = opto_electronics.detectors[0]

            reference_mean_amplitude = events.get_quantity(
                reference_detector.name
            ).mean()

            reference_power_trace = opto_electronics.source.get_gamma_trace(
                time_array=signal_dict["Time"],
                shape=expected_number_of_particles,
                scale=reference_mean_amplitude,
                mean_velocity=events.metadata["VelocityMean"],
            )

            if reference_mean_amplitude.magnitude == 0:
                raise ValueError(
                    "Gamma Model reference mean amplitude is zero, cannot normalize."
                )

            particle_trace = reference_power_trace / reference_mean_amplitude

            events.metadata["ParticleTrace"] = particle_trace
            events.metadata["TimeTrace"] = signal_dict["Time"]

            for detector in opto_electronics.detectors:
                mean_amplitude = events.get_quantity(detector.name).mean()
                detector_power_trace = particle_trace * mean_amplitude
                signal_dict[detector.name] += detector_power_trace

    def compute_analog(
        self,
        run_time: Time,
        event_collection: EventCollection,
        opto_electronics: OptoElectronics,
    ) -> dict:
        """
        Compute the full analog detector waveforms from an event collection.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        event_collection : EventCollection
            Population event blocks with optical coupling already evaluated.
        opto_electronics : OptoElectronics
            Opto electronic configuration.

        Returns
        -------
        dict
            Analog voltage signal dictionary.
        """
        power_signal_dict = opto_electronics.initialize_optical_signal_dict(
            run_time=run_time,
            background_power=self.background_power,
        )

        self._add_explicit_model_signals(
            event_collection=event_collection,
            signal_dict=power_signal_dict,
            opto_electronics=opto_electronics,
        )

        self._add_gamma_model_signals(
            event_collection=event_collection,
            signal_dict=power_signal_dict,
            opto_electronics=opto_electronics,
        )

        return opto_electronics.convert_optical_power_to_voltage(power_signal_dict)

    def _digitize_triggered_segments(
        self,
        processed_analog_dict: dict,
        triggered_analog_dict: dict,
        digital_processing: DigitalProcessing,
        opto_electronics: OptoElectronics,
    ) -> dict:
        """
        Digitize triggered analog segments.

        Parameters
        ----------
        processed_analog_dict : dict
            Processed analog dictionary before segmentation digitization.
        triggered_analog_dict : dict
            Triggered analog segments.
        digital_processing : DigitalProcessing
            Processing configuration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.

        Returns
        -------
        dict
            Triggered digital segment dictionary.
        """
        if opto_electronics.digitizer.use_auto_range:

            min_list = []
            max_list = []
            for detector in opto_electronics.detectors:
                min_, max_ = (
                    processed_analog_dict[detector.name].min(),
                    processed_analog_dict[detector.name].max(),
                )
                min_list.append(min_)
                max_list.append(max_)

            opto_electronics.digitizer.min_voltage = min(min_list)
            opto_electronics.digitizer.max_voltage = max(max_list)

        return opto_electronics.digitizer.digitize_data_dict(triggered_analog_dict)

    def _extract_peaks(
        self,
        triggered_digital_dict: dict,
        digital_processing: DigitalProcessing,
    ) -> Optional[dict]:
        """
        Extract peak features from digitized triggered segments.

        Parameters
        ----------
        triggered_digital_dict : dict
            Triggered digital segment dictionary.
        digital_processing : DigitalProcessing
            Processing configuration.

        Returns
        -------
        dict or None
            Peak dictionary, or ``None`` if no peak algorithm is configured.
        """
        if digital_processing.peak_algorithm is None:
            return None

        return digital_processing.peak_algorithm.run(triggered_digital_dict)

    def process_analog(
        self,
        run_time: Time,
        event_collection: EventCollection,
        analog_dict: dict,
        digital_processing: DigitalProcessing,
        opto_electronics: OptoElectronics,
    ) -> RunRecord:
        """
        Process an existing analog acquisition through the downstream signal
        processing chain.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        event_collection : EventCollection
            Event collection associated with the analog signals.
        analog_dict : dict
            Analog voltage signal dictionary.
        digital_processing : DigitalProcessing
            Signal processing configuration.
        opto_electronics : OptoElectronics
            Opto electronic configuration associated with the analog signal.

        Returns
        -------
        RunRecord
            Run record containing the analog acquisition and all downstream
            results that could be computed.
        """
        run_record = RunRecord(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
            digital_processing=digital_processing,
        )

        processed_analog_dict = opto_electronics.apply_analog_processing(
            analog_dict=analog_dict,
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=processed_analog_dict,
        )

        triggered_analog_dict = (
            digital_processing.discriminator.run_with_dict(processed_analog_dict)
            if digital_processing.discriminator is not None
            else None
        )

        if triggered_analog_dict is None:
            return run_record

        if len(triggered_analog_dict["segment_id"]) == 0:
            print(
                "No triggers detected. Returning analog signal without digital processing."
            )
            return run_record

        triggered_digital_dict = self._digitize_triggered_segments(
            processed_analog_dict=processed_analog_dict,
            triggered_analog_dict=triggered_analog_dict,
            digital_processing=digital_processing,
            opto_electronics=opto_electronics,
        )

        run_record.signal.digital = TriggerDataFrame._construct_from_flat_dict(
            triggered_digital_dict,
        )

        peaks_dict = self._extract_peaks(
            triggered_digital_dict=triggered_digital_dict,
            digital_processing=digital_processing,
        )

        if peaks_dict is not None:
            run_record.peaks = PeakDataFrame._construct_from_dict(peaks_dict)

        return run_record

    def process_run(
        self,
        run_record: RunRecord,
        digital_processing: DigitalProcessing,
    ) -> RunRecord:
        """
        Process an existing acquired run through the downstream signal
        processing chain.

        This method is intended for notebook workflows where the caller already
        has a ``RunRecord`` returned by ``acquire()`` and wants to apply
        downstream processing without passing the acquisition configuration again.

        Parameters
        ----------
        run_record : RunRecord
            Existing run record containing analog acquisition data and the
            opto electronic configuration used to produce it.
        digital_processing : DigitalProcessing
            Signal processing configuration.

        Returns
        -------
        RunRecord
            Processed run record.

        Raises
        ------
        ValueError
            If the input run record does not contain an ``opto_electronics``
            configuration.
        ValueError
            If the input run record does not contain analog signal data.
        """
        if run_record.opto_electronics is None:
            raise ValueError(
                "The provided run_record does not contain opto_electronics. "
                "Make sure it was created with acquire() or manually populated."
            )

        if run_record.signal is None or run_record.signal.analog is None:
            raise ValueError(
                "The provided run_record does not contain analog signal data."
            )

        return self.process_analog(
            run_time=run_record.run_time,
            event_collection=run_record.event_collection,
            analog_dict=run_record.signal.analog.raw_data,
            digital_processing=digital_processing,
            opto_electronics=run_record.opto_electronics,
        )

    def acquire(
        self,
        run_time: Time,
        opto_electronics: OptoElectronics,
    ) -> RunRecord:
        """
        Run the acquisition pipeline up to the analog stage.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.

        Returns
        -------
        RunRecord
            Run record containing the event collection, analog voltage
            waveforms, and the opto electronic configuration used to produce
            them.
        """
        event_collection = self.fluidics.generate_event_collection(
            run_time=run_time,
            sampling_rate=opto_electronics.digitizer.sampling_rate,
        )

        opto_electronics.add_coupling_to_dataframe(
            event_collection=event_collection,
            compute_cross_section=False,
        )

        processed_analog_dict = self.compute_analog(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
        )

        run_record = RunRecord(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=processed_analog_dict,
        )

        return run_record

    def run(
        self,
        run_time: Time,
        opto_electronics: OptoElectronics,
        digital_processing: Optional[DigitalProcessing] = None,
    ) -> RunRecord:
        """
        Run the full simulation pipeline from event generation to peak extraction.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        digital_processing : DigitalProcessing, optional
            Signal processing configuration. If None, no digital processing is applied.

        Returns
        -------
        RunRecord
            Full run record containing all available stages.
        """
        if digital_processing is None:
            digital_processing = DigitalProcessing()

        acquired_run_record = self.acquire(
            run_time=run_time,
            opto_electronics=opto_electronics,
        )

        return self.process_run(
            run_record=acquired_run_record,
            digital_processing=digital_processing,
        )
