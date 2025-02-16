import pandas as pd
from FlowCyPy import units
from scipy.signal import find_peaks
from FlowCyPy.utils import bessel_lowpass_filter, dc_highpass_filter
from FlowCyPy.dataframe_subclass import PeakDataFrame
from FlowCyPy.helper import validate_units
import pint_pandas

class TriggeredAcquisitions:
    """
    A class for handling and processing triggered acquisition data,
    including peak detection and signal filtering.
    """

    def __init__(self, parent, dataframe: pd.DataFrame):
        """
        Initializes the TriggeredAcquisitions instance.

        Parameters
        ----------
        parent : object
            Parent object containing cytometer and detector metadata.
        dataframe : pd.DataFrame
            Dataframe containing the acquired signals.
        """
        self.signal = dataframe
        self.parent = parent

        self.detect_peaks()

    def get_detector(self, name: str):
        """
        Retrieves a detector instance by name.

        Parameters
        ----------
        name : str
            Name of the detector to retrieve.

        Returns
        -------
        object or None
            Detector object if found, otherwise None.
        """
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
            - 'max': Take the maximum peak in the segment.
            - 'mean': Take the average of the peaks in the segment.
            - 'sum': Sum all peaks in the segment.
            - 'discard': Remove entries with multiple peaks.
            - 'keep': Keep all peaks without aggregation.
            Default is 'max'.
        """
        if multi_peak_strategy not in {'max', 'mean', 'sum', 'discard', 'keep'}:
            raise ValueError("Invalid multi_peak_strategy. Choose from 'max', 'mean', 'sum', 'discard', 'keep'.")

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

        # Process multi-peak strategies
        _temp = results.reset_index()[['Detector', 'SegmentID', 'Height']].pint.dequantify().droplevel('unit', axis=1)

        self.peaks = (
            results.reset_index()
            .loc[_temp.groupby(['Detector', 'SegmentID'])['Height'].idxmax()]
            .set_index(['Detector', 'SegmentID'])
        )

        return PeakDataFrame(self.peaks)

    def _apply_lowpass_filter(self, cutoff_freq: units.Quantity, order: int = 4) -> None:
        """
        Applies a Bessel low-pass filter to the signal data in-place.

        Parameters
        ----------
        cutoff_freq : units.Quantity
            The cutoff frequency for the low-pass filter (must have frequency units).
        order : int, optional
            The order of the Bessel filter, default is 4.

        Raises
        ------
        ValueError
            If cutoff frequency is missing or exceeds Nyquist frequency.
        TypeError
            If signal data is not stored as a PintArray.
        """
        if cutoff_freq is None:
            raise ValueError("Cutoff frequency must be specified for low-pass filtering.")

        # Get sampling frequency and ensure it's in Hertz
        fs = self.parent.cytometer.signal_digitizer.sampling_freq.to("hertz")
        nyquist_freq = fs / 2

        # Validate cutoff frequency
        if cutoff_freq.to("hertz") >= nyquist_freq:
            raise ValueError(f"Cutoff frequency ({cutoff_freq}) must be below the Nyquist frequency ({nyquist_freq}).")

        # Ensure the signal column is a PintArray
        if not isinstance(self.signal["DigitizedSignal"].array, pint_pandas.PintArray):
            raise TypeError("Expected 'DigitizedSignal' to be a PintArray, but got a different type.")

        # Iterate through each detector-segment pair and apply filtering
        for (detector, segment_id), segment_data in self.signal.groupby(level=['Detector', 'SegmentID']):
            filtered_values = bessel_lowpass_filter(
                signal=segment_data["DigitizedSignal"].pint.quantity.magnitude,
                cutoff=cutoff_freq,
                sampling_rate=fs,
                order=order
            )

            # Ensure values remain as a PintArray and keep original units
            self.signal.loc[(detector, segment_id), "DigitizedSignal"] = filtered_values.astype(int)

    def _apply_highpass_filter(self, cutoff_freq: units.Quantity, order: int = 4) -> None:
        """
        Applies a DC high-pass filter to the signal data in-place.

        Parameters
        ----------
        cutoff_freq : units.Quantity
            The cutoff frequency for the high-pass filter (must have frequency units).
        order : int, optional
            The order of the high-pass filter, default is 4.

        Raises
        ------
        ValueError
            If cutoff frequency is missing or exceeds Nyquist frequency.
        TypeError
            If signal data is not stored as a PintArray.
        """
        if cutoff_freq is None:
            raise ValueError("Cutoff frequency must be specified for high-pass filtering.")

        # Get sampling frequency and ensure it's in Hertz
        fs = self.parent.cytometer.signal_digitizer.sampling_freq.to("hertz")
        nyquist_freq = fs / 2

        # Validate cutoff frequency
        if cutoff_freq.to("hertz") >= nyquist_freq:
            raise ValueError(f"Cutoff frequency ({cutoff_freq}) must be below the Nyquist frequency ({nyquist_freq}).")

        # Ensure the signal column is a PintArray
        if not isinstance(self.signal["DigitizedSignal"].array, pint_pandas.PintArray):
            raise TypeError("Expected 'DigitizedSignal' to be a PintArray, but got a different type.")

        # Iterate through each detector-segment pair and apply filtering
        for (detector, segment_id), segment_data in self.signal.groupby(level=['Detector', 'SegmentID']):
            filtered_values = dc_highpass_filter(
                signal=segment_data["DigitizedSignal"].pint.quantity.magnitude,
                cutoff=cutoff_freq,
                sampling_rate=fs,
                order=order
            )

            # Ensure values remain as a PintArray and keep original units
            self.signal.loc[(detector, segment_id), "DigitizedSignal"] = filtered_values.astype(int)

    @validate_units(low_cutoff=units.hertz, high_cutoff=units.hertz)
    def apply_filters(self, low_cutoff: units.Quantity = None, high_cutoff: units.Quantity = None) -> None:
        """
        Applies low-pass and/or high-pass filters to the signal data in-place.

        Parameters
        ----------
        low_cutoff : units.Quantity, optional
            The cutoff frequency for the low-pass filter. If None, no low-pass filtering is applied.
        high_cutoff : units.Quantity, optional
            The cutoff frequency for the high-pass filter. If None, no high-pass filtering is applied.
        """
        if low_cutoff is not None:
            self._apply_lowpass_filter(low_cutoff)
        if high_cutoff is not None:
            self._apply_highpass_filter(high_cutoff)
