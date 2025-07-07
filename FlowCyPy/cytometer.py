#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd

from FlowCyPy import units
from FlowCyPy import helper
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.signal_generator import SignalGenerator
from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.fluidics import Fluidics
from FlowCyPy.signal_processing import SignalProcessing


class Result():
    analog: Optional[AcquisitionDataFrame] = None
    triggered_analog: Optional[AcquisitionDataFrame] = None
    events: Optional[pd.DataFrame] = None
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

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
    @helper.validate_input_units(background_power=units.watt)
    def __init__(self, opto_electronics: OptoElectronics, fluidics: Fluidics, signal_processing: SignalProcessing, background_power: Optional[units.Quantity] = 0 * units.milliwatt):
        self.fluidics = fluidics
        self.background_power = background_power
        self.opto_electronics = opto_electronics
        self.signal_processing = signal_processing

    def _create_signal_generator(self, run_time: units.second) -> SignalGenerator:
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

        signal_generator = SignalGenerator(n_elements=len(time_series), time_units=units.second, signal_units=units.watt)

        signal_generator.add_time(time_series)

        for detector in self.opto_electronics.detectors:
            signal_generator.create_zero_signal(signal_name=detector.name)

        return signal_generator

    @helper.validate_input_units(run_time=units.second)
    def initialize(self, run_time: units.Quantity) -> Result:
        """
        Initializes the flow cytometer simulation.

        Parameters
        ----------
        run_time : pint.Quantity
            The duration of the acquisition in seconds.

        Returns
        -------
        Result
            An instance of the Result class containing initialization data.
        """
        self.results = Result()
        self.results.run_time = run_time

        return self.results

    def compute_events(self, compute_cross_section: bool = False) -> pd.DataFrame:
        """
        Generates a DataFrame of events based on the scatterer collection and flow cell properties.

        This method samples particle events from the fluidics system and prepares a DataFrame
        containing the event times, positions, and other relevant properties.

        Parameters
        ----------
        run_time : pint.Quantity
            The duration of the acquisition in seconds.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing event data for the scatterers.
        """
        event_dataframe = self.fluidics.generate_event_dataframe(run_time=self.results.run_time)

        self.opto_electronics.model_event(
            event_dataframe=event_dataframe,
            compute_cross_section=compute_cross_section
        )

        self.results.events = event_dataframe

        return event_dataframe

    def compute_analog(self) -> AcquisitionDataFrame:
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
        signal_generator = self._create_signal_generator(run_time=self.results.run_time)
        signal_generator.signal_units = units.watt  # Initial unit: optical power

        for detector in self.opto_electronics.detectors:
            if self.results.events.empty:
                signal_generator.add_constant(constant=self.background_power)
            else:
                signal_generator.generate_pulses(
                    signal_name=detector.name,
                    widths=self.results.events['Widths'].values.quantity,
                    centers=self.results.events['Time'].values.quantity,
                    amplitudes=self.results.events[detector.name].values.quantity,
                    base_level=self.background_power
                )

        # Optical power → photocurrent
        for detector in self.opto_electronics.detectors:
            detector._transform_coupling_power_to_current(
                signal_generator=signal_generator,
                wavelength=self.opto_electronics.source.wavelength,
                bandwidth=self.signal_processing.digitizer.bandwidth
            )

        # Add dark current noise if enabled
        signal_generator.signal_units = units.ampere
        if SimulationSettings.include_noises and SimulationSettings.include_dark_current_noise:
            for detector in self.opto_electronics.detectors:
                detector.apply_dark_current_noise(
                    signal_generator=signal_generator,
                    bandwidth=self.signal_processing.digitizer.bandwidth
                )

        # Photocurrent → voltage
        signal_generator.signal_units = units.volt
        self.opto_electronics.amplifier.amplify(
            signal_generator=signal_generator,
            sampling_rate=self.signal_processing.digitizer.sampling_rate
        )

        # Final analog signal conditioning
        self.signal_processing.process_analog(signal_generator)

        # Create structured DataFrame output
        self.results.analog = self._make_dataframe_out_of_signal_generator(
            event_dataframe=self.results.events,
            signal_generator=signal_generator
        )

        return self.results.analog

    def compute_peaks(self):
        """
        Runs the triggering system and extracts signal segments corresponding to detected events.

        The method identifies regions in the analog voltage signals where the threshold condition is met
        (based on `triggering_system`). It then digitizes the triggered signal segments and applies
        peak detection, if configured.

        Returns
        -------
        Result
            The internal `results` object populated with:
            - `triggered_analog_acquisition`
            - `digital_acquisition`
            - `peaks` (if `peak_algorithm` is provided)
        """
        self.results.triggered_analog = self.signal_processing.triggering_system.run(
            dataframe=self.results.analog
        )

        self.signal_processing.process_digital(self.results)

        return self.results.peaks


    def _make_dataframe_out_of_signal_generator(self, event_dataframe: pd.DataFrame, signal_generator: SignalGenerator) -> AcquisitionDataFrame:
        """
        Converts a signal generator's output into a pandas DataFrame.

        Parameters
        ----------
        signal_generator : SignalGenerator
            The signal generator instance containing the generated signals.

        Returns
        -------
        AcquisitionDataFrame
            A DataFrame containing the signals from the signal generator.
        """
        signal_dataframe = pd.DataFrame()

        time = signal_generator.get_time()

        signal_dataframe["Time"] = pd.Series(time, dtype="pint[second]")

        for detector in self.opto_electronics.detectors:
            signal_dataframe[detector.name] = pd.Series(signal_generator.get_signal(detector.name), dtype="pint[volt]")

        signal_dataframe = AcquisitionDataFrame(
            signal_dataframe,
            scatterer=event_dataframe,
            plot_type='analog'
        )

        signal_dataframe.normalize_units(signal_units='SI', time_units='SI')

        return signal_dataframe

    def run(self, run_time: units.Quantity, compute_cross_section: bool = False) -> Result:
        """
        Runs a complete flow cytometry simulation for the specified acquisition duration.

        The pipeline includes:
        1. Initialization and setup of fluidic/optical components
        2. Particle event simulation and optical signal generation
        3. Analog and digital signal processing
        4. Triggered signal extraction and peak feature detection

        Parameters
        ----------
        run_time : Quantity
            Duration of the simulated acquisition (e.g., `1.0 * units.millisecond`).

        Returns
        -------
        Result
            Simulation output containing all analog, digital, and peak-level data.
        """
        self.results = None
        self.initialize(run_time=run_time)
        self.compute_events(compute_cross_section=compute_cross_section)
        self.compute_analog()

        if self.signal_processing.triggering_system is not None:
            self.compute_peaks()

        return self.results




from FlowCyPy._flow_cytometer_instances import *
