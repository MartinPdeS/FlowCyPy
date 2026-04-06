from typing import Any

import numpy as np
import pandas as pd


class EventDataFrame(pd.DataFrame):
    """
    DataFrame that stores column units in ``attrs["units"]``.

    Raw numerical magnitudes are stored in the dataframe itself.
    When a column is accessed with ``__getitem__``, a quantity is returned
    if that column has a registered unit.
    """

    _metadata = ["scatterer_type"]

    @property
    def _constructor(self):
        return EventDataFrame

    def __init__(self, *args, scatterer_type: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        if "units" not in self.attrs:
            self.attrs["units"] = {}

        self.scatterer_type = scatterer_type

    @property
    def units(self) -> dict[str, Any]:
        if "units" not in self.attrs:
            self.attrs["units"] = {}
        return self.attrs["units"]

    def set_column(
        self,
        column_name: str,
        values: Any,
        unit: Any | None = None,
    ) -> None:
        """
        Store a column in magnitude form and register its unit.

        Parameters
        ----------
        column_name : str
            Name of the column.
        values : Any
            Either a plain array-like object or a Pint quantity.
        unit : optional
            Unit to associate with the column. If omitted and ``values`` is a
            quantity, the unit is inferred from ``values``.
        """
        if hasattr(values, "magnitude") and hasattr(values, "units"):
            quantity_values = values if unit is None else values.to(unit)
            self.loc[:, column_name] = np.asarray(quantity_values.magnitude)
            self.units[column_name] = quantity_values.units
            return

        self.loc[:, column_name] = np.asarray(values)

        if unit is None:
            self.units.pop(column_name, None)
        else:
            self.units[column_name] = unit

    def set_unit(
        self,
        column_name: str,
        unit: Any,
    ) -> None:
        """
        Register or update the unit of an existing column.
        """
        self.units[column_name] = unit

    def get_unit(
        self,
        column_name: str,
    ) -> Any | None:
        """
        Return the registered unit of a column, or None.
        """
        return self.units.get(column_name)

    def get_magnitude(
        self,
        column_name: str,
    ) -> np.ndarray:
        """
        Return the raw stored magnitude values of a column.
        """
        return super().__getitem__(column_name).to_numpy()

    def get_quantity(
        self,
        column_name: str,
    ) -> Any:
        """
        Return the column as a quantity if it has a registered unit.
        Otherwise return the raw NumPy array.
        """
        raw_values = super().__getitem__(column_name).to_numpy()
        unit = self.get_unit(column_name)

        if unit is None:
            return raw_values

        return raw_values * unit

    def __getitem__(self, key):
        """
        Return a quantity for unit-aware single-column access.

        Single-column access:
            event_dataframe["x"] -> quantity or Series-like raw values

        Multi-column access:
            event_dataframe[["x", "y"]] -> EventDataFrame
        """
        output = super().__getitem__(key)

        if isinstance(key, str):
            unit = self.get_unit(key)

            if unit is None:
                return output

            return output.to_numpy() * unit

        if isinstance(output, pd.DataFrame):
            output = self._constructor(output)
            output.attrs = {**self.attrs}
            output.scatterer_type = getattr(self, "scatterer_type", None)

            if "units" not in output.attrs:
                output.attrs["units"] = {}

            output.attrs["units"] = {
                column_name: self.units[column_name]
                for column_name in output.columns
                if column_name in self.units
            }

        return output
