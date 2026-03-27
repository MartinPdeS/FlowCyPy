#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
import pandas as pd

from TypedUnit import Power, Time, ureg, validate_units

from FlowCyPy.fluidics import Fluidics
from FlowCyPy.fluidics import populations
from FlowCyPy.fluidics.event_collection import EventCollection, PopulationEvents
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.run_record import RunRecord
from FlowCyPy.signal_processing import SignalProcessing
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

    def copy_dict(self, dictionnary: dict) -> dict:
        """
        Create a safe working copy of a signal dictionary.

        Parameters
        ----------
        signal_dict : dict
            Signal dictionary containing arrays or Pint quantities.

        Returns
        -------
        dict
            Copied signal dictionary.
        """
        copied_signal_dict = {}

        for key, value in dictionnary.items():
            if hasattr(value, "copy"):
                copied_signal_dict[key] = value.copy()
            else:
                copied_signal_dict[key] = value

        return copied_signal_dict

    def _build_population_events(
        self,
        dataframe: pd.DataFrame,
        population: populations.BasePopulation,
    ) -> PopulationEvents:
        """
        Build a structured event container for one population.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Event table for one population.
        population : populations.BasePopulation
            Population that generated the events.

        Returns
        -------
        PopulationEvents
            Structured event block.
        """
        return PopulationEvents(
            dataframe=dataframe,
            population=population,
            sampling_method=population.sampling_method,
            name=population.name,
            population_type=population.__class__.__name__,
            scatterer_type=population.__class__.__name__,
            metadata={
                "Name": population.name,
                "PopulationType": population.__class__.__name__,
                "ParticleCount": population.concentration,
                "SamplingMethod": population.sampling_method.__class__.__name__,
            },
        )

    def add_population_property_to_events(
        self,
        events: PopulationEvents,
        population: populations.BasePopulation,
    ) -> None:
        """
        Sample population specific properties and append them to the event table.

        Parameters
        ----------
        events : PopulationEvents
            Event block updated in place.
        population : populations.BasePopulation
            Population providing the sampled properties.
        """
        properties = population.sample(number_of_samples=len(events.dataframe))

        for key, value in properties.items():
            events.set_quantity_column(column_name=key, value=value)

    def _generate_explicit_event(
        self,
        population: populations.BasePopulation,
        effective_concentration,
        run_time: Time,
    ) -> PopulationEvents:
        """
        Generate explicit event data for one population.

        Parameters
        ----------
        population : populations.BasePopulation
            Population to simulate.
        effective_concentration : pint.Quantity
            Effective concentration after any selection or dilution.
        run_time : Time
            Acquisition duration.

        Returns
        -------
        PopulationEvents
            Structured explicit event block.
        """
        flow_volume_per_second = (
            self.fluidics.flow_cell.sample.average_flow_speed
            * self.fluidics.flow_cell.sample.area
        )
        particle_flux = effective_concentration * flow_volume_per_second

        number_of_events = int(
            np.rint((particle_flux * run_time).to("particle").magnitude)
        )

        dataframe = pd.DataFrame(index=range(max(number_of_events, 0)))
        events = self._build_population_events(
            dataframe=dataframe, population=population
        )

        if number_of_events <= 0:
            events.metadata["NumberOfEvents"] = 0
            return events

        self.add_population_property_to_events(
            events=events,
            population=population,
        )

        arrival_time = self.fluidics.flow_cell.sample_arrival_times(
            n_events=number_of_events,
            run_time=run_time,
        )

        x_position, y_position, velocities = (
            self.fluidics.flow_cell.sample_transverse_profile(number_of_events)
        )

        events.set_quantity_column(column_name="Time", value=arrival_time)
        events.set_quantity_column(column_name="x", value=x_position)
        events.set_quantity_column(column_name="y", value=y_position)
        events.set_quantity_column(column_name="Velocity", value=velocities)

        events.metadata["NumberOfEvents"] = number_of_events

        return events

    def _generate_gamma_event(
        self,
        population: populations.BasePopulation,
        effective_concentration,
        opto_electronics: OptoElectronics,
    ) -> PopulationEvents:
        """
        Generate support data for one gamma model population.

        Parameters
        ----------
        population : populations.BasePopulation
            Population to simulate.
        effective_concentration : pint.Quantity
            Effective concentration after any selection or dilution.
        opto_electronics : OptoElectronics
            Opto electronic configuration used to compute occupancy related
            metadata.

        Returns
        -------
        PopulationEvents
            Structured gamma model event block.
        """
        number_of_events = population.sampling_method.number_of_samples

        dataframe = pd.DataFrame(index=range(number_of_events))
        events = self._build_population_events(
            dataframe=dataframe, population=population
        )

        x_position, y_position, velocities = (
            self.fluidics.flow_cell.sample_transverse_profile(number_of_events)
        )

        events.set_quantity_column(column_name="x", value=x_position)
        events.set_quantity_column(column_name="y", value=y_position)
        events.set_quantity_column(column_name="Velocity", value=velocities)

        self.add_population_property_to_events(
            events=events,
            population=population,
        )

        mean_velocity = events.get_quantity("Velocity").mean()

        interrogation_volume_per_time_bin = (
            mean_velocity
            / opto_electronics.digitizer.sampling_rate
            * self.fluidics.flow_cell.sample.area
        )

        expected_number_of_particles = (
            (effective_concentration * interrogation_volume_per_time_bin)
            .to("particle")
            .magnitude
        )

        events.metadata["VelocityMean"] = mean_velocity
        events.metadata["InterrogationVolumePerTimeBin"] = (
            interrogation_volume_per_time_bin
        )
        events.metadata["ExpectedNumberOfParticles"] = expected_number_of_particles
        events.metadata["NumberOfEvents"] = number_of_events

        return events

    @validate_units
    def generate_event_collection(
        self,
        run_time: Time,
        opto_electronics: OptoElectronics,
    ) -> EventCollection:
        """
        Generate the full event collection for all configured populations.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics
            Opto electronic configuration used where event metadata depends on
            digitizer timing, such as gamma model occupancy per time bin.

        Returns
        -------
        EventCollection
            Structured population event blocks with coupling already evaluated.
        """
        event_collection = EventCollection()

        for population in self.fluidics.scatterer_collection.populations:
            effective_concentration = population.get_effective_concentration()

            if isinstance(population.sampling_method, populations.ExplicitModel):
                events = self._generate_explicit_event(
                    population=population,
                    effective_concentration=effective_concentration,
                    run_time=run_time,
                )

            elif isinstance(population.sampling_method, populations.GammaModel):
                events = self._generate_gamma_event(
                    population=population,
                    effective_concentration=effective_concentration,
                    opto_electronics=opto_electronics,
                )

            else:
                raise TypeError(
                    f"Unsupported sampling method: {population.sampling_method.__class__.__name__}"
                )

            event_collection.append(events)

        opto_electronics._add_coupling_to_dataframe(
            event_collection=event_collection,
            compute_cross_section=False,
        )

        return event_collection

    def run_explicit_models(
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

    def run_gamma_models(
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

            particle_trace = reference_power_trace / reference_mean_amplitude

            events.metadata["particles_trace"] = particle_trace
            events.metadata["time_trace"] = signal_dict["Time"]

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

        self.run_explicit_models(
            event_collection=event_collection,
            signal_dict=power_signal_dict,
            opto_electronics=opto_electronics,
        )

        self.run_gamma_models(
            event_collection=event_collection,
            signal_dict=power_signal_dict,
            opto_electronics=opto_electronics,
        )

        return opto_electronics.convert_optical_power_to_voltage(power_signal_dict)

    def _digitize_triggered_segments(
        self,
        processed_analog_dict: dict,
        triggered_analog_dict: dict,
        signal_processing: SignalProcessing,
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
        signal_processing : SignalProcessing
            Processing configuration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.

        Returns
        -------
        dict
            Triggered digital segment dictionary.
        """
        if opto_electronics.digitizer.use_auto_range:
            opto_electronics.digitizer.capture_signal(
                processed_analog_dict[signal_processing.discriminator.trigger_channel]
            )

        return opto_electronics.digitizer.digitize_data_dict(triggered_analog_dict)

    def _extract_peaks(
        self,
        triggered_digital_dict: dict,
        signal_processing: SignalProcessing,
    ) -> Optional[dict]:
        """
        Extract peak features from digitized triggered segments.

        Parameters
        ----------
        triggered_digital_dict : dict
            Triggered digital segment dictionary.
        signal_processing : SignalProcessing
            Processing configuration.

        Returns
        -------
        dict or None
            Peak dictionary, or ``None`` if no peak algorithm is configured.
        """
        if signal_processing.peak_algorithm is None:
            return None

        return signal_processing.peak_algorithm.run(triggered_digital_dict)

    def process_analog(
        self,
        run_time: Time,
        event_collection: EventCollection,
        analog_dict: dict,
        signal_processing: SignalProcessing,
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
        signal_processing : SignalProcessing
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
            detector_names=[detector.name for detector in opto_electronics.detectors],
            event_collection=event_collection,
            opto_electronics=opto_electronics,
            signal_processing=signal_processing,
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=self.copy_dict(analog_dict),
        )

        processed_analog_dict = opto_electronics.apply_analog_processing(
            analog_dict=analog_dict,
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=processed_analog_dict,
        )

        triggered_analog_dict = (
            signal_processing.discriminator.run_with_dict(analog_dict)
            if signal_processing.discriminator is not None
            else None
        )

        if triggered_analog_dict is None:
            return run_record

        if len(triggered_analog_dict["segment_id"]) == 0:
            print(
                "No triggers detected. Returning analog signal without digital processing."
            )
            run_record.discriminator = signal_processing.discriminator
            return run_record

        triggered_digital_dict = self._digitize_triggered_segments(
            processed_analog_dict=processed_analog_dict,
            triggered_analog_dict=triggered_analog_dict,
            signal_processing=signal_processing,
            opto_electronics=opto_electronics,
        )

        run_record.signal.digital = TriggerDataFrame._construct_from_flat_dict(
            triggered_digital_dict,
        )

        peaks_dict = self._extract_peaks(
            triggered_digital_dict=triggered_digital_dict,
            signal_processing=signal_processing,
        )

        if peaks_dict is not None:
            run_record.peaks = PeakDataFrame._construct_from_dict(peaks_dict)

        run_record.discriminator = signal_processing.discriminator

        return run_record

    def process_run(
        self,
        run_record: RunRecord,
        signal_processing: SignalProcessing,
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
        signal_processing : SignalProcessing
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
            signal_processing=signal_processing,
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
        event_collection = self.generate_event_collection(
            run_time=run_time,
            opto_electronics=opto_electronics,
        )

        analog_dict = self.compute_analog(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
        )

        run_record = RunRecord(
            run_time=run_time,
            detector_names=[detector.name for detector in opto_electronics.detectors],
            event_collection=event_collection,
            opto_electronics=opto_electronics,
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=analog_dict,
        )

        return run_record

    def run(
        self,
        run_time: Time,
        opto_electronics: OptoElectronics,
        signal_processing: SignalProcessing,
    ) -> RunRecord:
        """
        Run the full simulation pipeline from event generation to peak extraction.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        signal_processing : SignalProcessing
            Signal processing configuration.

        Returns
        -------
        RunRecord
            Full run record containing all available stages.
        """
        acquired_run_record = self.acquire(
            run_time=run_time,
            opto_electronics=opto_electronics,
        )

        return self.process_run(
            run_record=acquired_run_record,
            signal_processing=signal_processing,
        )
