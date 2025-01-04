#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Callable, Optional
from MPSPlots.styles import mps
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.detector import Detector
import pandas as pd
import pint_pandas
from FlowCyPy.units import Quantity, milliwatt
from FlowCyPy.logger import SimulationLogger
import seaborn as sns

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
            flow_cell: FlowCell,
            detectors: List[Detector],
            coupling_mechanism: Optional[str] = 'mie',
            background_power: Optional[Quantity] = 0 * milliwatt):

        self.flow_cell = flow_cell
        self.scatterer_collection = flow_cell.scatterer_collection
        self.source = flow_cell.source
        self.detectors = detectors
        self.coupling_mechanism = coupling_mechanism
        self.background_power = background_power
        self.plot = self.PlotInterface(self)

        assert len(self.detectors) == 2, 'For now, FlowCytometer can only take two detectors for the analysis.'
        assert self.detectors[0].name != self.detectors[1].name, 'Both detectors cannot have the same name'

    def run_coupling_analysis(self) -> None:
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
                scatterer=self.scatterer_collection
            )

            self.scatterer_collection.dataframe["detector: " + detector.name] = pint_pandas.PintArray(self.coupling_power, dtype=self.coupling_power.units)

        self._generate_pulse_parameters()

    def initialize_signal(self) -> None:
        """
        Initializes the raw signal for each detector based on the source and flow cell configuration.

        This method prepares the detectors for signal capture by associating each detector with the
        light source and generating a time-dependent raw signal placeholder.

        Effects
        -------
        Each detector's `raw_signal` attribute is initialized with time-dependent values
        based on the flow cell's runtime.

        """
        # Initialize the detectors
        for detector in self.detectors:
            detector.source = self.source
            detector.init_raw_signal(run_time=self.flow_cell.run_time)

    def simulate_pulse(self) -> None:
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
        logging.debug("Starting pulse simulation.")

        _widths = self.scatterer_collection.dataframe['Widths'].values
        _centers = self.scatterer_collection.dataframe['Time'].values

        for detector in self.detectors:
            _coupling_power = self.scatterer_collection.dataframe["detector: " + detector.name].values

            # Generate noise components
            detector._add_thermal_noise_to_raw_signal()

            detector._add_dark_current_noise_to_raw_signal()

            # Broadcast the time array to the shape of (number of signals, len(detector.time))
            time_grid = np.expand_dims(detector.dataframe.Time.values.numpy_data, axis=0) * _centers.units

            centers = np.expand_dims(_centers.numpy_data, axis=1) * _centers.units
            widths = np.expand_dims(_widths.numpy_data, axis=1) * _widths.units

            # Compute the Gaussian for each height, center, and width using broadcasting
            power_gaussians = _coupling_power[:, np.newaxis] * np.exp(- (time_grid - centers) ** 2 / (2 * widths ** 2))

            total_power = np.sum(power_gaussians, axis=0) + self.background_power

            # Sum all the Gaussians and add them to the detector.raw_signal
            detector._add_optical_power_to_raw_signal(optical_power=total_power)

            detector.capture_signal()

        self._log_statistics()

    def _log_statistics(self) -> SimulationLogger:
        """
        Logs and displays key statistics about the simulated events.

        This includes metrics such as:
        - Total number of events processed.
        - Average time between events.
        - First and last event times.
        - Minimum time intervals between events.

        Returns
        -------
        SimulationLogger
            An instance of the logger containing all recorded statistics.

        Effects
        -------
        Outputs formatted tables to the console or log file, depending on the logger's configuration.
        """
        logger = SimulationLogger(cytometer=self)

        logger.log_statistics(include_totals=True, table_format="fancy_grid")

        return logger

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

    def _generate_pulse_parameters(self) -> None:
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

        self.pulse_dataframe['Centers'] = self.scatterer_collection.dataframe['Time']

        widths = self.source.waist / self.flow_cell.flow_speed * np.ones(self.scatterer_collection.n_events)

        self.scatterer_collection.dataframe['Widths'] = pint_pandas.PintArray(widths, dtype=widths.units)

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

    class PlotInterface:
        def __init__(self, cytometer):
            self.cytometer = cytometer

        def signals(self, figure_size: tuple = (10, 6), add_peak_locator: bool = False, show: bool = True) -> None:
            """
            Visualizes the raw signals for all detector channels along with the scatterer distribution.

            Parameters
            ----------
            figure_size : tuple, optional
                Dimensions of the generated plot (default: (10, 6)).
            add_peak_locator : bool, optional
                If True, adds visual markers for detected signal peaks (default: False).

            Effects
            -------
            Displays a multi-panel plot showing:
            - Raw signals for each detector channel.
            - Scatterer distribution along the time axis.
            """
            logging.info("Plotting the signal for the different channels.")

            scatterer_collection = self.cytometer.scatterer_collection
            detectors = self.cytometer.detectors

            n_detectors = len(detectors)

            with plt.style.context(mps):
                _, axes = plt.subplots(ncols=1, nrows=n_detectors + 1, figsize=figure_size, sharex=True, sharey=True, gridspec_kw={'height_ratios': [1, 1, 0.4]})

            time_unit, signal_unit = detectors[0].plot(ax=axes[0], show=False, add_peak_locator=add_peak_locator)
            detectors[1].plot(ax=axes[1], show=False, time_unit=time_unit, signal_unit=signal_unit, add_peak_locator=add_peak_locator)

            axes[-1].get_yaxis().set_visible(False)
            scatterer_collection.add_to_ax(axes[-1])

            # Add legends to each subplot
            for ax in axes:
                ax.legend()

            if show: # Display the plot
                plt.show()

        def coupling_distribution(self, log_scale: bool = False, show: bool = True, equal_limits: bool = False, save_path: str = None) -> None:
            """
            Plots the density distribution of optical coupling in the FSC and SSC channels.

            This method generates a joint plot showing the relationship between the signals from
            the forward scatter ('detector: forward') and side scatter ('detector: side') detectors.
            The plot is color-coded by particle population and can optionally display axes on a logarithmic scale.

            Parameters
            ----------
            log_scale : bool, optional
                If True, applies a logarithmic scale to both the x and y axes of the plot (default: False).
            show : bool, optional
                If True, displays the plot immediately. If False, the plot is created but not displayed,
                allowing for further customization or saving externally (default: True).
            equal_limits : bool, optional
                If True, sets the same limits for both the x and y axes based on the maximum range
                across both axes. If False, the limits are set automatically based on the data (default: False).

            """
            scatterer_collection = self.cytometer.scatterer_collection
            detector_0, detector_1 = self.cytometer.detectors

            with plt.style.context(mps):
                joint_plot = sns.jointplot(
                    data=scatterer_collection.dataframe,
                    x=f'detector: {detector_0.name}',
                    y=f'detector: {detector_1.name}',
                    hue="Population",
                    alpha=0.8,
                )

            if log_scale:
                joint_plot.ax_joint.set_xscale('log')
                joint_plot.ax_joint.set_yscale('log')

            if equal_limits:
                # Get data limits
                x_data = scatterer_collection.dataframe[f'detector: {detector_0.name}']
                y_data = scatterer_collection.dataframe[f'detector: {detector_1.name}']

                x_min, x_max = x_data.min(), x_data.max()
                y_min, y_max = y_data.min(), y_data.max()

                # Find the overall min and max
                overall_min = min(x_min, y_min)
                overall_max = max(x_max, y_max)

                # Set equal limits
                joint_plot.ax_joint.set_xlim(overall_min, overall_max)
                joint_plot.ax_joint.set_ylim(overall_min, overall_max)

            if save_path:
                joint_plot.figure.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Plot saved to {save_path}")

            if show:  # Display the plot
                plt.show()