
from MPSPlots.styles import mps
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import pandas as pd


class TriggeredAcquisition:
    """
    A class for analyzing triggered signal acquisition data.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index DataFrame with detector and segment as levels,
        containing time and signal columns.
    """
    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.dataframe = dataframe

        self.plot = self.PlotInterface(self)


    def get_acquisition(self, detector_name: str, acquisition_id: int) -> pd.DataFrame:
        return self.dataframe.loc[detector_name, acquisition_id]

    def detect_peaks(self) -> pd.DataFrame:
        """
        Detect peaks for all segments of all detectors in a MultiIndex DataFrame using vectorized operations.
        The output is a MultiIndex DataFrame matching the structure of the input.

        Parameters
        ----------
        df : pd.DataFrame
            A MultiIndex DataFrame with levels ['Detector', 'SegmentID'].
        signal_column : str
            The name of the column containing the signal data to analyze.

        Returns
        -------
        pd.DataFrame
            A MultiIndex DataFrame containing peak indices and their corresponding properties
            for each detector and segment.
        """
        df = self.dataframe

        def process_segment(segment):
            signal = segment['Signal'].values
            time = segment['Time'].values
            peak_indices, peak_properties = find_peaks(signal)
            segment_results = pd.DataFrame({
                "PeakIndex": time[peak_indices],
                "PeakHeight": signal[peak_indices],
                **{key: values for key, values in peak_properties.items()}
            })
            return segment_results

        # Apply peak detection to each group (Detector, SegmentID)
        results = df.groupby(level=["Detector", "SegmentID"], group_keys=True).apply(process_segment)

        # Ensure the output has a MultiIndex
        results.index.names = ["Detector", "SegmentID", "Peak"]

        self.peaks_dataframe = results

    class PlotInterface:
        """
        A nested class for handling visualization and plotting.

        Methods
        -------
        signals(figure_size=(10, 6), add_peak_locator=False, show=True)
            Visualizes raw signals for detector channels and scatterer distributions.
        coupling_distribution(log_scale=False, show=True, equal_limits=False, save_path=None)
            Plots the density distribution of optical coupling between two detector channels.
        """

        def __init__(self, experiment: "Experiment"):
            self.experiment = experiment
            self.dataframe = self.experiment.dataframe

        def signals(self, num_segments: int = 5) -> None:
            """
            Plots the first few segments of signal data for each detector using subplots.

            Parameters
            ----------
            num_segments : int, optional
                Number of segments to plot for each detector, by default 5.
            """
            # Get unique detectors
            detectors = self.dataframe.index.get_level_values('Detector').unique()
            num_detectors = len(detectors)

            with plt.style.context(mps):
                # Create subplots
                fig, axes = plt.subplots(
                    num_detectors, 1,
                    figsize=(10, 3 * num_detectors),
                    sharex=True, sharey=True,
                    constrained_layout=True
                )

            # Ensure axes is iterable for single detector case
            if num_detectors == 1:
                axes = [axes]

            # Plot each detector
            for ax, detector_name in zip(axes, detectors):
                detector_data = self.dataframe.loc[detector_name]

                for segment_id, segment_data in detector_data.groupby(level='SegmentID'):
                    if segment_id >= num_segments:
                        break
                    ax.step(segment_data['Time'], segment_data['Signal'], label=f"Segment {segment_id}")

                # Add title and grid
                ax.grid(True)
                ax.legend()

            # Global plot adjustments
            fig.suptitle("Triggered Signal Segments", fontsize=16, y=1.02)
            axes[-1].set_xlabel("Time", fontsize=12)
            for ax in axes:
                ax.set_ylabel(f"Signal {detector_name}", fontsize=12)

            plt.tight_layout()
            plt.show()

        def peaks(self, figsize: tuple = (10, 6)) -> None:
            """
            Plots the signal and highlights the detected peaks for each detector.

            Parameters
            ----------
            figsize : tuple, optional
                The size of the figure for the entire plot. Default is (10, 6).

            Returns
            -------
            None
                Displays the plots for each detector.
            """
            # Get the unique detectors
            detectors = self.dataframe.index.get_level_values("Detector").unique()

            # Create subplots
            fig, axes = plt.subplots(len(detectors), 1, figsize=figsize, sharex=True, constrained_layout=True)

            # Ensure axes is iterable for a single detector case
            axes = axes if len(detectors) > 1 else [axes]

            # Plot each detector's data
            for ax, detector in zip(axes, detectors):
                # Filter data for the current detector
                detector_data = self.dataframe.loc[detector]

                # Plot each segment within the detector
                for segment_id, segment_data in detector_data.groupby(level="SegmentID"):
                    peaks = self.experiment.peaks_dataframe.loc[(detector, segment_id)]

                    # Plot signal
                    ax.step(segment_data["Time"], segment_data["Signal"], color='C0')

                    # Plot peaks
                    if not peaks.empty:
                        ax.scatter(peaks["PeakIndex"], peaks["PeakHeight"], color="red")

                # Customize subplot
                ax.set_title(f"Detector: {detector}")
                ax.set_xlabel("Time")
                ax.set_ylabel("Signal")
                ax.grid(True)

            # Show the plot
            plt.show()

    def compute_statistics(self) -> pd.DataFrame:
        """
        Computes basic statistics (mean, std, min, max) for each segment.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the statistics for each detector and segment.
        """
        stats = self.data.groupby(level=['Detector', 'SegmentID'])['Signal'].agg(['mean', 'std', 'min', 'max'])
        return stats

    def log_summary(self) -> None:
        """
        Prints a summary of the data to the console.

        Prints:
        - Number of detectors.
        - Number of segments.
        - Segment statistics (mean, std, min, max).
        """
        num_detectors = self.data.index.get_level_values('Detector').nunique()
        num_segments = len(self.data.index.get_level_values('SegmentID').unique())

        print("Triggered Acquisition Analysis Summary")
        print("--------------------------------------")
        print(f"Number of Detectors: {num_detectors}")
        print(f"Number of Segments: {num_segments}\n")

        print("Segment Statistics:")
        stats = self.compute_statistics()
        print(stats)

