#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional
import pandas as pd

from FlowCyPy import units
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.helper import validate_units
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.circuits import SignalProcessor
from FlowCyPy.source import BaseBeam
from FlowCyPy.binary.interface_signal_generator import SignalGenerator
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
            digitizer: SignalDigitizer,
            detectors: List[Detector],
            transimpedance_amplifier: TransimpedanceAmplifier,
            background_power: Optional[units.Quantity] = 0 * units.milliwatt):

        self.scatterer_collection = scatterer_collection
        self.transimpedance_amplifier = transimpedance_amplifier
        self.flow_cell = flow_cell
        self.source = source
        self.detectors = detectors
        self.digitizer = digitizer
        self.background_power = background_power

    def _run_coupling_analysis(self, scatterer_dataframe: pd.DataFrame, compute_cross_section: bool = False) -> None:
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
                signal_digitizer=self.digitizer,
                scatterer_dataframe=scatterer_dataframe,
                medium_refractive_index=self.scatterer_collection.medium_refractive_index,
                compute_cross_section=compute_cross_section
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
        if self.scatterer_dataframe.empty:
            return

        widths = self.source.get_particle_width(
            velocity=scatterer_dataframe['Velocity']
        )

        scatterer_dataframe['Widths'] = widths

    @validate_units(run_time=units.second)
    def prepare_acquisition(self, run_time: units.second, compute_cross_section: bool = False) -> pd.DataFrame:
        """
        Set the internal properties for run_time.

        Parameters
        ----------
        run_time : pint.Quantity
            The duration of the acquisition in seconds.
        compute_cross_section : bool, optional
            If True, computes the cross-section for each scatterer. Defaults to False.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the scatterer data with computed coupling powers and pulse parameters.

        """
        self.run_time = run_time

        self.scatterer_dataframe = self.flow_cell._generate_event_dataframe(self.scatterer_collection.populations, run_time=run_time)

        self.scatterer_collection.fill_dataframe_with_sampling(self.scatterer_dataframe)

        self._run_coupling_analysis(self.scatterer_dataframe, compute_cross_section=compute_cross_section)

        self._generate_pulse_parameters(self.scatterer_dataframe)

        return self.scatterer_dataframe

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
        time_series = self.digitizer.get_time_series(
            run_time=run_time
        )

        signal_generator = SignalGenerator(n_elements=len(time_series))

        signal_generator.add_signal("Time", time_series.to('second').magnitude)

        for detector in self.detectors:
            signal_generator.create_zero_signal(signal_name=detector.name)

        return signal_generator


    @validate_units(run_time=units.second)
    def get_acquisition(self, processing_steps: list[SignalProcessor] = []) -> AcquisitionDataFrame:
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
        signal_generator = self._create_signal_generator(run_time=self.run_time)

        for detector in self.detectors:
            if self.scatterer_dataframe.empty:
                signal_generator.add_constant(constant=self.background_power.to('watt').magnitude)

            else:
                signal_generator.generate_pulses_signal(
                    signal_name=detector.name,
                    widths=self.scatterer_dataframe['Widths'].pint.to('second').values.quantity.magnitude,
                    centers=self.scatterer_dataframe['Time'].pint.to('second').values.quantity.magnitude,
                    coupling_power=self.scatterer_dataframe[detector.name].pint.to('watt').values.quantity.magnitude,
                    background_power=self.background_power.to('watt').magnitude
                )

            # Till here the pulses are in optical power units (watt)
            detector._transform_coupling_power_to_current(
                signal_generator=signal_generator,
                wavelength=self.source.wavelength,
                bandwidth=self.digitizer.bandwidth
            )

            # Now the pulses are in current units (ampere)
            self.transimpedance_amplifier.amplify(
                detector_name=detector.name,
                signal_generator=signal_generator,
                sampling_rate=self.digitizer.sampling_rate
            )

        # Now the pulses are in voltage units (volt)
        for circuit in processing_steps:
            circuit.process(
                signal_generator=signal_generator,
                sampling_rate=self.digitizer.sampling_rate
            )

        return self._make_dataframe_out_of_signal_generator(signal_generator=signal_generator)

    def _make_dataframe_out_of_signal_generator(self, signal_generator: SignalGenerator) -> AcquisitionDataFrame:
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
        df = pd.DataFrame()

        signal_dataframe = df

        signal_dataframe["Time"] = pd.Series(signal_generator.get_signal("Time"), dtype="pint[second]")

        for detector in self.detectors:
            signal_dataframe[detector.name] = pd.Series(signal_generator.get_signal(detector.name), dtype="pint[volt]")

        signal_dataframe = AcquisitionDataFrame(
            signal_dataframe,
            scatterer=self.scatterer_dataframe,
            plot_type='analog'
        )

        signal_dataframe.normalize_units(signal_units='SI', time_units='SI')

        return signal_dataframe

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

