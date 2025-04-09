#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from typing import List, Optional
import pandas as pd
import pint_pandas

from FlowCyPy import units
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.detector import Detector
from FlowCyPy.acquisition import Acquisition
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.helper import validate_units
from FlowCyPy import dataframe_subclass
from FlowCyPy.circuits import SignalProcessor
from FlowCyPy.source import BaseBeam
from FlowCyPy.binary import interface_signal_generator
from FlowCyPy.noises import NoiseSetting
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy.coupling import compute_detected_signal

class FlowCytometer:
    """
    A simulation class for modeling flow cytometer signals, including Forward Scatter (FSC) and Side Scatter (SSC) channels.

    The FlowCytometer class integrates optical and flow dynamics to simulate signal generation in a flow cytometer.
    It handles particle distributions, flow cell properties, laser source configurations, and detector behavior to
    replicate realistic cytometry conditions. This includes the generation of synthetic signal pulses for each
    particle event and noise modeling for accurate signal representation.

    Parameters
    ----------
    flow_cell : FlowCell
        The flow cell object representing the fluidic and optical environment through which particles travel.
    detectors : List[Detector]
        A list of `Detector` objects representing the detectors used to measure optical signals (e.g., FSC and SSC). Exactly two detectors must be provided.
    background_power : units.watt, optional
        The background optical power added to the detector signal. Defaults to 0 milliwatts.

    Attributes
    ----------
    flow_cell : FlowCell
        The flow cell instance representing the system environment.
    scatterer_collection : ScattererCollection
        A collection of particles or scatterers passing through the flow cytometer.
    source : GaussianBeam
        The laser beam source providing illumination to the flow cytometer.
    detectors : List[Detector]
        The detectors used to collect and process signals from the scatterers.
    background_power : units.watt
        The optical background power added to the detector signals.

    Raises
    ------
    AssertionError
        If the number of detectors provided is not exactly two, or if both detectors share the same name.

    """
    def __init__(
            self,
            source: BaseBeam,
            scatterer_collection: object,
            flow_cell: FlowCell,
            signal_digitizer: SignalDigitizer,
            detectors: List[Detector],
            transimpedance_amplifier: TransimpedanceAmplifier,
            background_power: Optional[units.Quantity] = 0 * units.milliwatt):

        self.scatterer_collection = scatterer_collection
        self.transimpedance_amplifier = transimpedance_amplifier
        self.flow_cell = flow_cell
        self.source = source
        self.detectors = detectors
        self.signal_digitizer = signal_digitizer
        self.background_power = background_power

        # assert len(self.detectors) == 2, 'For now, FlowCytometer can only take two detectors for the analysis.'
        assert self.detectors[0].name != self.detectors[1].name, 'Both detectors cannot have the same name'

        for detector in detectors:
            detector.cytometer = self

        for detector in self.detectors:
            detector.signal_digitizer = signal_digitizer

    def _run_coupling_analysis(self, scatterer_dataframe: pd.DataFrame) -> None:
        """
        Computes and assigns the optical coupling power for each particle-detection event.

        This method evaluates the coupling between the scatterers in the flow cell and the detectors
        using the specified detection mechanism. The computed coupling power is stored in the
        `scatterer_collection` dataframe under detector-specific columns.

        Updates
        -------
        scatterer_collection.dataframe : pandas.DataFrame
            Adds columns for each detector, labeled as "detector: <detector_name>", containing the computed
            coupling power for all particle events.

        Raises
        ------
        ValueError
            If an invalid coupling mechanism is specified during initialization.
        """
        if scatterer_dataframe.empty:
            return

        for detector in self.detectors:
            compute_detected_signal(
                source=self.source,
                detector=detector,
                scatterer_dataframe=scatterer_dataframe,
                medium_refractive_index=self.scatterer_collection.medium_refractive_index
            )

    def _generate_pulse_parameters(self, scatterer_dataframe: pd.DataFrame) -> None:
        r"""
        Generates and assigns random Gaussian pulse parameters for each particle event.

        The pulse shape follows the Gaussian beam"s spatial intensity profile:

        .. math::

            I(r) = I_0 \exp\left(-\frac{2r^2}{w_0^2}\right),

        where :math:`w_0` is the beam waist (the :math:`1/e^2` radius of the intensity distribution).
        This profile can be rewritten in standard Gaussian form:

        .. math::

            I(r) = I_0 \exp\left(-\frac{r^2}{2\sigma_x^2}\right),

        which implies the spatial standard deviation:

        .. math::

            \sigma_x = \frac{w_0}{2}.

        When a particle moves at a constant flow speed :math:`v`, the spatial coordinate :math:`r`
        is related to time :math:`t` via :math:`r = v t`. Substituting this into the intensity profile
        gives a temporal Gaussian:

        .. math::

            I(t) = I_0 \exp\left(-\frac{2 (v t)^2}{w_0^2}\right).

        This is equivalent to a Gaussian in time:

        .. math::

            I(t) = I_0 \exp\left(-\frac{t^2}{2\sigma_t^2}\right),

        so that the temporal standard deviation is:

        .. math::

            \sigma_t = \frac{\sigma_x}{v} = \frac{w_0}{2v}.

        The full width at half maximum (FWHM) in time is then:

        .. math::

            \text{FWHM} = 2\sqrt{2 \ln2} \, \sigma_t = \frac{w_0}{v} \sqrt{2 \ln2}.

        **Generated Parameters:**
        - **Centers:** The time at which each pulse occurs (randomly determined).
        - **Widths:** The pulse width (:math:`\sigma_t`) in seconds, computed as :math:`w_0 / (2 v)`.

        **Effects**
        -----------
        Modifies `scatterer_dataframe` in place by adding:
        - A `'Centers'` column with the pulse center times.
        - A `'Widths'` column with the computed pulse widths.
        """
        # Calculate the pulse width (standard deviation in time, σₜ) based on the beam waist and flow speed.
        scatterer_dataframe['Widths'] = self.source.get_particle_width(velocity=scatterer_dataframe['Velocity'])


    def _initialize_signal(self, run_time: units.second) -> None:
        """
        Initializes the raw signal for each detector based on the source and flow cell configuration.

        This method prepares the detectors for signal capture by associating each detector with the
        light source and generating a time-dependent raw signal placeholder.

        Effects
        -------
        Each detector's `raw_signal` attribute is initialized with time-dependent values
        based on the flow cell's runtime.

        """
        detector_names = [d.name for d in self.detectors]

        time_series = self.signal_digitizer.get_time_series(
            run_time=run_time
        )

        self.sequence_length = len(time_series)

        signal = np.zeros(self.sequence_length)

        time_series = pint_pandas.PintArray(time_series.magnitude, time_series.units)

        df = pd.DataFrame(index=range(self.sequence_length), columns=[*detector_names, 'Time'])

        df['Time'] = time_series

        for detector in detector_names:
            df[detector] = pint_pandas.PintArray(signal, dtype='volt')

        return df


    @validate_units(run_time=units.second)
    def prepare_acquisition(self, run_time: units.second) -> pd.DataFrame:
        """
        Set the internal properties for run_time.

        Parameters
        ----------
        run_time : pint.Quantity
            The duration of the acquisition in seconds.

        """
        self.run_time = run_time

        self.scatterer_dataframe = self.flow_cell._generate_event_dataframe(self.scatterer_collection.populations, run_time=run_time)

        self.scatterer_collection.fill_dataframe_with_sampling(self.scatterer_dataframe)

        self._run_coupling_analysis(self.scatterer_dataframe)

        self._generate_pulse_parameters(self.scatterer_dataframe)

        return self.scatterer_dataframe


    @validate_units(run_time=units.second)
    def get_acquisition(self, processing_steps: list[SignalProcessor] = []) -> Acquisition:
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

        Returns
        -------
        Acquisition
            The simulated acquisition experiment.

        Raises
        ------
        ValueError
            If the scatterer collection lacks required data columns ('Widths', 'Time').
        """
        signal_dataframe = self._initialize_signal(run_time=self.run_time)

        # signal_dict = dict()

        for column in signal_dataframe:
            if column == 'Time':
                continue

            detector = self.get_detector_by_name(column)

            if not self.scatterer_dataframe.empty:
                coupling_power = np.zeros(self.sequence_length, dtype='float64')

                interface_signal_generator.generate_pulses(
                    signal=coupling_power,
                    widths=self.scatterer_dataframe['Widths'].pint.to('second').values.quantity.magnitude,
                    centers=self.scatterer_dataframe['Time'].pint.to('second').values.quantity.magnitude,
                    coupling_power=self.scatterer_dataframe[column].pint.to('watt').values.quantity.magnitude,
                    time=signal_dataframe['Time'].pint.to('second').values.quantity.magnitude,
                    background_power=self.background_power.to('watt').magnitude
                )

                coupling_power = coupling_power * units.watt

            if not NoiseSetting.include_shot_noise or not NoiseSetting.include_noises:
                photocurrent = (coupling_power * detector.responsivity)
            else:
                photocurrent = detector.get_shot_noise(optical_power=coupling_power, wavelength=self.source.wavelength, bandwidth=self.signal_digitizer.bandwidth)

            if NoiseSetting.include_dark_current_noise and NoiseSetting.include_noises:
                photocurrent += detector.get_dark_current_noise(sequence_length=self.sequence_length, bandwidth=self.signal_digitizer.bandwidth)

            signal = self.transimpedance_amplifier.amplify(signal=photocurrent, dt=1 / self.signal_digitizer.sampling_rate).to('volt')

            for step in processing_steps:
                step.apply(signal, sampling_rate=self.signal_digitizer.sampling_rate)  # Apply processing in-place

            signal_dataframe[column] = pd.Series(signal, dtype="pint[volt]")


        signal_dataframe = dataframe_subclass.AnalogAcquisitionDataFrame(
            signal_dataframe,
            scatterer_dataframe=self.scatterer_dataframe
        )

        experiment = Acquisition(
            cytometer=self,
            run_time=self.run_time,
            scatterer_dataframe=self.scatterer_dataframe,
            detector_dataframe=signal_dataframe
        )

        experiment.sample_volume = (self.flow_cell.sample.volume_flow * self.run_time).to_compact()

        return experiment

    def run_processing(self, *processing_steps) -> None:
        signal = self.signal.copy()
        for step in processing_steps:
            step.apply(signal, sampling_rate=self.signal_digitizer.sampling_rate)  # Apply processing in-place

        return signal
        signal_dataframe[column] = pd.Series(signal, dtype="pint[volt]")


    def get_detector_by_name(self, name: str) -> Detector:
        """
        Retrieve a detector object by its name.

        Parameters
        ----------
        name : str
            The name of the detector to retrieve.

        Returns
        -------
        Detector
            The detector object corresponding to the specified name.
        """
        for detector in self.detectors:
            if detector.name == name:
                return detector

