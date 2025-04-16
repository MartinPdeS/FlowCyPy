import numpy as np
import pandas as pd
from FlowCyPy import units
from FlowCyPy.dataframe_subclass import TriggerDataFrame
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
        self.analog = dataframe.sort_index()
        self.parent = parent

    @property
    def signal_digitizer(self) -> object:
        return self.parent.signal_digitizer

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

    def get_digital_signal(self) -> TriggerDataFrame:

        digitizer = self.signal_digitizer

        digital_df = pd.DataFrame(
            index=self.analog.index,
            columns=self.analog.columns,
            data=dict(Time=self.analog.Time)
        )

        for detector_name in self.analog.detector_names:
            analog_signal = self.analog[detector_name]
            digitized_signal, _ = digitizer.capture_signal(signal=analog_signal)

            digital_df[detector_name] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return TriggerDataFrame(
            dataframe=digital_df,
            plot_type='digital',
            scatterer_dataframe=self.analog.attrs['scatterer_dataframe']
        )
