import pandas as pd


class BaseSubFrame(pd.DataFrame):
    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of ScattererDataFrame."""
        return self.__class__
