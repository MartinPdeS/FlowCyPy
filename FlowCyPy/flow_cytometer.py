#!/usr/bin/env python
# -*- coding: utf-8 -*-
import signal
from typing import Optional
import pandas as pd
import numpy as np
from TypedUnit import Power, Time, ureg, validate_units
from pint_pandas import PintArray

from FlowCyPy.fluidics import Fluidics
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.signal_processing import SignalProcessing
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.sub_frames.triggered import TriggerDataFrame
from FlowCyPy.run_record import RunRecord
from FlowCyPy.fluidics import populations
from FlowCyPy.fluidics.event_collection import EventCollection


class FlowCytometer:
    """
    A simulation class for modeling flow cytometer signals, including Forward Scatter (FSC) and Side Scatter (SSC) channels.

    The FlowCytometer class integrates optical and flow dynamics to simulate signal generation in a flow cytometer.
    It handles particle distributions, flow cell properties, laser source configurations, and detector behavior to
    replicate realistic cytometry conditions. This includes the generation of synthetic signal pulses for each
    particle event and noise modeling for accurate signal representation.

    Parameters
    ----------
    opto_electronics : OptoElectronics
        An instance of the OptoElectronics class, which contains the configuration of detectors, digitizer, source, and amplifier.
    fluidics : Fluidics
        An instance of the Fluidics class, which manages the flow cell and scatterer collection.
    signal_processing : SignalProcessing
        An instance of the SignalProcessing class, which handles the processing of analog and digital signals.
    background_power : pint.Quantity, optional
        The background power level in the system, defaulting to 0 mW. This represents the constant background signal that is present in the system, which can affect the detection of actual signals.

    Raises
    ------
    AssertionError
        If the number of detectors provided is not exactly two, or if both detectors share the same name.

    """

    @validate_units
    def __init__(
        self,
        opto_electronics: OptoElectronics,
        fluidics: Fluidics,
        signal_processing: SignalProcessing,
        background_power: Optional[Power] = 0 * ureg.milliwatt,
    ):
        self.fluidics = fluidics
        self.background_power = background_power
        self.opto_electronics = opto_electronics
        self.signal_processing = signal_processing

    def run_explicit_models(self, event_collection, signals: dict) -> None:
        """
        Run all ExplicitModel populations and add their optical power pulses to the signal generator.

        For each population event frame using ExplicitModel, this method generates Gaussian shaped
        pulses directly in the optical power domain for every detector, using:
        - events["Time"] as pulse centers
        - events["Sigmas"] as pulse widths
        - events[detector.name] as pulse amplitudes

        Notes
        -----
        Assumes all required columns exist and carry Pint units.
        Skips populations whose event frame is empty.
        """
        for events in event_collection:
            if not isinstance(events.sampling_method, populations.ExplicitModel):
                continue

            if events.empty:
                continue

            for detector in self.opto_electronics.detectors:
                signal_watt = self.opto_electronics.source.generate_pulses(
                    velocities=events["Velocity"].pint.quantity,
                    pulse_centers=events["Time"].pint.quantity,
                    pulse_amplitudes=events[detector.name].pint.quantity,
                    time_array=signals["Time"],
                    base_level=0 * ureg.watt,
                )

                signals[detector.name] += signal_watt

    def run_gamma_models(self, event_collection, signals: dict) -> None:
        """
        Run all GammaModel populations and add correlated optical power traces to the signal generator.

        For each GammaModel population, this method produces a single shared stochastic latent trace
        and applies detector specific scaling so that all detector signals are perfectly correlated
        in time and differ only by amplitude.

        Implementation
        --------------
        - Use the first detector as a reference to draw one gamma distributed power trace via the
        C++ backend (this sets the temporal stochasticity).
        - Convert that reference trace into a dimensionless latent particle trace by dividing by
        the reference mean amplitude.
        - For each other detector, scale the latent trace by its mean amplitude and add it to the
        corresponding detector signal.

        Notes
        -----
        Skips populations whose event frame is empty.
        Assumes:
        - events.population.concentration exists
        - signal_generator._cpp_add_gamma_trace writes into the named signal and returns the trace
        - signal_generator.add_array_to_signal exists (as in your SignalGenerator wrapper)
        """
        for events in event_collection:
            if not isinstance(events.sampling_method, populations.GammaModel):
                continue

            if events.empty:
                continue

            velocity = events["Velocity"].pint.quantity.mean()

            interrogation_volume_per_time_bin = (
                velocity
                / self.signal_processing.digitizer.sampling_rate
                * self.fluidics.flow_cell.sample.area
            )

            effective_concentration = events.population.get_effective_concentration()
            expected_number_of_particles = (
                (effective_concentration * interrogation_volume_per_time_bin)
                .to("particle")
                .magnitude
            )

            if expected_number_of_particles == 0:
                continue

            events.attrs["expected_number_of_particles"] = expected_number_of_particles

            reference_detector = self.opto_electronics.detectors[0]

            reference_mean_amplitude = events[
                reference_detector.name
            ].values.quantity.mean()

            reference_power_trace = self.opto_electronics.source.get_gamma_trace(
                time_array=signals["Time"],
                shape=expected_number_of_particles,
                scale=reference_mean_amplitude,
                mean_velocity=events.attrs["VelocityMean"],
            )

            particles_trace = reference_power_trace / (reference_mean_amplitude)

            events.attrs["particles_trace"] = particles_trace
            events.attrs["time_trace"] = signals["Time"]

            for detector in self.opto_electronics.detectors:
                mean_amplitude = events[detector.name].values.quantity.mean()

                detector_power_trace = particles_trace * mean_amplitude

                signals[detector.name] += detector_power_trace

    def compute_analog(
        self, run_time: Time, event_collection: pd.DataFrame
    ) -> AcquisitionDataFrame:
        """
        Simulates the complete analog optical response generated by all detected particle events.

        This function builds the full analog waveform that emerges from the optical and
        opto electronic chain of the cytometer. It proceeds in three major stages:

        1. Optical domain
        - Creates an optical power time series for each detector
        - For explicit sampling models, generates Gaussian shaped pulses directly
        - For gamma models, draws a gamma distributed power trace that matches the
            expected total particle contribution and optionally smooths it with a
            Gaussian convolution
        - Adds the constant background optical power

        2. Conversion to photocurrent
        - Converts optical power to photocurrent using the detector responsivity
            and the illumination wavelength
        - Applies bandwidth dependent effects from the digitizer

        3. Current domain to voltage domain
        - Adds optional dark current noise when enabled in simulation settings
        - Passes all photocurrents through the analog amplifier model
        - Applies final analog conditioning and filtering steps

        The output is returned as an AcquisitionDataFrame, which contains voltage
        waveforms for all detectors on a shared time base, formatted with a clear
        multi level index.

        Parameters
        ----------
        run_time : Time
            Total simulated duration of the acquisition
        event_collection : pandas.DataFrame
            Collection of detected particle events, where each entry contains the
            event time, width, amplitude, velocity, and sampling method

        Returns
        -------
        AcquisitionDataFrame
            Structured representation of the final analog voltage signals for all
            detectors, including the time axis and processed analog waveforms

        Raises
        ------
        ValueError
            If required event fields are missing, including Sigmas or Time for
            explicit pulse generation
        """
        signal_dict = {}

        signal_dict["Time"] = self.signal_processing.digitizer.get_time_series(
            run_time=run_time
        )
        n_elements = len(signal_dict["Time"])

        for detector in self.opto_electronics.detectors:
            signal_dict[detector.name] = np.ones(n_elements) * self.background_power

        self.run_explicit_models(event_collection=event_collection, signals=signal_dict)

        self.run_gamma_models(event_collection=event_collection, signals=signal_dict)

        # Add RIN noise if enabled (before shot noise, as it is a modulation of the optical power)
        if (
            self.opto_electronics.source.include_rin_noise
            and self.opto_electronics.source.rin is not None
        ):
            signal_dict = self.opto_electronics.source.add_rin_to_signal_dict(
                signal_dict=signal_dict,
            )

        # Add shot noise if enabled (after all optical processing steps)
        if self.opto_electronics.source.include_shot_noise:
            for detector in self.opto_electronics.detectors:
                signal_dict[detector.name] = (
                    self.opto_electronics.source.add_shot_noise_to_signal(
                        signal=signal_dict[detector.name],
                        time=signal_dict["Time"],
                    )
                )

        # Optical power → photocurrent
        # Step: Convert optical power to current using the responsivity
        for detector in self.opto_electronics.detectors:
            signal_dict[detector.name] *= detector.responsivity.to("ampere / watt")

        # Signal units are now ampere
        for detector in self.opto_electronics.detectors:
            signal_dict[detector.name] = detector.apply_dark_current_noise(
                signal=signal_dict[detector.name],
                bandwidth=self.signal_processing.digitizer.bandwidth,
            )

        # Photocurrent → voltage
        # Signal units are now volt
        for detector in self.opto_electronics.detectors:
            signal_dict[detector.name] = self.opto_electronics.amplifier.amplify(
                signal=signal_dict[detector.name],
                sampling_rate=self.signal_processing.digitizer.sampling_rate,
            )

        # Final analog signal conditioning
        for detector in self.opto_electronics.detectors:
            for circuit in self.signal_processing.analog_processing:
                signal_dict[detector.name] = circuit.process(
                    signal=signal_dict[detector.name],
                    sampling_rate=self.signal_processing.digitizer.sampling_rate,
                )

        return signal_dict

    def run(self, run_time: Time) -> RunRecord:
        """
        Runs a complete flow cytometry simulation for the specified acquisition duration.

        The pipeline includes:
        1. Initialization and setup of fluidic/optical components
        2. Particle event simulation and optical signal generation
        3. Analog and digital signal processing
        4. Triggered signal extraction and peak feature detection

        Parameters
        ----------
        run_time : Time
            Duration of the simulated acquisition (e.g., `1.0 * ureg.millisecond`).
        compute_cross_section : bool, optional
            Whether to compute the scattering cross-section for each event. Default is False.

        Returns
        -------
        RunRecord
            Simulation output containing all analog, digital, and peak-level data.
        """
        event_collection = self.generate_event_collection(run_time=run_time)

        run_record = RunRecord(
            run_time=run_time,
            detector_names=[d.name for d in self.opto_electronics.detectors],
            event_collection=event_collection,
        )

        analog_dict = self.compute_analog(
            event_collection=event_collection, run_time=run_time
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=analog_dict,
        )

        if self.signal_processing.discriminator is None:
            return run_record

        triggered_analog_dict = self.signal_processing.discriminator.run_with_dict(
            analog_dict
        )

        if self.signal_processing.digitizer.use_auto_range:
            self.signal_processing.digitizer.capture_signal(
                analog_dict[self.signal_processing.discriminator.trigger_channel]
            )

        triggered_digital_dict = self.signal_processing.digitizer.digitize_data_dict(
            triggered_analog_dict
        )

        run_record.signal.digital = TriggerDataFrame._construct_from_segment_dict(
            triggered_digital_dict,
        )

        if self.signal_processing.discriminator is None:
            return run_record

        run_record.peaks = self.signal_processing.peak_algorithm.run(
            run_record.signal.digital
        )
        run_record.discriminator = self.signal_processing.discriminator

        return run_record

    def add_population_property_to_frame(
        self, dataframe: pd.DataFrame, population: populations.BasePopulation
    ) -> None:
        """
        Adds properties of a given population to the provided DataFrame.

        This method extracts relevant properties from the population and adds them as columns
        to the DataFrame. The specific properties added depend on the type of population and
        its attributes.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            The DataFrame to which the population properties will be added.
        population : populations.BasePopulation
            The population whose properties are to be added to the DataFrame.

        Returns
        -------
        None
            The method modifies the DataFrame in place and does not return anything.
        """
        properties = population.sample(number_of_samples=len(dataframe))

        for key, value in properties.items():
            dataframe[key] = PintArray(value, dtype=value.units)

    def _generate_explicit_event(
        self,
        population: populations.BasePopulation,
        effective_concentration,
        run_time: Time,
    ) -> pd.DataFrame:
        """
        Generates events for a population using the ExplicitModel sampling method.
        This method calculates the expected number of particles based on the effective concentration and flow conditions,
        then samples particle events according to the ExplicitModel. The resulting DataFrame includes event times, positions, velocities, and any additional properties from the population.

        Parameters
        ----------
        population : populations.BasePopulation
            The population for which to generate events.
        effective_concentration : pint.Quantity
            The effective concentration of particles in the flow.
        run_time : Time
            The total duration of the simulated acquisition.

        Returns
        -------
        None
            The method modifies the DataFrame in place and does not return anything.
        """

        flow_volume_per_second = (
            self.fluidics.flow_cell.sample.average_flow_speed
            * self.fluidics.flow_cell.sample.area
        )
        particle_flux = effective_concentration * flow_volume_per_second

        n_events = int(np.rint((particle_flux * run_time).to("particle").magnitude))
        if n_events <= 0:
            return

        dataframe = pd.DataFrame(index=range(n_events))

        self.add_population_property_to_frame(
            dataframe=dataframe, population=population
        )

        arrival_time = self.fluidics.flow_cell.sample_arrival_times(
            n_events=n_events, run_time=run_time
        )

        x, y, velocities = self.fluidics.flow_cell.sample_transverse_profile(n_events)

        for key, value in {
            "Time": arrival_time,
            "x": x,
            "y": y,
            "Velocity": velocities,
        }.items():
            dataframe[key] = PintArray(value, value.units)

        return dataframe

    def _generate_gamma_event(
        self, population: populations.BasePopulation, effective_concentration
    ) -> pd.DataFrame:
        """
        Generates events for a population using the GammaModel sampling method.

        This method calculates the expected number of particles based on the effective concentration and flow conditions,
        then samples particle events according to the GammaModel. The resulting DataFrame includes event times, positions,
        velocities, and any additional properties from the population.

        Parameters
        ----------
        population : populations.BasePopulation
            The population for which to generate events.
        effective_concentration : pint.Quantity
            The effective concentration of particles in the flow.

        Returns
        -------
        None
            The method modifies the DataFrame in place and does not return anything.
        """

        n_events = population.sampling_method.number_of_samples

        dataframe = pd.DataFrame(index=range(n_events))

        x, y, velocities = self.fluidics.flow_cell.sample_transverse_profile(n_events)

        dataframe["x"] = PintArray(x, ureg.meter)
        dataframe["y"] = PintArray(y, ureg.meter)
        dataframe["Velocity"] = PintArray(velocities, ureg.meter / ureg.second)

        self.add_population_property_to_frame(
            dataframe=dataframe, population=population
        )

        dataframe.attrs["VelocityMean"] = dataframe["Velocity"].mean()

        dataframe.attrs["InterrogationVolumePerTimeBin"] = (
            dataframe.attrs["VelocityMean"]
            / self.signal_processing.digitizer.sampling_rate
            * self.fluidics.flow_cell.sample.area
        ).mean()

        dataframe.expected = (
            (effective_concentration * dataframe.attrs["InterrogationVolumePerTimeBin"])
            .to("particle")
            .magnitude
        )

        return dataframe

    @validate_units
    def generate_event_collection(self, run_time: Time) -> EventCollection:
        """
        Generates a DataFrame of event times and sampled velocities for each population based on the specified scheme.
        """
        event_collection = EventCollection()

        for population in self.fluidics.scatterer_collection.populations:
            effective_concentration = population.get_effective_concentration()

            if isinstance(population.sampling_method, populations.ExplicitModel):
                dataframe = self._generate_explicit_event(
                    population=population,
                    effective_concentration=effective_concentration,
                    run_time=run_time,
                )

            elif isinstance(population.sampling_method, populations.GammaModel):
                dataframe = self._generate_gamma_event(
                    population=population,
                    effective_concentration=effective_concentration,
                )

            dataframe.attrs["Name"] = population.name
            dataframe.attrs["PopulationType"] = population.__class__.__name__
            dataframe.attrs["ParticleCount"] = population.concentration
            dataframe.attrs["SamplingMethod"] = (
                population.sampling_method.__class__.__name__
            )

            dataframe.sampling_method = population.sampling_method

            dataframe.population = population

            dataframe.scatterer_type = population.__class__.__name__

            event_collection.events_list.append(dataframe)

        self.opto_electronics._add_coupling_to_dataframe(
            event_collection=event_collection,
            compute_cross_section=False,
        )

        return event_collection
