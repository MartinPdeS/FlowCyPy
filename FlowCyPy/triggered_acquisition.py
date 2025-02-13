import pandas as pd
from FlowCyPy import units
from scipy.signal import find_peaks
from FlowCyPy.utils import bessel_lowpass_filter, dc_highpass_filter
from FlowCyPy.dataframe_subclass import PeakDataFrame

class TriggeredAcquisitions():
    def __init__(self, parent, dataframe: pd.DataFrame):
        self.signal = dataframe
        self.parent = parent

        self.detect_peaks()

    def get_detector(self, name: str):
        for detector in self.parent.cytometer.detectors:
            if detector.name == name:
                return detector

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
        if multi_peak_strategy not in {'max', }:
            raise ValueError("Invalid multi_peak_strategy. Choose from 'max'.")

        def process_segment(segment):
            signal = segment['DigitizedSignal'].values
            time = segment['Time'].values
            peaks, properties = find_peaks(signal, width=1)

            return pd.DataFrame({
                "SegmentID": segment.name[1],
                "Detector": segment.name[0],
                "Height": signal[peaks],
                "Time": time[peaks],
                **{k: v for k, v in properties.items()}
            })

        # Process peaks for each group
        results = self.signal.groupby(level=['Detector', 'SegmentID']).apply(process_segment)
        results = results.reset_index(drop=True)

        # Check for multiple peaks and issue a warning
        # peak_counts = results.groupby(['Detector', 'SegmentID']).size()
        # multiple_peak_segments = peak_counts[peak_counts > 1]
        # if not multiple_peak_segments.empty:
        #     warnings.warn(
        #         f"Multiple peaks detected in the following segments: {multiple_peak_segments.index.tolist()}",
        #         UserWarning
        #     )

        _temp = results.reset_index()[['Detector', 'SegmentID', 'Height']].pint.dequantify().droplevel('unit', axis=1)

        self.peaks = (
            results.reset_index()
            .loc[_temp.groupby(['Detector', 'SegmentID'])['Height'].idxmax()]
            .set_index(['Detector', 'SegmentID'])
        )

        return PeakDataFrame(self.peaks)

    def process_data(self, cutoff_low: units.Quantity = None, cutoff_high: units.Quantity = None):
        """Applies the Bessel low-pass and DC high-pass filters to each SegmentID separately."""
        filtered_df = self.data.triggered.copy()  # Copy to avoid modifying the original
        segment_ids = self.data.triggered.index.levels[1]  # Extract unique SegmentID values
        fs = self.cytometer.signal_digitizer.sampling_freq

        for segment_id in segment_ids:
            for detector in self.data.triggered.index.levels[0]:  # Iterate through Detectors
                col = (detector, segment_id)  # MultiIndex column tuple
                if col in self.data.triggered:
                    data = self.data.triggered[col].values
                    if cutoff_low is not None:
                        data = bessel_lowpass_filter(data, cutoff_low, fs)
                    if cutoff_high is not None:
                        data = dc_highpass_filter(data, cutoff_high, fs)
                    filtered_df[col] = data  # Store filtered data

        return filtered_df
