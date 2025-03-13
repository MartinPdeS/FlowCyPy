#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
from typing import List, Callable, Optional
import pandas as pd

from FlowCyPy import units
from FlowCyPy.units import milliwatt
from FlowCyPy.flow_cell import BaseFlowCell
from FlowCyPy.detector import Detector
from FlowCyPy.acquisition import Acquisition
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.helper import validate_units
from FlowCyPy import dataframe_subclass
from FlowCyPy.circuits import SignalProcessor
from FlowCyPy.source import BaseBeam


# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


class FlowCytometer:
    """
    A simulation class for modeling flow cytometer signals, including Forward Scatter (FSC) and Side Scatter (SSC) channels.

    The FlowCytometer class integrates optical and flow dynamics to simulate signal generation in a flow cytometer.
    It handles particle distributions, flow cell properties, laser source configurations, and detector behavior to
    replicate realistic cytometry conditions. This includes the generation of synthetic signal pulses for each
    particle event and noise modeling for accurate signal representation.

    Parameters
    ----------
    flow_cell : BaseFlowCell
        The flow cell object representing the fluidic and optical environment through which particles travel.
    detectors : List[Detector]
        A list of `Detector` objects representing the detectors used to measure optical signals (e.g., FSC and SSC). Exactly two detectors must be provided.
    coupling_mechanism : str, optional
        The scattering mechanism used to couple the signal from the particles to the detectors.
        Supported mechanisms include: 'mie' (default): Mie scattering, 'rayleigh': Rayleigh scattering, 'uniform': Uniform signal coupling, 'empirical': Empirical data-driven coupling
    background_power : units.watt, optional
        The background optical power added to the detector signal. Defaults to 0 milliwatts.

    Attributes
    ----------
    flow_cell : BaseFlowCell
        The flow cell instance representing the system environment.
    scatterer_collection : ScattererCollection
        A collection of particles or scatterers passing through the flow cytometer.
    source : GaussianBeam
        The laser beam source providing illumination to the flow cytometer.
    detectors : List[Detector]
        The detectors used to collect and process signals from the scatterers.
    coupling_mechanism : str
        The selected mechanism for signal coupling.
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
            flow_cell: BaseFlowCell,
            signal_digitizer: SignalDigitizer,
            detectors: List[Detector],
            coupling_mechanism: Optional[str] = 'mie',
            background_power: Optional[units.Quantity] = 0 * milliwatt):

        self.scatterer_collection = scatterer_collection
        self.flow_cell = flow_cell
        self.source = source
        self.detectors = detectors
        self.signal_digitizer = signal_digitizer
        self.coupling_mechanism = coupling_mechanism
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
        detection_mechanism = self._get_detection_mechanism()

        if scatterer_dataframe.empty:
            return

        for detector in self.detectors:
            detection_mechanism(
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
        dataframes = []

        # Initialize the detectors
        for detector in self.detectors:
            dataframe = detector.get_initialized_signal(run_time=run_time)

            dataframes.append(dataframe)

        dataframe = pd.concat(dataframes, keys=[d.name for d in self.detectors])

        dataframe.index.names = ["Detector", "Index"]

        return dataframe.sort_index()

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
    def get_acquisition(self, processing_steps: list[SignalProcessor] = None) -> None:
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
        _widths = self.scatterer_dataframe['Widths'].pint.to('second').pint.quantity.magnitude
        _centers = self.scatterer_dataframe['Time'].pint.to('second').pint.quantity.magnitude

        signal_dataframe = self._initialize_signal(run_time=self.run_time)

        for detector_name, group in signal_dataframe.groupby('Detector'):
            detector = self.get_detector_by_name(detector_name)
            total_power = self.background_power

            # Broadcast the time array to the shape of (number of signals, len(detector.time))
            if not self.scatterer_dataframe.empty:
                _coupling_power = self.scatterer_dataframe[detector_name].values

                time_grid = np.expand_dims(group['Time'].pint.magnitude, axis=0) * units.second
                centers = np.expand_dims(_centers, axis=1) * units.second
                widths = np.expand_dims(_widths, axis=1) * units.second

                # Compute the Gaussian for each height, center, and width using broadcasting. To be noted that widths is defined as: waist / (2 * flow_speed)
                power_gaussians = _coupling_power[:, np.newaxis] * np.exp(- (time_grid - centers) ** 2 / (2 * widths ** 2))

                total_power += np.sum(power_gaussians, axis=0)

            # Sum all the Gaussians and add them to the detector.raw_signal
            signal = detector.capture_signal(
                signal=group['Signal'],
                optical_power=total_power,
                wavelength=self.source.wavelength
            ).pint.to(group['Signal'].pint.units)

            signal_dataframe.loc[detector_name, 'Signal'] = signal

        # Apply user-defined processing steps
        self.circuit_process_data(signal_dataframe, processing_steps)

        # Generate noise components
        self.add_noises_to_signal(signal_dataframe)

        saturation_levels = self.get_saturation_levels(signal_dataframe)

        signal_dataframe = dataframe_subclass.AnalogAcquisitionDataFrame(
            signal_dataframe,
            saturation_levels=saturation_levels,
            scatterer_dataframe=self.scatterer_dataframe
        )

        experiment = Acquisition(
            cytometer=self,
            run_time=self.run_time,
            scatterer_dataframe=self.scatterer_dataframe,
            detector_dataframe=signal_dataframe
        )

        return experiment

    def get_saturation_levels(self, signal_dataframe: pd.DataFrame) -> dict:
        saturation_levels = dict()
        for detector_name, group in signal_dataframe.groupby('Detector'):
            saturation_levels[detector_name] = self.signal_digitizer.get_saturation_values(signal=group['Signal'])

        return saturation_levels

    def circuit_process_data(self, signal_dataframe: pd.DataFrame, processing_steps: list) -> None:
        """
        Apply a sequence of user-defined processing steps to the signal data in place.

        This method iterates through the signal dataframe grouped by detector, retrieves the
        raw signal data as a writable NumPy array, and applies each processing step sequentially.
        After processing, it reintroduces the original units and updates the dataframe.

        Parameters
        ----------
        signal_dataframe : pd.DataFrame
            DataFrame containing the signal data to be processed.
        processing_steps : list
            A list of signal processing steps (SignalProcessor instances) that modify the signal data in place.
        """
        for detector_name, group in signal_dataframe.groupby('Detector'):
            detector = self.get_detector_by_name(detector_name)

            if processing_steps:
                temporary = group['Signal'].values.numpy_data  # Get writable NumPy array

                for step in processing_steps:
                    step.apply(temporary, sampling_rate=detector.signal_digitizer.sampling_rate)  # Apply processing in-place

                # Reintroduce units after processing
                signal_dataframe.loc[group.index, 'Signal'] = temporary * group['Signal'].pint.units

    def add_noises_to_signal(self, signal_dataframe: pd.DataFrame) -> None:
        """
        Add noise components to the signal data in the given dataframe.

        For each detector, this method retrieves noise parameters (e.g., thermal and dark current noise),
        generates corresponding noise values using a normal distribution, and adds the noise to the existing
        signal data in place.

        Parameters
        ----------
        signal_dataframe : pd.DataFrame
            DataFrame containing the signal data where noise will be added.
        """
        # Generate noise components
        for detector_name, group in signal_dataframe.groupby('Detector'):
            mean = 0 * units.volt
            std_2 = 0 * units.volt ** 2
            signal_units = group['Signal'].pint.units
            detector = self.get_detector_by_name(detector_name)
            noises = detector.get_noise_parameters()

            for _, parameters in noises.items():
                if parameters is None:
                    continue

                mean += parameters['mean']
                std_2 += parameters['mean'] ** 2


            # Generate noise values for this group
            noise = np.random.normal(
                mean.to(signal_units).magnitude,
                np.sqrt(std_2).to(signal_units).magnitude,
                size=len(group)
            ) * signal_units

            # Update the 'Signal' column in the original DataFrame using .loc
            signal_dataframe.loc[group.index, 'Signal'] = group['Signal'] + noise

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

    def _get_detection_mechanism(self) -> Callable:
        """
        Retrieves the detection mechanism function for signal coupling based on the selected method.

        Supported Coupling Mechanisms
        -----------------------------
        - 'mie': Mie scattering.
        - 'rayleigh': Rayleigh scattering.
        - 'uniform': Uniform scattering.
        - 'empirical': Empirical (data-driven) scattering.

        Returns
        -------
        Callable
            A function that computes the detected signal for scatterer diameters and particle distributions.

        Raises
        ------
        ValueError
            If an unsupported coupling mechanism is specified.
        """
        from FlowCyPy import coupling_mechanism

        # Determine which coupling mechanism to use and compute the corresponding factors
        match self.coupling_mechanism.lower():
            case 'rayleigh':
                return coupling_mechanism.rayleigh.compute_detected_signal
            case 'uniform':
                return coupling_mechanism.uniform.compute_detected_signal
            case 'mie':
                return coupling_mechanism.mie.compute_detected_signal
            case 'empirical':
                return coupling_mechanism.empirical.compute_detected_signal
            case _:
                raise ValueError("Invalid coupling mechanism. Choose 'rayleigh' or 'uniform'.")

