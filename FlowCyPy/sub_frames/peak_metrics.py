from typing import Any, List

import numpy
import pandas as pd
from TypedUnit import Quantity, ureg


class PeakMetricsMixin:
    """Statistical helpers shared by peak result dataframes."""

    def standard_deviation(
        self, detector_name: str, metrics: str | slice = slice(None)
    ):
        """Calculate the standard deviation of selected peak metrics."""
        return self.loc[detector_name, metrics].std()

    def robust_standard_deviation(
        self, detector_name: str, metrics: str | slice = slice(None)
    ):
        """Calculate a normal-equivalent median absolute deviation."""
        sub_frame = self.loc[detector_name, metrics]
        return numpy.abs(sub_frame - sub_frame.median()).median() * 1.4826

    def mean(self, detector_name: str, metrics: str | slice = slice(None)):
        """Calculate the mean of selected peak metrics."""
        return self.loc[detector_name, metrics].mean(axis=0)

    def get_sub_dataframe(
        self, columns: List[str], rows: List[str]
    ) -> tuple[pd.DataFrame, List[Any]]:
        """Extract detector rows and convert columns to compact units."""
        dataframe = self.loc[rows, columns].copy()
        units = []

        for column_name, column_data in dataframe.items():
            if not hasattr(column_data, "pint"):
                dataframe[column_name] = column_data
                units.append("None")
                continue

            unit = column_data.max().to_compact().units
            if unit.dimensionality == ureg.bit_bins.dimensionality:
                unit = ureg.bit_bins
            dataframe[column_name] = column_data.pint.to(unit)
            units.append(unit)

        return dataframe, units
