#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Callable
from MPSPlots.styles import mps
from dataclasses import dataclass
from FlowCyPy.scatterer_distribution import ScattererDistribution
from FlowCyPy.detector import Detector
from FlowCyPy.source import Source


# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

@dataclass
class FlowCytometer:
    """
    A class to simulate flow cytometer signals for Forward Scatter (FSC) and Side Scatter (SSC) channels.

    This class models the particle distribution, flow characteristics, and detector configurations to
    simulate the signal generated as particles pass through the flow cytometer's laser.

    Attributes
    ----------
    scatterer_distribution : ScattererDistribution
        The distribution of particle sizes which affects scattering signals.
    source : Source
        The laser source object representing the illumination scheme.
    detectors : List[Detector]
        List of `Detector` objects representing the detectors in the system.

    Methods
    -------
    simulate_pulse()
        Simulates the signal pulses for FSC and SSC channels based on particle distribution and flow.
    plot()
        Plots the simulated signals for each detector channel.
    print_properties()
        Displays the key properties of the flow cytometer and its detectors.
    """
    scatterer_distribution: ScattererDistribution
    coupling_mechanism: str
    source: Source
    detectors: List[Detector]

    def print_properties(self) -> None:
        """Displays the core properties of the flow cytometer and its detectors using the `tabulate` library."""
        self.scatterer_distribution.print_properties()
        print("\nFlowCytometer Properties")

        self.source.print_properties()

        for detector in self.detectors:
            detector.print_properties()

    def simulate_pulse(self) -> None:
        """
        Simulates the signal pulses for the FSC and SSC channels by generating Gaussian pulses for
        each particle event and distributing them across the detectors.
        """
        logging.debug("Starting pulse simulation.")

        centers, widths = self._generate_pulse_parameters()

        centers = centers[:, np.newaxis]
        widths = widths[:, np.newaxis]
        detection_mechanism = self._get_detection_mechanism()

        for detector in self.detectors:
            detector.init_raw_signal(total_time=self.scatterer_distribution.flow.total_time)

            heights = detection_mechanism(
                source=self.source,
                detector=detector,
                scatterer_distribution=self.scatterer_distribution
            )

            # Broadcast the time array to the shape of (number of signals, len(detector.time))
            time_grid = np.expand_dims(detector.time, axis=0)

            # Compute the Gaussian for each height, center, and width using broadcasting
            gaussians = heights[:, np.newaxis] * np.exp( - (time_grid - centers) ** 2 / (2 * widths ** 2))

            # Sum all the Gaussians and add them to the detector.raw_signal
            detector.raw_signal = np.sum(gaussians, axis=0)

        for detector in self.detectors:
            detector.capture_signal()

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

    def _generate_pulse_parameters(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates random parameters for a Gaussian pulse, including the center and width.

        Returns
        -------
        center : np.ndarray
            The center of the pulse in time.
        width : np.ndarray
            The width of the pulse (standard deviation of the Gaussian, in seconds).
        """
        centers = self.scatterer_distribution.flow.time_positions

        widths = self.source.waist / self.scatterer_distribution.flow.flow_speed * np.ones(centers.size)
        return centers, widths

    def _add_to_ax(self, ax: plt.Axes) -> None:
        """
        Plots the signal for each detector channel on the given axis.

        Parameters
        ----------
        ax : plt.Axes
            The Matplotlib axis where the signal will be plotted.
        """
        ax.set(
            title='Simulated raw flow-cytometry signal',
            xlabel='Time [seconds]',
            ylabel='Signal Intensity [V]'
        )

        for c, detector in enumerate(self.detectors):
            detector._add_to_ax(ax=ax, color=f'C{c}')

        ax.legend()

    def plot(self) -> None:
        """Plots the signals generated for each detector channel."""
        logging.info(f"Plotting the signal for the different channels.")

        with plt.style.context(mps):
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))

            self._add_to_ax(ax=ax)

            plt.show()
