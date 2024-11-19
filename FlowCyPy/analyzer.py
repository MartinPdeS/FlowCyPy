import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from FlowCyPy.units import second
import warnings
from FlowCyPy.detector import Detector
from FlowCyPy import peak_finder
from FlowCyPy.cytometer import FlowCytometer

import logging
from tabulate import tabulate
from FlowCyPy.report import Report


class Analyzer:
    """
    A class for analyzing pulse signals generated by a flow cytometer. It processes signals
    from multiple detectors to extract key features such as peak height, width, area,
    and time of occurrence, while providing tools to detect coincident events between detectors.

    Parameters
    ----------
    cytometer : FlowCytometer
        An instance of FlowCytometer that contains detectors and their associated signals.
    algorithm : peak_finder.BaseClass
        The peak-finding algorithm used to detect peaks in the signals.

    Methods
    -------
    run_analysis(compute_peak_area=False):
        Performs peak analysis on all detectors, extracting features such as height, width,
        and area, and stores the results in a DataFrame.
    get_coincidence(margin):
        Identifies and returns events where peak times from different detectors coincide
        within a given time margin.
    display_features():
        Displays the extracted features from the analysis in a tabular format.
    plot_peak(show=True, figure_size=(7, 6)):
        Plots the signals and highlights the detected peaks and their properties (e.g., width).
    plot(show=True, log_plot=True):
        Generates a 2D density plot of the scattering intensities from the detectors.
    generate_report(filename):
        Generates a report summarizing the results of the analysis.
    """

    def __init__(self, cytometer: FlowCytometer, algorithm: peak_finder.BaseClass) -> None:
        """
        Initializes the Analyzer class with the cytometer object and the peak-finding algorithm.

        Parameters
        ----------
        cytometer : FlowCytometer
            An instance of FlowCytometer that contains detectors and their signals.
        algorithm : peak_finder.BaseClass
            The peak-finding algorithm used to detect peaks in the signals.
        """
        self.algorithm = algorithm
        self.cytometer = cytometer
        self.datasets = []

    def run_analysis(self, compute_peak_area: bool = False) -> None:
        """
        Runs the peak detection analysis on all detectors within the flow cytometer.
        Extracts key features such as peak height, width, area, and stores the results
        in a pandas DataFrame for further analysis.

        Parameters
        ----------
        compute_peak_area : bool, optional
            Whether to compute the area under the peaks, by default False.

        Returns
        -------
        pd.DataFrame
            A DataFrame with the detected peak properties, organized by detector.
        """
        logging.info("Starting peak analysis for all detectors.")

        # Run peak detection on each detector
        self._analyze_all_detectors(compute_peak_area)

        # Calculate and log additional statistics
        self._log_statistics()

    def _analyze_detector(self, detector: Detector, compute_peak_area: bool) -> None:
        """
        Analyzes the signal from a single detector, detecting peaks and extracting
        features such as height, width, and area.

        Parameters
        ----------
        detector : Detector
            The detector object that contains signal data.
        compute_peak_area : bool
            Whether to compute the area under the peaks.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the peak properties (e.g., height, width, area)
            for the analyzed detector.
        """
        logging.info(f"Analyzing Detector {detector.name}.")

        # Run the peak detection algorithm
        self.algorithm.detect_peaks(detector=detector, compute_area=compute_peak_area)

        logging.info(f"Detector {detector.name}: Detected {len(detector.peak_properties)} peaks.")

    def _analyze_all_detectors(self, compute_peak_area: bool) -> None:
        """
        Runs the peak detection analysis on all detectors, concatenating the results
        into a combined DataFrame.

        Parameters
        ----------
        compute_peak_area : bool
            Whether to compute the area under the peaks for all detectors.
        """
        for detector in self.cytometer.detectors:
            # Analyze each detector and append the results
            self._analyze_detector(detector, compute_peak_area)

        self.dataframe = pd.concat(
            [d.peak_properties for d in self.cytometer.detectors],
            keys=[f'{d.name}' for d in self.cytometer.detectors]
        )

        self.dataframe.index.names = ['Detector', 'Event']

    def _log_statistics(self) -> None:
        """
        Logs statistical information about the detected peaks for each detector,
        including the number of events, the first and last peak times, the average
        time between peaks, and the minimum time between peaks.

        The results are displayed in a formatted table using `tabulate` for clarity.
        """
        total_peaks = 0
        table_data = []  # List to store table data for each detector

        logging.info("\n=== Analysis Summary ===")

        # Group by the 'Detector' column to calculate stats for each detector
        for detector, (_, group) in zip(self.cytometer.detectors, self.dataframe.groupby('Detector')):
            num_events = len(group)
            total_peaks += num_events
            # Calculate average and minimum time between peaks if more than one event is detected
            if num_events > 1:
                times = group['PeakTimes'].sort_values()
                time_diffs = times.diff().dropna()  # Compute time differences between peaks
                avg_time_between_peaks = time_diffs.mean()
                min_time_between_peaks = time_diffs.min()  # Calculate minimum time difference between peaks
            else:
                avg_time_between_peaks = "N/A"
                min_time_between_peaks = "N/A"

            # Get first and last peak times
            first_peak_time = group['PeakTimes'].min() if num_events > 0 else "N/A"
            last_peak_time = group['PeakTimes'].max() if num_events > 0 else "N/A"

            # Append detector statistics to table data
            table_data.append([
                detector.name,                                  # Detector name
                num_events,                                     # Number of events
                f"{first_peak_time.to_compact():.4~P}",         # First peak time
                f"{last_peak_time.to_compact():.4~P}",          # Last peak time
                f"{avg_time_between_peaks.to_compact():.4~P}" if avg_time_between_peaks != "N/A" else "N/A",  # Average time between peaks
                f"{min_time_between_peaks.to_compact():.4~P}" if min_time_between_peaks != "N/A" else "N/A"  # Minimum time between peaks
            ])

        # Format the table using tabulate
        headers = ["Detector", "Number of Events", "First Peak Time", "Last Peak Time", "Avg Time Between Peaks", "Min Time Between Peaks"]
        formatted_table = tabulate(table_data, headers=headers, tablefmt="grid", floatfmt=".3f")

        # Log the formatted table
        logging.info("\n" + formatted_table)

        # Log total peaks across all detectors
        logging.info(f"\nTotal number of peaks detected across all detectors: {total_peaks}")

    def get_coincidence(self, margin: second.dimensionality) -> None:
        """
        Identifies coincident events between two detectors within a specified time margin.

        Parameters
        ----------
        margin : pint.Quantity
            The time margin within which peaks are considered coincident, in compatible time units.
        """
        # Ensure margin has correct dimensionality (time)
        assert margin.dimensionality == second.dimensionality, "Margin must have time dimensionality."

        self.dataframe['PeakTimes'] = self.dataframe['PeakTimes'].pint.to(margin.units)

        # Split the data for Detector_1 and Detector_2
        d0 = self.dataframe.xs(self.cytometer.detectors[0].name, level='Detector')
        d1 = self.dataframe.xs(self.cytometer.detectors[1].name, level='Detector')

        # Repeat and tile PeakTimes for comparison (keeping your protocol)
        d0_repeated = np.repeat(d0['PeakTimes'].values.numpy_data, len(d1)) * margin.units
        d1_tiled = np.tile(d1['PeakTimes'].values.numpy_data, len(d0)) * margin.units

        # Compute time differences and reshape the mask
        time_diffs = np.abs(d0_repeated - d1_tiled)
        mask = time_diffs <= margin
        mask = mask.reshape(len(d0), len(d1))

        # Find indices where coincidences occur
        indices = np.where(mask)

        # Count coincidences per column (for each event in Detector_1)
        true_count_per_column = np.sum(mask.astype(int), axis=0)

        # Warnings and assertions
        if np.all(true_count_per_column == 0):
            warnings.warn("No coincidence events found, the margin might be too low.")

        assert np.all(true_count_per_column <= 1), \
            "Coincidence events are ambiguously defined, the margin might be too high."

        # Extract coincident events from both detectors
        coincident_detector_0 = d0.iloc[indices[0]].reset_index(drop=True)
        coincident_detector_1 = d1.iloc[indices[1]].reset_index(drop=True)

        # Combine the coincident events into a single DataFrame
        combined_coincidences = pd.concat([coincident_detector_0, coincident_detector_1], axis=1)

        # Assign proper MultiIndex column names
        combined_coincidences.columns = pd.MultiIndex.from_product([[d.name for d in self.cytometer.detectors], d0.columns])

        self.coincidence = combined_coincidences

    def display_features(self) -> None:
        """
        Displays extracted peak features for all datasets in a tabular format.
        """
        for i, dataset in enumerate(self.datasets):
            print(f"\nFeatures for Dataset {i + 1}:")
            dataset.print_properties()  # Reuse the print_properties method from DataSet

    def plot_peak(self, show: bool = True, figure_size: tuple = (10, 6)) -> None:
        """
        Plots the detected peaks on the signal for each detector, including peak widths at half-maximum.

        Parameters
        ----------
        show : bool, optional
            Whether to display the plot immediately, by default True.
        figure_size : tuple, optional
            The size of the figure, by default (7, 6).
        """
        n_detectors = len(self.cytometer.detectors)

        with plt.style.context(mps):
            _, axes = plt.subplots(ncols=1, nrows=n_detectors + 1, figsize=figure_size, sharex=True, sharey=True, gridspec_kw={'height_ratios': [1, 1, 0.3]})

        for ax, detector in zip(axes, self.cytometer.detectors):
            self.algorithm.plot(detector, ax=ax, show=False)

        axes[-1].get_yaxis().set_visible(False)
        self.cytometer.scatterer.add_to_ax(axes[-1])

        plt.tight_layout()

        for ax in axes:
            ax.legend()

        if show:
            plt.show()

    # Function to map scatterers to time points
    def map_scatterers_to_time(time_points, scatterers, margin):
        results = []  # List to hold the results for each time point

        for t in time_points:
            scatterer_names = []  # To store scatterer names that match
            for i, scatterer_times in enumerate(scatterers):
                # Check if any scatterer time is within the margin
                if np.any(np.abs(scatterer_times - t) <= margin):
                    scatterer_names.append(f"Scatterer_{i+1}")

            # Concatenate scatterer names with a dash
            scatterers_str = "-".join(scatterer_names)

            # Add results for this time point
            results.append({
                "Time Point": t,
                "Scatterers": scatterers_str
            })

        return pd.DataFrame(results)

    def plot(self, show: bool = True, log_plot: bool = True, x_limits: tuple = None, y_limits: tuple = None, bandwidth_adjust: float = 1) -> None:
        """
        Plots a 2D density plot of the scattering intensities from the two detectors,
        along with individual peak heights.

        Parameters
        ----------
        show : bool, optional
            Whether to display the plot immediately, by default True.
        log_plot : bool, optional
            Whether to use logarithmic scaling for the plot axes, by default True.
        bandwidth_adjust : float, optional
            Bandwidth adjustment factor for the kernel density estimate of the marginal distributions. Higher values produce smoother density estimates. Default is 1.
        """
        # Reset the index if necessary (to handle MultiIndex)
        df_reset = self.coincidence.reset_index()
        # df_reset.loc[:10, 'scatterer'] = 1
        # df_reset.loc[10:, 'scatterer'] = 2

        x_data = df_reset[(self.cytometer.detectors[0].name, 'Heights')]
        y_data = df_reset[(self.cytometer.detectors[1].name, 'Heights')]

        # Extract the units from the pint-pandas columns
        x_units = x_data.max().to_compact().units
        y_units = y_data.max().to_compact().units

        x_data = x_data.pint.to(x_units)
        y_data = y_data.pint.to(y_units)

        bandwidth_adjust = 1
        import seaborn as sns
        with plt.style.context(mps):

            g = sns.jointplot(
                data=df_reset,
                x=x_data,
                y=y_data,
                kind='kde',
                alpha=0.8,
                fill=True,
                joint_kws={'alpha': 0.7, 'bw_adjust': bandwidth_adjust}
            )
            sns.scatterplot(
                data=df_reset,
                x=x_data,
                y=y_data,
                # hue='scatterer',
                ax=g.ax_joint,
                alpha=0.6,
                zorder=1
            )

            # Set the x and y labels with units
            g.ax_joint.set_xlabel(f"Heights : {self.cytometer.detectors[0].name} [{x_units:P}]")
            g.ax_joint.set_ylabel(f"Heights: {self.cytometer.detectors[1].name} [{y_units:P}]")

            if log_plot:
                g.ax_marg_x.set_xscale('log')
                g.ax_marg_y.set_yscale('log')

            if x_limits is not None:
                x0, x1 = x_limits
                x0 = x0.to(x_units).magnitude
                x1 = x1.to(x_units).magnitude
                g.ax_joint.set_xlim(x0, x1)

            if y_limits is not None:
                y0, y1 = y_limits
                y0 = y0.to(y_units).magnitude
                y1 = y1.to(y_units).magnitude
                g.ax_joint.set_ylim(y0, y1)

            plt.tight_layout()

            if show:
                plt.show()

    def generate_report(self, filename: str) -> None:
        """
        Generates a detailed report summarizing the analysis, including peak features
        and detected events.

        Parameters
        ----------
        filename : str
            The filename where the report will be saved.
        """
        report = Report(
            flow_cell=self.cytometer.scatterer.flow_cell,
            scatterer=self.cytometer.scatterer,
            analyzer=self
        )

        report.generate_report()