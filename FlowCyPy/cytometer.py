#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd

from FlowCyPy import units
from FlowCyPy import helper
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.circuits import SignalProcessor
from FlowCyPy.signal_generator import SignalGenerator
from FlowCyPy.noises import NoiseSetting
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.fluidics import Fluidics



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
    def __init__(self, opto_electronics: OptoElectronics, fluidics: Fluidics, background_power: Optional[units.Quantity] = 0 * units.milliwatt):
        self.fluidics = fluidics
        self.background_power = background_power
        self.opto_electronics = opto_electronics

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
        time_series = self.opto_electronics.digitizer.get_time_series(
            run_time=run_time
        )

        signal_generator = SignalGenerator(n_elements=len(time_series), time_units=units.second, signal_units=units.watt)

        signal_generator.add_time(time_series)

        for detector in self.opto_electronics.detectors:
            signal_generator.create_zero_signal(signal_name=detector.name)

        return signal_generator

    @helper.validate_input_units(run_time=units.second)
    def get_event_dataframe(self, run_time: units.Quantity, compute_cross_section: bool = False) -> pd.DataFrame:
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
        event_dataframe = self.fluidics.generate_event_dataframe(run_time=run_time)

        self.opto_electronics.model_event(
            event_dataframe=event_dataframe,
            compute_cross_section=compute_cross_section
        )

        return event_dataframe


    @helper.validate_input_units(run_time=units.second)
    def get_acquisition(self, run_time: units.Quantity, processing_steps: list[SignalProcessor] = [], compute_cross_section: bool = False) -> AcquisitionDataFrame:
        """
        Simulates the generation of optical signal pulses for each particle event.

        This method calculates Gaussian signal pulses based on particle positions, coupling power, and
        widths. It adds the generated pulses, background power, and noise components (thermal and dark current)
        to each detector's raw signal.

        Notes
        -----
        - Adds Gaussian pulses to each detector's `raw_signal`.
        - Includes noise and background power in the simulated signals.
        - Updates detector dataframes with captured signal information.

        Parameters
        ----------
        processing_steps : list of SignalProcessor, optional
            List of signal processing steps to apply in order.
        run_time : pint.Quantity
            The duration of the acquisition in seconds.
        compute_cross_section : bool, optional
            If True, computes the cross-section for each scatterer in the event DataFrame.

        Returns
        -------
        Acquisition
            The simulated acquisition experiment.

        Raises
        ------
        ValueError
            If the scatterer collection lacks required data columns ('Widths', 'Time').
        """
        event_dataframe = self.get_event_dataframe(run_time=run_time, compute_cross_section=compute_cross_section)

        signal_generator = self._create_signal_generator(run_time=run_time)

        signal_generator.signal_units = units.watt  # Till here the pulses are in optical power units (watt)
        for detector in self.opto_electronics.detectors:
            if event_dataframe.empty:
                signal_generator.add_constant(constant=self.background_power)

            else:
                signal_generator.generate_pulses(
                    signal_name=detector.name,
                    widths=event_dataframe['Widths'].values.quantity,
                    centers=event_dataframe['Time'].values.quantity,
                    amplitudes=event_dataframe[detector.name].values.quantity,
                    base_level=self.background_power
                )


        for detector in self.opto_electronics.detectors:
            detector._transform_coupling_power_to_current(
                signal_generator=signal_generator,
                wavelength=self.opto_electronics.source.wavelength,
                bandwidth=self.opto_electronics.digitizer.bandwidth
            )

        signal_generator.signal_units = units.ampere  # Now the pulses are in current units (ampere)
        if NoiseSetting.include_dark_current_noise and NoiseSetting.include_noises:
            for detector in self.opto_electronics.detectors:  # Step 3: Add dark current noise to photo-current if enabled
                detector.apply_dark_current_noise(
                    signal_generator=signal_generator,
                    bandwidth=self.opto_electronics.digitizer.bandwidth
                )

        signal_generator.signal_units = units.volt  # Step 4: Convert current to voltage using the transimpedance amplifier
        self.opto_electronics.amplifier.amplify(
            signal_generator=signal_generator,
            sampling_rate=self.opto_electronics.digitizer.sampling_rate
        )

        # Now the pulses are in voltage units (volt)
        for circuit in processing_steps:
            circuit.process(
                signal_generator=signal_generator,
                sampling_rate=self.opto_electronics.digitizer.sampling_rate
            )

        acquisition = self._make_dataframe_out_of_signal_generator(
            event_dataframe=event_dataframe,
            signal_generator=signal_generator
        )
        return acquisition, event_dataframe


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
