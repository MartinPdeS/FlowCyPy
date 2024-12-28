#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Callable, Optional
from MPSPlots.styles import mps
from FlowCyPy.scatterer import Scatterer
from FlowCyPy.detector import Detector
from FlowCyPy.source import GaussianBeam
import pandas as pd
import pint_pandas
from FlowCyPy.units import Quantity, milliwatt
from FlowCyPy.logger import SimulationLogger

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


class FlowCytometer:
    """
    A class to simulate flow cytometer signals for Forward Scatter (FSC) and Side Scatter (SSC) channels.

    This class models the particle distribution, flow characteristics, and detector configurations to
    simulate the signal generated as particles pass through the flow cytometer's laser.

    Parameters
    ----------
    scatterer : Scatterer
        The distribution of particle sizes which affects scattering signals.
    source : GaussianBeam
        The laser source object representing the illumination scheme.
    detectors : List[Detector]
        List of `Detector` objects representing the detectors in the system.

    """
    def __init__(
            self,
            scatterer: Scatterer,
            source: GaussianBeam,
            detectors: List[Detector],
            coupling_mechanism: Optional[str] = 'mie',
            background_power: Optional[Quantity] = 0 * milliwatt):

        self.scatterer = scatterer
        self.source = source
        self.detectors = detectors
        self.coupling_mechanism = coupling_mechanism
        self.background_power = background_power

        assert len(self.detectors) == 2, 'For now, FlowCytometer can only take two detectors for the analysis.'
        assert self.detectors[0].name != self.detectors[1].name, 'Both detectors cannot have the same name'

    def simulate_pulse(self) -> None:
        """
        Simulates the signal pulses for the FSC and SSC channels by generating Gaussian pulses for
        each particle event and distributing them across the detectors.
        """
        logging.debug("Starting pulse simulation.")

        columns = pd.MultiIndex.from_product(
            [[p.name for p in self.detectors], ['Centers', 'Heights']]
        )

        self.pulse_dataframe = pd.DataFrame(columns=columns)

        self._generate_pulse_parameters()

        _widths = self.scatterer.dataframe['Widths'].values
        _centers = self.scatterer.dataframe['Time'].values

        detection_mechanism = self._get_detection_mechanism()

        # Initialize the detectors
        for detector in self.detectors:
            detector.source = self.source
            detector.init_raw_signal(run_time=self.scatterer.flow_cell.run_time)

        # Fetch the coupling power for each scatterer
        for detector in self.detectors:
            coupling_power = detection_mechanism(
                source=self.source,
                detector=detector,
                scatterer=self.scatterer
            )

            self.scatterer.dataframe['CouplingPower'] = pint_pandas.PintArray(coupling_power, dtype=coupling_power.units)

        for detector in self.detectors:
            # Generate noise components
            detector._add_thermal_noise_to_raw_signal()

            detector._add_dark_current_noise_to_raw_signal()

            # Broadcast the time array to the shape of (number of signals, len(detector.time))
            time_grid = np.expand_dims(detector.dataframe.Time.values.numpy_data, axis=0) * _centers.units

            centers = np.expand_dims(_centers.numpy_data, axis=1) * _centers.units
            widths = np.expand_dims(_widths.numpy_data, axis=1) * _widths.units

            # Compute the Gaussian for each height, center, and width using broadcasting
            power_gaussians = coupling_power[:, np.newaxis] * np.exp(- (time_grid - centers) ** 2 / (2 * widths ** 2))

            total_power = np.sum(power_gaussians, axis=0) + self.background_power

            # Sum all the Gaussians and add them to the detector.raw_signal
            detector._add_optical_power_to_raw_signal(optical_power=total_power)

            detector.capture_signal()

        self._log_statistics()

    def _log_statistics(self) -> SimulationLogger:
        """
        Logs key statistics about the simulated pulse events for each detector using tabulate for better formatting.
        Includes total events, average time between events, gfirst and last event times, and minimum time between events.
        """
        logger = SimulationLogger(cytometer=self)

        logger.log_statistics(include_totals=True, table_format="fancy_grid")

        return logger

    def _get_detection_mechanism(self) -> Callable:
        """
        Generates coupling factors for the scatterer sizes based on the selected coupling mechanism.

        Returns
        -------
        Callable
            The generated coupling factors for the scatterer sizes.
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
        Generates random parameters for a Gaussian pulse, including the center and width.

        Returns
        -------
        center : np.ndarray
            The center of the pulse in time.
        width : np.ndarray
            The width of the pulse (standard deviation of the Gaussian, in seconds).
        """
        self.pulse_dataframe['Centers'] = self.scatterer.dataframe['Time']

        widths = self.source.waist / self.scatterer.flow_cell.flow_speed * np.ones(self.scatterer.n_events)

        self.scatterer.dataframe['Widths'] = pint_pandas.PintArray(widths, dtype=widths.units)

    def plot(self, figure_size: tuple = (10, 6), add_peak_locator: bool = False) -> None:
        """Plots the signals generated for each detector channel."""
        logging.info("Plotting the signal for the different channels.")

        n_detectors = len(self.detectors)

        with plt.style.context(mps):
            _, axes = plt.subplots(ncols=1, nrows=n_detectors + 1, figsize=figure_size, sharex=True, sharey=True, gridspec_kw={'height_ratios': [1, 1, 0.4]})

        time_unit, signal_unit = self.detectors[0].plot(ax=axes[0], show=False, add_peak_locator=add_peak_locator)
        self.detectors[1].plot(ax=axes[1], show=False, time_unit=time_unit, signal_unit=signal_unit, add_peak_locator=add_peak_locator)

        axes[-1].get_yaxis().set_visible(False)
        self.scatterer.add_to_ax(axes[-1])

        # Add legends to each subplot
        for ax in axes:
            ax.legend()

        # Display the plot
        plt.show()

    def add_detector(self, **kwargs) -> Detector:
        detector = Detector(
            **kwargs
        )

        self.detectors.append(detector)

        return detector
