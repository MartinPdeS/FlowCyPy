#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
from typing import List, Callable, Optional
from MPSPlots.styles import mps
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.detector import Detector
import pandas as pd
import pint_pandas
from FlowCyPy import units
from FlowCyPy.units import Quantity, milliwatt
from pint_pandas import PintArray
from FlowCyPy.experiment import ContinuousAcquisition, TriggeredAcquisition


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
    flow_cell : FlowCell
        The flow cell object representing the fluidic and optical environment through which particles travel.
    detectors : List[Detector]
        A list of `Detector` objects representing the detectors used to measure optical signals (e.g., FSC and SSC). Exactly two detectors must be provided.
    coupling_mechanism : str, optional
        The scattering mechanism used to couple the signal from the particles to the detectors.
        Supported mechanisms include: 'mie' (default): Mie scattering, 'rayleigh': Rayleigh scattering, 'uniform': Uniform signal coupling, 'empirical': Empirical data-driven coupling
    background_power : Quantity, optional
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
    coupling_mechanism : str
        The selected mechanism for signal coupling.
    background_power : Quantity
        The optical background power added to the detector signals.

    Raises
    ------
    AssertionError
        If the number of detectors provided is not exactly two, or if both detectors share the same name.

    """
    def __init__(
            self,
            scatterer_collection: object,
            flow_cell: FlowCell,
            detectors: List[Detector],
            coupling_mechanism: Optional[str] = 'mie',
            background_power: Optional[Quantity] = 0 * milliwatt):

        self.scatterer_collection = scatterer_collection
        self.flow_cell = flow_cell
        self.source = flow_cell.source
        self.detectors = detectors
        self.coupling_mechanism = coupling_mechanism
        self.background_power = background_power

        assert len(self.detectors) == 2, 'For now, FlowCytometer can only take two detectors for the analysis.'
        assert self.detectors[0].name != self.detectors[1].name, 'Both detectors cannot have the same name'

        for detector in detectors:
            detector.cytometer = self

    def run_coupling_analysis(self, scatterer_dataframe: pd.DataFrame) -> None:
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

        for detector in self.detectors:
            self.coupling_power = detection_mechanism(
                source=self.source,
                detector=detector,
                scatterer_dataframe=scatterer_dataframe,
                medium_refractive_index=self.scatterer_collection.medium_refractive_index
            )

            scatterer_dataframe["detector: " + detector.name] = pint_pandas.PintArray(self.coupling_power, dtype=self.coupling_power.units)

    def _generate_pulse_parameters(self, scatterer_dataframe: pd.DataFrame) -> None:
        """
        Generates and assigns random Gaussian pulse parameters for each particle event.

        The generated parameters include:
        - Centers: The time at which each pulse occurs.
        - Widths: The standard deviation (spread) of each pulse in seconds.

        Effects
        -------
        scatterer_collection.dataframe : pandas.DataFrame
            Adds a 'Widths' column with computed pulse widths for each particle.
            Uses the flow speed and beam waist to calculate pulse widths.
        """
        columns = pd.MultiIndex.from_product(
            [[p.name for p in self.detectors], ['Centers', 'Heights']]
        )

        self.pulse_dataframe = pd.DataFrame(columns=columns)

        self.pulse_dataframe['Centers'] = scatterer_dataframe['Time']

        widths = self.source.waist / self.flow_cell.flow_speed * np.ones(len(scatterer_dataframe))

        scatterer_dataframe['Widths'] = pint_pandas.PintArray(widths, dtype=widths.units)

    def initialize_signal(self, run_time: Quantity) -> None:
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

        self.dataframe = pd.concat(dataframes, keys=[d.name for d in self.detectors])

        self.dataframe.index.names = ["Detector", "Index"]

    def get_trigger_indices(
        self,
        threshold: Quantity,
        trigger_detector_name: str = None,
        custom_trigger: np.ndarray = None,
        pre_buffer: int = 64,
        post_buffer: int = 64
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Computes the start and end indices of segments based on the trigger condition.

        Parameters
        ----------
        threshold : Quantity
            The signal value threshold for the trigger detector.
        trigger_detector_name : str, optional
            The name of the detector to be used as the triggering system. Ignored if `custom_trigger` is provided.
        custom_trigger : np.ndarray, optional
            A custom boolean trigger array indicating where the signal should be extracted.
            Must have the same length as the acquisition time.
        pre_buffer : int, optional
            Number of points to include before each threshold crossing, by default 64.
        post_buffer : int, optional
            Number of points to include after each threshold crossing, by default 64.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Two arrays: `start_indices` and `end_indices` for the triggered segments.

        Raises
        ------
        ValueError
            If the `custom_trigger` array is invalid or the specified trigger detector is not found.
        """
        if custom_trigger is not None:
            # Validate custom trigger
            if len(custom_trigger) != len(self.dataframe.xs(self.detectors[0].name)['Signal'].pint.magnitude):
                raise ValueError("Custom trigger array length must match the acquisition signal length.")
            trigger_signal = custom_trigger
        else:
            # Use trigger detector
            if trigger_detector_name not in [detector.name for detector in self.detectors]:
                raise ValueError(f"Trigger detector '{trigger_detector_name}' not found.")

            trigger_signal = self.dataframe.xs(trigger_detector_name)['Signal']
            trigger_units = self.dataframe.xs(trigger_detector_name)['Signal'].pint.units

            trigger_signal = trigger_signal > threshold.to(trigger_units)


        # Identify threshold crossings
        crossing_indices = np.where(np.diff(trigger_signal.astype(int)) == 1)[0]

        # Compute start and end indices using pre-buffer and post-buffer
        start_indices = np.clip(crossing_indices - pre_buffer, 0, len(trigger_signal) - 1)
        end_indices = np.clip(crossing_indices + post_buffer, 0, len(trigger_signal) - 1)

        return start_indices, end_indices

    def get_triggered_acquisition(
        self,
        run_time: Quantity,
        threshold: Quantity,
        trigger_detector_name: str = None,
        custom_trigger: np.ndarray = None,
        pre_buffer: int = 64,
        post_buffer: int = 64,
        maximum_number_of_triggers: int = None,
    ) -> pd.DataFrame:
        """
        Extracts thresholded signal segments based on a trigger detector or custom trigger array
        and returns them in a multi-index DataFrame.

        Parameters
        ----------
        run_time : Quantity
            The duration of the simulation (must be in seconds).
        threshold : Quantity
            The signal value threshold for the trigger detector.
        trigger_detector_name : str, optional
            The name of the detector to be used as the triggering system. Ignored if `custom_trigger` is provided.
        custom_trigger : np.ndarray, optional
            A custom boolean trigger array indicating where the signal should be extracted.
            Must have the same length as the acquisition time.
        pre_buffer : int, optional
            Number of points to include before each threshold crossing, by default 64.
        post_buffer : int, optional
            Number of points to include after each threshold crossing, by default 64.
        maximum_number_of_triggers : int, optional
            The maximum number of triggers to process. If None, all triggers will be processed.

        Returns
        -------
        pd.DataFrame
            A multi-index DataFrame with the first level as the detector name and the second level as the segment ID.
            Includes columns for time and signal.

        Raises
        ------
        ValueError
            If `run_time` is not in seconds, the trigger detector is not found, or the `custom_trigger` array is invalid.
        """
        # Ensure the acquisition data is generated
        self.get_continous_acquisition(run_time)

        # Get trigger indices
        start_indices, end_indices = self.get_trigger_indices(
            threshold, trigger_detector_name, custom_trigger, pre_buffer, post_buffer
        )

        # Limit the number of triggers if specified
        if maximum_number_of_triggers is not None:
            start_indices = start_indices[:maximum_number_of_triggers]
            end_indices = end_indices[:maximum_number_of_triggers]

        # List to store data for concatenation
        all_segments = []

        # Process each detector using the trigger segments
        for detector in self.detectors:
            signal = self.dataframe.xs(detector.name)['Signal'].pint.magnitude
            time = self.dataframe.xs(detector.name)['Time'].pint.magnitude

            for i, (start, end) in enumerate(zip(start_indices, end_indices)):
                segment = pd.DataFrame({
                    'Time': time[start:end + 1],
                    'Signal': signal[start:end + 1]
                })
                segment['Detector'] = detector.name
                segment['SegmentID'] = i
                all_segments.append(segment)

        # Concatenate all segments into a single DataFrame
        result = pd.concat(all_segments, ignore_index=True)

        # Set Multi-Index with Detector and SegmentID
        result = result.set_index(['Detector', 'SegmentID'])

        return TriggeredAcquisition(result)

    def get_continous_acquisition(self, run_time: Quantity) -> None:
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

        Raises
        ------
        ValueError
            If the scatterer collection lacks required data columns ('Widths', 'Time').
        """
        if not run_time.check('second'):
            raise ValueError(f"flow_speed must be in meter per second, but got {run_time.units}")

        self.initialize_signal(run_time=run_time)

        scatterer_dataframe = self.flow_cell.generate_event_dataframe(self.scatterer_collection.populations, run_time=run_time)

        self.scatterer_collection.fill_dataframe_with_sampling(scatterer_dataframe)

        self.run_coupling_analysis(scatterer_dataframe)

        self._generate_pulse_parameters(scatterer_dataframe)

        self.scatterer_collection.dataframe = scatterer_dataframe

        _widths = scatterer_dataframe['Widths'].pint.to('second').pint.quantity.magnitude
        _centers = scatterer_dataframe['Time'].pint.to('second').pint.quantity.magnitude

        for detector in self.detectors:
            _coupling_power = scatterer_dataframe["detector: " + detector.name].values

            detector_signal = self.dataframe.xs(detector.name)['Signal']

            # Generate noise components
            detector._add_thermal_noise_to_raw_signal(signal=detector_signal)

            detector._add_dark_current_noise_to_raw_signal(signal=detector_signal)

            # Broadcast the time array to the shape of (number of signals, len(detector.time))
            time = self.dataframe.xs(detector.name)['Time'].pint.magnitude

            time_grid = np.expand_dims(time, axis=0) * units.second

            centers = np.expand_dims(_centers, axis=1) * units.second
            widths = np.expand_dims(_widths, axis=1) * units.second

            # Compute the Gaussian for each height, center, and width using broadcasting
            power_gaussians = _coupling_power[:, np.newaxis] * np.exp(- (time_grid - centers) ** 2 / (2 * widths ** 2))

            total_power = np.sum(power_gaussians, axis=0) + self.background_power

            # Sum all the Gaussians and add them to the detector.raw_signal
            detector._add_optical_power_to_raw_signal(
                signal=detector_signal,
                optical_power=total_power,
                wavelength=self.flow_cell.source.wavelength
            )

            digitized_signal, _ = detector.capture_signal(signal=detector_signal)

            self.dataframe.loc[detector.name, 'Signal'] = PintArray(detector_signal, detector_signal.pint.units)

            self.dataframe.loc[detector.name, 'DigitizedSignal'] = PintArray(digitized_signal, units.bit_bins)

        experiment = ContinuousAcquisition(
            run_time=run_time,
            scatterer_dataframe=scatterer_dataframe,
            detector_dataframe=self.dataframe
        )

        return experiment

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
            A function that computes the detected signal for scatterer sizes and particle distributions.

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

    def add_detector(self, **kwargs) -> Detector:
        """
        Dynamically adds a new detector to the system configuration.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments passed to the `Detector` constructor.

        Returns
        -------
        Detector
            The newly added detector instance.

        Effects
        -------
        - Appends the created detector to the `detectors` list.
        """
        detector = Detector(**kwargs)

        self.detectors.append(detector)

        return detector

