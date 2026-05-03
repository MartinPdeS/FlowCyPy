# -*- coding: utf-8 -*-
from typing import List, Mapping

import pandas as pd
from TypedUnit import Time, Voltage, ureg


class AcquisitionDataFrame(pd.DataFrame):
    """
    DataFrame subclass for continuous analog acquisition data.

    Notes
    -----
    This class does not use pint-pandas.
    All columns store plain numeric magnitudes.
    Units are stored in:

        self.attrs["units"][column_name]

    The input dictionary is expected to contain:
        - "Time": a quantity-like object with `.magnitude` and `.units`
        - detector channels: quantity-like objects with `.magnitude` and `.units`

    The ``__getitem__`` operator is overloaded so that:

        self["Time"]
        self["DetectorA"]

    return quantity arrays with units attached.

    Internally, whenever raw pandas Series are required, this class uses:

        super().__getitem__(column_name)
    """

    @property
    def _constructor(self) -> type:
        """
        Ensure operations return instances of AcquisitionDataFrame.
        """
        return self.__class__

    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the AcquisitionDataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Input dataframe containing plain numeric magnitudes.
        """
        super().__init__(dataframe)

        if "units" not in self.attrs:
            self.attrs["units"] = {}

    def __getitem__(self, key):
        """
        Return dataframe content.

        Behavior
        --------
        - If ``key`` is a single column name with registered units, return the
          corresponding numeric values as a quantity array.
        - Otherwise, fall back to the default pandas behavior.

        Parameters
        ----------
        key : object
            Standard pandas dataframe key.

        Returns
        -------
        object
            Quantity array for unit-aware single-column access, otherwise the
            default pandas return type.
        """
        output = super().__getitem__(key)

        if isinstance(key, str) and key in self.columns:
            if "units" in self.attrs and key in self.attrs["units"]:
                return output.to_numpy() * self.attrs["units"][key]

        return output

    def __finalize__(self, other, method=None, **kwargs):
        """
        Finalize the DataFrame after operations while preserving unit metadata.

        Parameters
        ----------
        other : object
            Source object used by pandas during propagation.
        method : str, optional
            Finalization method name.
        **kwargs
            Additional keyword arguments forwarded by pandas.

        Returns
        -------
        AcquisitionDataFrame
            Finalized dataframe with copied unit metadata.
        """
        output = super().__finalize__(other, method=method, **kwargs)

        if hasattr(other, "attrs"):
            output.attrs["units"] = dict(other.attrs.get("units", {}))

        return output

    @classmethod
    def _construct_from_signal_dict(
        cls,
        signal_dict: Mapping[str, object],
    ) -> "AcquisitionDataFrame":
        """
        Convert a dictionary of time and detector signals into an AcquisitionDataFrame.

        The input dictionary must contain a ``"Time"`` entry and one or more detector
        entries. Each value is expected to be a quantity-like object exposing
        ``.magnitude`` and ``.units``.

        Parameters
        ----------
        signal_dict : Mapping[str, object]
            Dictionary containing the acquisition data. It must contain the key
            ``"Time"`` and all arrays must have the same length.

        Returns
        -------
        AcquisitionDataFrame
            A dataframe containing the time axis and detector signals.
        """
        cls.raw_data = signal_dict

        if "Time" not in signal_dict:
            raise ValueError("signal_dict must contain a 'Time' entry.")

        if len(signal_dict) < 2:
            raise ValueError(
                "signal_dict must contain at least 'Time' and one detector signal."
            )

        time_values = signal_dict["Time"]

        if not hasattr(time_values, "magnitude"):
            raise ValueError("signal_dict['Time'] must have a 'magnitude' attribute.")

        if not hasattr(time_values, "units"):
            raise ValueError("signal_dict['Time'] must have a 'units' attribute.")

        expected_length = len(time_values)
        signal_dataframe = pd.DataFrame()
        signal_dataframe["Time"] = pd.Series(time_values.magnitude)

        for detector_name, detector_signal in signal_dict.items():
            if detector_name == "Time":
                continue

            if len(detector_signal) != expected_length:
                raise ValueError(
                    f"Signal '{detector_name}' has length {len(detector_signal)} but "
                    f"'Time' has length {expected_length}."
                )

            if not hasattr(detector_signal, "magnitude"):
                raise ValueError(
                    f"Signal '{detector_name}' must have a 'magnitude' attribute."
                )

            if not hasattr(detector_signal, "units"):
                raise ValueError(
                    f"Signal '{detector_name}' must have a 'units' attribute."
                )

            signal_dataframe[detector_name] = pd.Series(detector_signal.magnitude)

        signal_dataframe = cls(signal_dataframe)
        signal_dataframe.attrs["units"]["Time"] = time_values.units

        for detector_name, detector_signal in signal_dict.items():
            if detector_name == "Time":
                continue

            signal_dataframe.attrs["units"][detector_name] = detector_signal.units

        signal_dataframe.normalize_units(signal_units="SI", time_units="SI")

        return signal_dataframe

    def get_units(self, column: str):
        """
        Return the stored unit associated with a column.

        Parameters
        ----------
        column : str
            Column name for which unit metadata should be retrieved.

        Returns
        -------
        object
            Stored unit object.

        Raises
        ------
        KeyError
            If no unit metadata exists for the requested column.
        """
        if "units" not in self.attrs:
            raise KeyError("No unit metadata is stored in this AcquisitionDataFrame.")

        if column not in self.attrs["units"]:
            raise KeyError(f"No unit metadata is stored for column '{column}'.")

        return self.attrs["units"][column]

    @property
    def detector_names(self) -> List[str]:
        """
        Return detector column names.
        """
        return [col for col in self.columns if col != "Time"]

    @property
    def time_units(self):
        """
        Return the stored units associated with the time axis.
        """
        return self.get_units("Time")

    @time_units.setter
    def time_units(self, value) -> None:
        """
        Set the stored unit associated with the time axis.

        Parameters
        ----------
        value : object
            Unit object to associate with the ``Time`` column.
        """
        self.attrs["units"]["Time"] = value

    @property
    def signal_units(self):
        """
        Return the stored units associated with the detector channels.

        This assumes all detector channels share the same units.
        """
        if len(self.detector_names) == 0:
            raise ValueError("No detector channels are present in the dataframe.")

        return self.get_units(self.detector_names[0])

    @signal_units.setter
    def signal_units(self, value) -> None:
        """
        Set the stored units associated with all detector channels.

        Parameters
        ----------
        value : object
            Unit object to assign to every detector column.
        """
        for detector_name in self.detector_names:
            self.attrs["units"][detector_name] = value

    def _convert_column_to_units(self, column: str, target_units) -> None:
        """Convert one stored magnitude column to target units in place.

        Parameters
        ----------
        column : str
            Column to convert.
        target_units : object
            Target unit.

        Notes
        -----
        The dataframe stores raw magnitudes, so this method converts values and
        updates the corresponding unit metadata together.
        """
        source_units = self.get_units(column)
        raw_series = super().__getitem__(column)
        converted_quantity = (raw_series.to_numpy() * source_units).to(target_units)

        super().__setitem__(column, converted_quantity.magnitude)
        self.attrs["units"][column] = target_units

    def normalize_units(
        self,
        signal_units: Voltage | str = None,
        time_units: Time | str = None,
    ) -> "AcquisitionDataFrame":
        """
        Convert the stored time and detector columns to consistent units.

        Parameters
        ----------
        signal_units : Voltage | str, optional
            The units to which the signal columns should be normalized.
            Supported string values are ``"max"`` and ``"SI"``.
        time_units : Time | str, optional
            The units to which the time column should be normalized.
            Supported string values are ``"max"`` and ``"SI"``.

        Returns
        -------
        AcquisitionDataFrame
            The same dataframe instance, modified in place.

        Notes
        -----
        Passing ``"max"`` selects a compact unit based on the maximum observed
        magnitude. Passing ``"SI"`` selects base SI-style units used by the
        acquisition code.
        """
        if len(self.detector_names) == 0:
            raise ValueError("At least one detector channel is required.")

        reference_detector_name = self.detector_names[0]

        if signal_units == "max":
            raw_signal = super().__getitem__(reference_detector_name)

            if raw_signal.size == 0:
                signal_units = self.get_units(reference_detector_name)
            else:
                maximum_signal_quantity = raw_signal.max() * self.get_units(
                    reference_detector_name
                )
                signal_units = maximum_signal_quantity.to_compact().units

        if signal_units == "SI":
            reference_units = self.get_units(reference_detector_name)

            if reference_units.dimensionality == ureg.bit_bins.dimensionality:
                signal_units = ureg.bit_bins
            else:
                signal_units = ureg.volt

        if time_units == "max":
            raw_time = super().__getitem__("Time")

            if raw_time.size == 0:
                time_units = self.get_units("Time")
            else:
                maximum_time_quantity = raw_time.max() * self.get_units("Time")
                time_units = maximum_time_quantity.to_compact().units

        if time_units == "SI":
            time_units = ureg.second

        if time_units is not None:
            self._convert_column_to_units("Time", time_units)

        if signal_units is not None:
            for detector_name in self.detector_names:
                self._convert_column_to_units(detector_name, signal_units)

        return self

