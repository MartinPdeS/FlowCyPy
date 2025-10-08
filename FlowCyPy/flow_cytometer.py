#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
from TypedUnit import Power, Time, ureg, validate_units

from FlowCyPy.fluidics import Fluidics
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.signal_generator import SignalGenerator
from FlowCyPy.signal_processing import SignalProcessing
from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.run_record import RunRecord


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

        signal_generator = SignalGenerator(
            n_elements=len(time_series), time_units=ureg.second, signal_units=ureg.watt
        )

        signal_generator.add_time(time_series)

        for detector in self.opto_electronics.detectors:
            signal_generator.create_zero_signal(signal_name=detector.name)

        return signal_generator

    def compute_events(
        self, run_record: RunRecord, compute_cross_section: bool = False
    ) -> pd.DataFrame:
        """
        Generates a DataFrame of events based on the scatterer collection and flow cell properties.

        This method samples particle events from the fluidics system and prepares a DataFrame
        containing the event times, positions, and other relevant properties.

        Parameters
        ----------
        run_record : RunRecord
            The RunRecord instance containing the run time for the simulation.
        compute_cross_section : bool, optional
            Whether to compute the scattering cross-section for each event. Default is False.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing event data for the scatterers.
        """
        event_dataframe = self.fluidics.generate_event_dataframe(
            run_time=run_record.run_time
        )

        self.opto_electronics.model_event(
            event_dataframe=event_dataframe, compute_cross_section=compute_cross_section
        )

        return event_dataframe

    def compute_analog(
        self, run_time: Time, events: pd.DataFrame
    ) -> AcquisitionDataFrame:
        """
        Simulates the analog optical signal response for all detected events.

        This method generates Gaussian-shaped optical pulses based on particle event data
        (time, width, amplitude), adds background optical power, and propagates the resulting
        signal through the detector chain:
        - Optical power → photocurrent → amplified voltage
        - Includes optional noise models (e.g., dark current)
        - Final output is voltage signals stored in an `AcquisitionDataFrame`

        Returns
        -------
        AcquisitionDataFrame
            Structured DataFrame representing the multi-detector analog voltage signals.

        Raises
        ------
        ValueError
            If the event DataFrame is missing required columns ('Widths', 'Time').
        """
        signal_generator = self._create_signal_generator(run_time=run_time)
        signal_generator.signal_units = ureg.watt  # Initial unit: optical power

        for detector in self.opto_electronics.detectors:
            if events.empty:
                signal_generator.add_constant(constant=self.background_power)
            else:
                signal_generator.generate_pulses(
                    signal_name=detector.name,
                    widths=events["Widths"].values.quantity,
                    centers=events["Time"].values.quantity,
                    amplitudes=events[detector.name].values.quantity,
                    base_level=self.background_power,
                )

        # Optical power → photocurrent
        for detector in self.opto_electronics.detectors:
            detector._transform_coupling_power_to_current(
                signal_generator=signal_generator,
                wavelength=self.opto_electronics.source.wavelength,
                bandwidth=self.signal_processing.digitizer.bandwidth,
            )

        # Add dark current noise if enabled
        signal_generator.signal_units = ureg.ampere
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
        signal_generator.signal_units = ureg.volt
        self.opto_electronics.amplifier.amplify(
            signal_generator=signal_generator,
            sampling_rate=self.signal_processing.digitizer.sampling_rate,
        )

        # Final analog signal conditioning
        self.signal_processing.process_analog(signal_generator)

        # Create structured DataFrame output
        analog_aquisition = AcquisitionDataFrame._construct_from_signal_generator(
            signal_generator=signal_generator,
            time_units="second",
            signal_units="volt",
        )

        return analog_aquisition

    def run(self, run_time: Time, compute_cross_section: bool = False) -> RunRecord:
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
        events = self.fluidics.generate_event_dataframe(run_time=run_time)

        self.opto_electronics.model_event(
            event_dataframe=events,
            compute_cross_section=compute_cross_section,
        )

        analog = self.compute_analog(events=events, run_time=run_time)

        run_record = RunRecord(
            run_time=run_time,
            detector_names=[d.name for d in self.opto_electronics.detectors],
            events=events,
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
