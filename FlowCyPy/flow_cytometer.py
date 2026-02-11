#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import numpy as np
from TypedUnit import Power, Time, ureg, validate_units

from FlowCyPy.fluidics import Fluidics
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.binary.signal_generator import SignalGenerator
from FlowCyPy.signal_processing import SignalProcessing
from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.run_record import RunRecord


from FlowCyPy.event_collection import EventCollection
import pint_pandas
from FlowCyPy.sampling_method import GammaModel, ExplicitModel


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

    def _create_signal_generator(self, run_time: Time) -> SignalGenerator:
        """
        Creates a signal generator for the flow cytometer.

        This method initializes a signal generator with the specified run time and prepares it
        to generate signals based on the flow cytometer's configuration.

        Parameters
        ----------
        run_time : pint.Quantity
            The duration of the acquisition in seconds.

        Returns
        -------
        SignalGenerator
            An instance of `SignalGenerator` configured for the flow cytometer.
        """
        time_series = self.signal_processing.digitizer.get_time_series(
            run_time=run_time
        )

        signal_generator = SignalGenerator(n_elements=len(time_series))

        signal_generator.add_time(time_series)

        for detector in self.opto_electronics.detectors:
            signal_generator.create_zero_signal(channel=detector.name)

        return signal_generator

    def run_explicit_models(self, event_collection, signal_generator) -> None:
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
            if not isinstance(events.sampling_method, ExplicitModel):
                continue

            if events.empty:
                continue

            for detector in self.opto_electronics.detectors:
                signal_generator.generate_pulses_to_signal(
                    channel=detector.name,
                    sigmas=events["Sigmas"].pint.to("second").values.quantity.magnitude,
                    centers=events["Time"].pint.to("second").values.quantity.magnitude,
                    amplitudes=events[detector.name]
                    .pint.to("watt")
                    .values.quantity.magnitude,
                    base_level=0,
                )

    def run_gamma_models(self, event_collection, signal_generator) -> None:
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
        - events.population.particle_count exists
        - events.attrs["VelocitySigmas"] exists (Pint Quantity)
        - signal_generator._cpp_add_gamma_trace writes into the named signal and returns the trace
        - signal_generator.add_array_to_signal exists (as in your SignalGenerator wrapper)
        """
        for events in event_collection:
            if not isinstance(events.sampling_method, GammaModel):
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

            reference_power_trace = (
                signal_generator.add_gamma_trace_to_signal(
                    channel=reference_detector.name,
                    shape=expected_number_of_particles,
                    scale=reference_mean_amplitude.to("watt").magnitude,
                    gaussian_sigma=events.attrs["VelocitySigmas"]
                    .to("second")
                    .magnitude,
                )
                * ureg.watt
            )

            particles_trace = reference_power_trace / (reference_mean_amplitude)

            events.attrs["particles_trace"] = particles_trace
            events.attrs["time_trace"] = signal_generator.get_time()

            for detector in self.opto_electronics.detectors[1:]:
                mean_amplitude = events[detector.name].values.quantity.mean().to("watt")

                detector_power_trace = particles_trace * mean_amplitude

                signal_generator.add_array_to_signal(
                    channel=detector.name,
                    array=detector_power_trace.to("watt").magnitude,
                )

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
        signal_generator = self._create_signal_generator(run_time=run_time)

        signal_generator.add_constant(
            constant=self.background_power.to("watt").magnitude
        )  # Initial unit: optical power

        self.run_explicit_models(
            event_collection=event_collection, signal_generator=signal_generator
        )

        self.run_gamma_models(
            event_collection=event_collection, signal_generator=signal_generator
        )

        # Optical power → photocurrent
        for detector in self.opto_electronics.detectors:
            detector._transform_coupling_power_to_current(
                signal_generator=signal_generator,
                wavelength=self.opto_electronics.source.wavelength,
                bandwidth=self.signal_processing.digitizer.bandwidth,
            )

        # Add dark current noise if enabled
        # Signal units are now ampere
        if (
            SimulationSettings.include_noises
            and SimulationSettings.include_dark_current_noise
        ):
            for detector in self.opto_electronics.detectors:
                detector.apply_dark_current_noise(
                    signal_generator=signal_generator,
                    bandwidth=self.signal_processing.digitizer.bandwidth,
                )

        # Photocurrent → voltage
        # Signal units are now volt
        self.opto_electronics.amplifier.amplify(
            signal_generator=signal_generator,
        )

        # Final analog signal conditioning
        self.signal_processing.process_analog(signal_generator)

        # Create structured DataFrame output
        analog_aquisition = AcquisitionDataFrame._construct_from_signal_generator(
            signal_generator=signal_generator,
        )

        return analog_aquisition

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

        analog = self.compute_analog(
            event_collection=event_collection, run_time=run_time
        )

        run_record = RunRecord(
            run_time=run_time,
            detector_names=[d.name for d in self.opto_electronics.detectors],
            event_collection=event_collection,
            analog=analog,
        )

        if self.signal_processing.triggering_system is not None:
            run_record.signal.analog_triggered = (
                self.signal_processing.triggering_system.run(dataframe=analog)
            )

            run_record.signal.digital = run_record.signal.analog_triggered.digitalize(
                digitizer=self.signal_processing.digitizer
            ).normalize_units(signal_units=ureg.bit_bins)

            if self.signal_processing.peak_algorithm is not None:
                run_record.peaks = self.signal_processing.peak_algorithm.run(
                    run_record.signal.digital
                )

            run_record.triggering_system = self.signal_processing.triggering_system

        return run_record

    @validate_units
    def generate_event_collection(self, run_time: Time) -> EventCollection:
        """
        Generates a DataFrame of event times and sampled velocities for each population based on the specified scheme.
        """
        event_collection = EventCollection()

        for population in self.fluidics.scatterer_collection.populations:
            effective_concentration = population.get_effective_concentration()

            if isinstance(population.sampling_method, ExplicitModel):

                flow_volume_per_second = (
                    self.fluidics.flow_cell.sample.average_flow_speed
                    * self.fluidics.flow_cell.sample.area
                )
                particle_flux = effective_concentration * flow_volume_per_second

                n_events = int(
                    np.rint((particle_flux * run_time).to("particle").magnitude)
                )
                if n_events <= 0:
                    continue

                dataframe = pd.DataFrame(index=range(n_events))

                population.add_property_to_frame(dataframe=dataframe)

                arrival_time = self.fluidics.flow_cell.sample_arrival_times(
                    n_events=n_events, run_time=run_time
                )

                x, y, velocities = self.fluidics.flow_cell.sample_transverse_profile(
                    n_events
                )
                for key, value in {
                    "Time": arrival_time,
                    "x": x,
                    "y": y,
                    "Velocity": velocities,
                }.items():
                    dataframe[key] = pint_pandas.PintArray(value, value.units)

                widths = self.opto_electronics.source.get_particle_width(
                    velocity=velocities
                )

                dataframe["Sigmas"] = pint_pandas.PintArray(widths, widths.units)

            elif isinstance(population.sampling_method, GammaModel):
                n_events = population.sampling_method.mc_samples

                dataframe = pd.DataFrame(index=range(n_events))

                x, y, velocities = self.fluidics.flow_cell.sample_transverse_profile(
                    n_events
                )

                dataframe["x"] = pint_pandas.PintArray(x, ureg.meter)
                dataframe["y"] = pint_pandas.PintArray(y, ureg.meter)
                dataframe["Velocity"] = pint_pandas.PintArray(
                    velocities, ureg.meter / ureg.second
                )

                population.add_property_to_frame(dataframe=dataframe)

                dataframe.attrs["VelocityMean"] = dataframe["Velocity"].mean()

                dataframe.attrs["VelocitySigmas"] = (
                    self.opto_electronics.source.get_particle_width(
                        velocity=dataframe["Velocity"]
                    ).mean()
                )

                dataframe.attrs["InterrogationVolumePerTimeBin"] = (
                    dataframe.attrs["VelocityMean"]
                    / self.signal_processing.digitizer.sampling_rate
                    * self.fluidics.flow_cell.sample.area
                ).mean()

                dataframe.expected = (
                    (
                        effective_concentration
                        * dataframe.attrs["InterrogationVolumePerTimeBin"]
                    )
                    .to("particle")
                    .magnitude
                )

            dataframe.attrs["Name"] = population.name
            dataframe.attrs["PopulationType"] = population.__class__.__name__
            dataframe.attrs["ParticleCount"] = population.particle_count
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
