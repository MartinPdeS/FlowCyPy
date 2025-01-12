from MPSPlots.styles import mps
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from FlowCyPy import units
import pandas as pd
import seaborn as sns


class TriggeredAcquisition:
    """
    A streamlined class for analyzing triggered signal acquisition data.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index DataFrame with levels 'Detector' and 'SegmentID',
        containing time and signal columns.
    """

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.continuous_dataframe = dataframe
        self.plot = self.PlotInterface(self)

    @property
    def n_detectors(self) -> int:
        return len(self.triggered_dataframe.index.get_level_values('Detector').unique())

    def run(self,
            threshold: units.Quantity,
            trigger_detector_name: str = None,
            custom_trigger: np.ndarray = None,
            pre_buffer: int = 64,
            post_buffer: int = 64,
            max_triggers: int = None) -> None:
        """
        Executes the triggered acquisition analysis.

        Parameters
        ----------
        threshold : units.Quantity
            Trigger threshold value.
        trigger_detector_name : str, optional
            Detector used for triggering, by default None.
        custom_trigger : np.ndarray, optional
            Custom trigger array, by default None.
        pre_buffer : int, optional
            Points before trigger, by default 64.
        post_buffer : int, optional
            Points after trigger, by default 64.
        max_triggers : int, optional
            Maximum number of triggers to process, by default None.
        """
        start_indices, end_indices = self._get_trigger_indices(
            threshold, trigger_detector_name, custom_trigger, pre_buffer, post_buffer
        )

        if max_triggers is not None:
            start_indices = start_indices[:max_triggers]
            end_indices = end_indices[:max_triggers]

        segments = []
        for detector_name in self.continuous_dataframe.index.get_level_values('Detector').unique():
            detector_data = self.continuous_dataframe.xs(detector_name)
            time, signal = detector_data['Time'], detector_data['DigitizedSignal']

            for idx, (start, end) in enumerate(zip(start_indices, end_indices)):

                # print(detector_name, idx)
                segment = pd.DataFrame({
                    'Time': time[start:end + 1],
                    'Signal': signal[start:end + 1],
                    'Detector': detector_name,
                    'ID': idx
                })
                segments.append(segment)

        self.triggered_dataframe = pd.concat(segments).set_index(['Detector', 'ID'])

    def get_acquisition(self, detector_name: str, acquisition_id: int) -> pd.DataFrame:
        """Retrieve specific acquisition data."""
        return self.triggered_dataframe.loc[detector_name, acquisition_id]

    def detect_peaks(self) -> None:
        """
        Detects peaks for each segment and stores results in a DataFrame.
        """
        def process_segment(segment):
            signal = segment['Signal'].values
            time = segment['Time'].values
            peaks, properties = find_peaks(signal)

            peaks = [peaks[0]]
            return pd.DataFrame({
                "Time": time[peaks],
                "Height": signal[peaks],
                **{k: v for k, v in properties.items()}
            })

        results = self.triggered_dataframe.groupby(level=['Detector', 'ID']).apply(process_segment)
        results.index.names = ['Detector', 'ID', 'Peak']
        self.peaks_dataframe = results

        print(results)

    def compute_statistics(self) -> pd.DataFrame:
        """Compute statistics for each segment."""
        return self.triggered_dataframe.groupby(level=['Detector'])['Signal'].agg(['mean', 'std', 'min', 'max'])

    def log_summary(self) -> None:
        """Log summary statistics of the acquisition analysis."""
        print("Triggered Acquisition Analysis Summary")
        print("--------------------------------------")
        print(f"Detectors: {self.triggered_dataframe.index.get_level_values('Detector').nunique()}")
        print(f"Segments: {len(self.triggered_dataframe.index.get_level_values('SegmentID').unique())}")
        print(self.compute_statistics())

    def _get_trigger_indices(
            self,
            threshold: units.Quantity,
            trigger_detector_name: str = None,
            custom_trigger: np.ndarray = None, pre_buffer: int = 64,
            post_buffer: int = 64) -> tuple[np.ndarray, np.ndarray]:
        """
        Calculate start and end indices for triggered segments.
        """
        if custom_trigger is not None:
            if len(custom_trigger) != len(self.continuous_dataframe.xs(self.detectors[0].name)['Signal']):
                raise ValueError("Custom trigger length must match signal length.")
            trigger_signal = custom_trigger
        else:
            if trigger_detector_name not in self.continuous_dataframe.index.get_level_values('Detector').unique():
                raise ValueError(f"Detector '{trigger_detector_name}' not found.")
            signal = self.continuous_dataframe.xs(trigger_detector_name)['Signal']
            trigger_signal = signal > threshold.to(signal.pint.units)

        crossings = np.where(np.diff(trigger_signal.astype(int)) == 1)[0]
        start_indices = np.clip(crossings - pre_buffer, 0, len(trigger_signal) - 1)
        end_indices = np.clip(crossings + post_buffer, 0, len(trigger_signal) - 1)

        return start_indices, end_indices

    class PlotInterface:
        """Handles visualization of acquisition data."""

        def __init__(self, acquisition: "TriggeredAcquisition"):
            self.acquisition = acquisition

        def signals(self) -> None:
            """Plot detected peaks on signal segments."""
            with plt.style.context(mps):
                _, axes = plt.subplots(
                    nrows=self.acquisition.n_detectors,
                    ncols=1,
                    figsize=(10, 6),
                    sharex=True,
                    constrained_layout=True
                )

            for ax, (detector_name, group) in zip(axes, self.acquisition.triggered_dataframe.groupby(level=['Detector'])):
                ax.set_ylabel(f"Detector: {detector_name}")

                for _, sub_group in group.groupby(level=['ID']):
                    ax.step(sub_group.Time, sub_group.Signal)

            for ax, (_, group) in zip(axes, self.acquisition.peaks_dataframe.groupby(level=['Detector'])):
                ax.scatter(group['Time'], group['Height'], color='C1')

            plt.show()

        def statistiques(self, x_detector: str, y_detector: str, signal: str = 'Height', bandwidth_adjust: float = 0.8) -> None:
            """
            Plot the joint KDE distribution of the specified signal between two detectors using seaborn,
            optionally overlaying scatter points.

            Parameters
            ----------
            x_detector : str
                Name of the detector to use for the x-axis.
            y_detector : str
                Name of the detector to use for the y-axis.
            signal : str, optional
                The signal column to plot, by default 'Height'.
            bandwidth_adjust : float, optional
                Bandwidth adjustment factor for KDE, by default 0.8.
            """
            _peak_data = self.acquisition.peaks_dataframe[signal].unstack('Detector').droplevel('Peak', axis=0)

            # Filter to only include rows for the specified detectors
            x_data = _peak_data[x_detector]
            y_data = _peak_data[y_detector]


            x_units = x_data.max().to_compact().units
            y_units = y_data.max().to_compact().units

            x_data = x_data.pint.to(x_units)
            y_data = y_data.pint.to(y_units)

            print(x_data)
            print(y_data)

            with plt.style.context(mps):
                # Create joint KDE plot with scatter points overlay
                grid = sns.jointplot(
                    x=x_data,
                    y=y_data,
                    kind='kde',
                    fill=True,
                    cmap="Blues",
                    joint_kws={'bw_adjust': bandwidth_adjust, 'alpha': 0.7}
                )

            grid.ax_joint.scatter(
                x_data,
                y_data,
                color='C1',
                alpha=0.6,
            )

            grid.set_axis_labels(f"{signal} ({x_detector}) [{x_units}]", f"{signal} ({y_detector}) [{y_units}]", fontsize=12)
            plt.tight_layout()
            plt.show()

