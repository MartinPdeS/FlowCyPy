from MPSPlots.styles import mps
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from FlowCyPy import units
import pandas as pd
import seaborn as sns
import warnings


class DataAccessor:
    def __init__(self, outer):
        self._outer = outer

class TriggeredAcquisition:
    """
    A streamlined class for analyzing triggered signal acquisition data.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index DataFrame with levels 'Detector' and 'SegmentID',
        containing time and signal columns.
    """

    def __init__(self, continuous_acquisition: pd.DataFrame, scatterer_dataframe: pd.DataFrame) -> None:
        self.data = DataAccessor(self)
        self.data.continuous = continuous_acquisition
        self.data.scatterer = scatterer_dataframe
        self.plot = self.PlotInterface(self)

    @property
    def n_detectors(self) -> int:
        return len(self.data.triggered.index.get_level_values('Detector').unique())

    def run(self,
            threshold: units.Quantity,
            trigger_detector_name: str,
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
        self.threshold = threshold
        start_indices, end_indices = self._get_trigger_indices(
            threshold, trigger_detector_name, pre_buffer, post_buffer
        )

        if max_triggers is not None:
            start_indices = start_indices[:max_triggers]
            end_indices = end_indices[:max_triggers]

        segments = []
        for detector_name in self.data.continuous.index.get_level_values('Detector').unique():
            detector_data = self.data.continuous.xs(detector_name)
            time, signal = detector_data['Time'], detector_data['DigitizedSignal']


            for idx, (start, end) in enumerate(zip(start_indices, end_indices)):

                segment = pd.DataFrame({
                    'Time': time[start:end + 1],
                    'Signal': signal[start:end + 1],
                    'Detector': detector_name,
                    'SegmentID': idx
                })
                segments.append(segment)

        if len(segments) !=0:
            self.data.triggered = pd.concat(segments).set_index(['Detector', 'SegmentID'])
        else:
            warnings.warn(
                f"No signal were triggered during the run time, try changing the threshold. Signal min-max value is: {self.data.continuous['Signal'].min().to_compact()}, {self.data.continuous['Signal'].max().to_compact()}",
                UserWarning
            )

    def get_acquisition(self, detector_name: str, acquisition_id: int) -> pd.DataFrame:
        """Retrieve specific acquisition data."""
        return self.data.triggered.loc[detector_name, acquisition_id]

    def detect_peaks(self, multi_peak_strategy: str = 'max') -> None:
        """
        Detects peaks for each segment and stores results in a DataFrame.

        Parameters
        ----------
        multi_peak_strategy : str, optional
            Strategy for handling multiple peaks in a segment. Options are:
            - 'mean': Take the average of the peaks in the segment.
            - 'max': Take the maximum peak in the segment.
            - 'sum': Sum all peaks in the segment.
            - 'discard': Remove entries with multiple peaks.
            - 'keep': Keep all peaks without aggregation.
            Default is 'mean'.
        """
        if multi_peak_strategy not in {'mean', 'max', 'sum', 'discard', 'keep'}:
            raise ValueError("Invalid multi_peak_strategy. Choose from 'mean', 'max', 'sum', 'discard', 'keep'.")

        def process_segment(segment):
            signal = segment['Signal'].values
            time = segment['Time'].values
            peaks, properties = find_peaks(signal)

            return pd.DataFrame({
                "SegmentID": segment.name[1],
                "Detector": segment.name[0],
                "Time": time[peaks],
                "Height": signal[peaks],
                **{k: v for k, v in properties.items()}
            })

        # Process peaks for each group
        results = self.data.triggered.groupby(level=['Detector', 'SegmentID']).apply(process_segment)
        results = results.reset_index(drop=True)

        # Check for multiple peaks and issue a warning
        peak_counts = results.groupby(['Detector', 'SegmentID']).size()
        multiple_peak_segments = peak_counts[peak_counts > 1]
        if not multiple_peak_segments.empty:
            warnings.warn(
                f"Multiple peaks detected in the following segments: {multiple_peak_segments.index.tolist()}",
                UserWarning
            )

        # Handle multiple peaks based on the chosen strategy

        print(results)
        dsa
        match multi_peak_strategy:
            case 'sum':
                self.data.peaks = results.groupby(['Detector', 'SegmentID']).sum().unstack('Detector').dropna()
            case 'mean':
                self.data.peaks = results.groupby(['Detector', 'SegmentID']).mean().unstack('Detector').dropna()
            case 'max':
                self.data.peaks = results.groupby(['Detector', 'SegmentID'])['height'].max().unstack('Detector').dropna()
            case 'discard':
                single_peak_segments = peak_counts[peak_counts == 1].index
                self.data.peaks = results.set_index(['Detector', 'SegmentID']).loc[single_peak_segments].unstack('Detector').dropna()
            case 'keep':
                self.data.peaks = results.set_index(['Detector', 'SegmentID']).unstack('Detector').dropna()

    def compute_statistics(self) -> pd.DataFrame:
        """Compute statistics for each segment."""
        return self.data.triggered.groupby(level=['Detector'])['Signal'].agg(['mean', 'std', 'min', 'max'])

    def log_summary(self) -> None:
        """Log summary statistics of the acquisition analysis."""
        print("Triggered Acquisition Analysis Summary")
        print("--------------------------------------")
        print(f"Detectors: {self.data.triggered.index.get_level_values('Detector').nunique()}")
        print(f"Segments: {len(self.data.triggered.index.get_level_values('SegmentID').unique())}")
        print(self.compute_statistics())

    def _get_trigger_indices(
            self,
            threshold: units.Quantity,
            trigger_detector_name: str = None,
            pre_buffer: int = 64,
            post_buffer: int = 64) -> tuple[np.ndarray, np.ndarray]:
        """
        Calculate start and end indices for triggered segments.
        """
        if trigger_detector_name not in self.data.continuous.index.get_level_values('Detector').unique():
            raise ValueError(f"Detector '{trigger_detector_name}' not found.")

        signal = self.data.continuous.xs(trigger_detector_name)['Signal']
        trigger_signal = signal > threshold.to(signal.pint.units)

        crossings = np.where(np.diff(trigger_signal.astype(int)) == 1)[0]
        start_indices = np.clip(crossings - pre_buffer, 0, len(trigger_signal) - 1)
        end_indices = np.clip(crossings + post_buffer, 0, len(trigger_signal) - 1)

        return start_indices, end_indices

    class PlotInterface:
        """Handles visualization of acquisition data."""

        def __init__(self, acquisition: "TriggeredAcquisition"):
            self.acquisition = acquisition

        def signals(self, scatterer_collection = None, palette: str = 'tab10', show: bool = True) -> None:
            """Plot detected peaks on signal segments."""
            n_plots = self.acquisition.n_detectors + 1
            with plt.style.context(mps):
                _, axes = plt.subplots(
                    nrows=n_plots,
                    ncols=1,
                    height_ratios=[1] * (n_plots - 1) + [0.5],
                    figsize=(10, 6),
                    sharex=True,
                    constrained_layout=True
                )

            time_units = self.acquisition.data.triggered['Time'].max().to_compact().units

            for ax, (detector_name, group) in zip(axes, self.acquisition.data.triggered.groupby(level=['Detector'])):
                ax.set_ylabel(f"Detector: {detector_name}")

                for _, sub_group in group.groupby(level=['SegmentID']):
                    x = sub_group['Time'].pint.to(time_units)
                    ax.step(x, sub_group.Signal)

            for ax, (detector_name, group) in zip(axes, self.acquisition.data.peaks.groupby(level=['Detector'], axis=1)):
                x = group[('Time', detector_name)].pint.to(time_units)
                y = group[('Height', detector_name)]
                ax.scatter(x, y, color='C1')


            self._add_digitization_factor_ticks(axes[0], axes[1])

            self._add_event_to_ax(ax=axes[-1], time_units=time_units)

            axes[-1].set_xlabel(f"Time [{time_units}]")

            if show:
                plt.show()

        def _add_event_to_ax(self, ax: plt.Axes, time_units: units.Quantity, palette: str = 'tab10') -> None:
            unique_populations = self.acquisition.data.scatterer.index.get_level_values('Population').unique()
            color_mapping = dict(zip(unique_populations, sns.color_palette(palette, len(unique_populations))))

            for population_name, group in self.acquisition.data.scatterer.groupby('Population'):
                x = group.Time.pint.to(time_units)
                color = color_mapping[population_name]
                ax.vlines(x, ymin=0, ymax=1, transform=ax.get_xaxis_transform(), label=population_name, color=color)

            ax.tick_params(axis='y', left=False, labelleft=False)

            ax.get_yaxis().set_visible(False)
            plt.legend()

        def _add_digitization_factor_ticks(self, *axes: plt.Axes) -> None:
            """
            Add scaled secondary y-axes to the given matplotlib axes, synchronizing the
            secondary axes with the primary axes based on a digitization factor.

            This method creates secondary y-axes for the provided primary axes (`axes`)
            and ensures they remain dynamically synchronized when the primary axes'
            limits change. The secondary axes represent scaled versions of the primary
            axes, using the digitization ratio defined in the `signal_digitizer`.

            Parameters:
            -----------
            axes : plt.Axes
                One or more matplotlib Axes objects for which secondary axes will be added.
                Each primary axis will have a corresponding secondary y-axis.
            """
            for ax in axes:
                # Create a secondary axis
                ax2 = ax.twinx()

                # Define the scaling factor
                scale_factor = self.acquisition.signal_digitizer.digitization_ratio

                # Function to update the secondary axis based on primary axis limits
                def update_secondary_axis(ax1, ax2, scale_factor):
                    """Synchronize ax2 with ax1."""
                    y1_min, y1_max = ax1.get_ylim()  # Get limits from primary axis

                    units = (y1_max * scale_factor).to_compact().units
                    ax2.set_ylim(
                        (y1_min * scale_factor).to(units),
                        (y1_max * scale_factor).to(units)
                    )  # Scale limits
                    ax2.figure.canvas.draw_idle()  # Redraw the figure

                # Attach the update function to the primary axis limits
                ax.callbacks.connect('ylim_changed', lambda ax: update_secondary_axis(ax, ax2, scale_factor))

                # Initial sync of secondary axis
                update_secondary_axis(ax, ax2, scale_factor)

                value = int((self.acquisition.threshold / scale_factor).to('').magnitude)
                ax.axhline(y=value)

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
            # Filter to only include rows for the specified detectors
            x_data = self.acquisition.data.peaks.loc[:, (signal, x_detector)]
            y_data = self.acquisition.data.peaks.loc[:, (signal, y_detector)]

            x_units = x_data.max().to_compact().units
            y_units = y_data.max().to_compact().units

            x_data = x_data.pint.to(x_units)
            y_data = y_data.pint.to(y_units)

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

