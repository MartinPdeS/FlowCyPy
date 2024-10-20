#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Callable, Optional
from MPSPlots.styles import mps
from dataclasses import dataclass, field
from FlowCyPy.scatterer import Scatterer
from FlowCyPy.detector import Detector
from FlowCyPy.source import Source
from tabulate import tabulate
import pandas as pd
import pint_pandas

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

    Parameters
    ----------
    scatterer : Scatterer
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
    scatterer: Scatterer
    source: Source
    detectors: List[Detector] = field(default_factory=lambda: [])
    coupling_mechanism: Optional[str] = 'mie'

    def simulate_pulse(self) -> None:
        """
        Simulates the signal pulses for the FSC and SSC channels by generating Gaussian pulses for
        each particle event and distributing them across the detectors.
        """
        assert len(self.detectors) == 2, 'For now, FlowCytometer can only take two detectors for the analysis.'
        assert self.detectors[0].name != self.detectors[1].name, 'Both detectors cannot have the same name'

        logging.debug("Starting pulse simulation.")

        columns = pd.MultiIndex.from_product(
            [[p.name for p in self.detectors], ['Centers', 'Widths', 'Heights']]
        )

        self.pulse_dataframe = pd.DataFrame(columns=columns)

        self._generate_pulse_parameters()

        _widths = self.pulse_dataframe['Widths'].values
        _centers = self.pulse_dataframe['Centers'].values

        detection_mechanism = self._get_detection_mechanism()

        for detector in self.detectors:
            detector.source = self.source

            detector.init_raw_signal(run_time=self.scatterer.flow_cell.run_time)

            coupling_power = detection_mechanism(
                source=self.source,
                detector=detector,
                scatterer=self.scatterer
            )

            # Generate noise components
            detector._add_thermal_noise_to_raw_signal()

            detector._add_dark_current_noise_to_raw_signal()

            # Broadcast the time array to the shape of (number of signals, len(detector.time))
            time_grid = np.expand_dims(detector.dataframe.Time.values.numpy_data, axis=0) * _centers.units

            centers = np.expand_dims(_centers.numpy_data, axis=1) * _centers.units
            widths = np.expand_dims(_widths.numpy_data, axis=1) * _widths.units

            # Compute the Gaussian for each height, center, and width using broadcasting
            power_gaussians = coupling_power[:, np.newaxis] * np.exp(- (time_grid - centers) ** 2 / (2 * widths ** 2))

            total_power = np.sum(power_gaussians, axis=0)

            detector._add_photon_shot_noise_to_raw_signal(optical_power=total_power)

            # Sum all the Gaussians and add them to the detector.raw_signal
            signal_volt = total_power * detector.responsitivity * detector.resistance

            detector.dataframe['RawSignal'] += signal_volt

            detector.capture_signal()

        self._log_statistics()

    def _log_statistics(self) -> None:
        """
        Logs key statistics about the simulated pulse events for each detector using tabulate for better formatting.
        Includes total events, average time between events, gfirst and last event times, and minimum time between events.
        """
        total_events = 0
        table_data = []  # List to store table data for each detector

        logging.info("\n=== Simulation Statistics Summary ===")

        # Iterate through each detector to calculate statistics
        for detector in self.detectors:
            centers = self.pulse_dataframe['Centers']
            num_events = len(centers)
            total_events += num_events

            # Calculate average and minimum time between events if more than one event is detected
            if num_events > 1:
                centers_sorted = centers.sort_values()
                time_diffs = centers_sorted.diff().dropna()  # Compute time differences between events
                avg_time_between_events = time_diffs.mean()
                min_time_between_events = time_diffs.min()
            else:
                avg_time_between_events = "N/A"
                min_time_between_events = "N/A"

            # Get first and last event times
            first_event_time = centers.min() if num_events > 0 else "N/A"
            last_event_time = centers.max() if num_events > 0 else "N/A"

            # Append detector statistics to table data
            table_data.append([
                detector.name,                                  # Detector name
                num_events,                                     # Number of events
                f"{first_event_time.to_compact():.4~P}",        # First event time
                f"{last_event_time.to_compact():.4~P}",         # Last event time
                f"{avg_time_between_events.to_compact():.4~P}" if avg_time_between_events != "N/A" else "N/A",  # Average time between events
                f"{min_time_between_events.to_compact():.4~P}" if min_time_between_events != "N/A" else "N/A"   # Minimum time between events
            ])

        # Format the table using tabulate for better readability
        headers = ["Detector", "Number of Events", "First Event Time", "Last Event Time", "Avg Time Between Events", "Min Time Between Events"]
        formatted_table = tabulate(table_data, headers=headers, tablefmt="grid", floatfmt=".3f")

        # Log the formatted table
        logging.info("\n" + formatted_table)

        # Log total events across all detectors
        logging.info(f"\nTotal number of events detected across all detectors: {total_events}")

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

        self.pulse_dataframe['Widths'] = pint_pandas.PintArray(widths, dtype=widths.units)

    def plot(self, figure_size: tuple = (10, 6)) -> None:
        """Plots the signals generated for each detector channel."""
        logging.info("Plotting the signal for the different channels.")

        n_detectors = len(self.detectors)

        with plt.style.context(mps):
            _, axes = plt.subplots(ncols=1, nrows=n_detectors + 1, figsize=figure_size, sharex=True, sharey=True, gridspec_kw={'height_ratios': [1, 1, 0.4]})

        # Plot the main signals for each detector
        for ax, detector in zip(axes, self.detectors):
            detector.plot(ax=ax, show=False)

        axes[-1].get_yaxis().set_visible(False)
        self.scatterer.add_to_ax(axes[-1])

        # Add legends to each subplot
        for ax in axes:
            ax.legend()

        # Display the plot
        plt.show()

    def print_properties(self) -> None:
        """Displays the core properties of the flow cytometer and its detectors using the `tabulate` library."""
        self.scatterer.print_properties()
        print("\nFlowCytometer Properties")

        self.source.print_properties()

        for detector in self.detectors:
            detector.print_properties()

    def add_detector(self, **kwargs) -> Detector:
        detector = Detector(
            **kwargs
        )

        self.detectors.append(detector)

        return detector
