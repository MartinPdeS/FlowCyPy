from typing import List
from FlowCyPy.units import meter, second
from PyMieSim.units import Quantity
from tabulate import tabulate
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from pint_pandas import PintType, PintArray
from FlowCyPy.source import BaseBeam
import pandas
import numpy

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class FlowCell(object):
    """
    Models the flow parameters in a flow cytometer, including flow speed, flow area,
    and particle interactions. This class interacts with ScattererDistribution to simulate
    the flow of particles through the cytometer.

    Parameters
    ----------
    flow_speed : Quantity
        The speed of the flow in meters per second (m/s).
    flow_area : Quantity
        The cross-sectional area of the flow tube in square meters (m²).
    run_time : Quantity
        The total duration of the flow simulation in seconds.
    """
    flow_speed: Quantity
    flow_area: Quantity
    run_time: Quantity

    source: BaseBeam = None
    
    @field_validator('flow_speed')
    def _validate_flow_speed(cls, value):
        """
        Validates that the flow speed is provided in meter per second.

        Parameters
        ----------
        value : Quantity
            The flow speed to validate.

        Returns
        -------
        Quantity
            The flow speed frequency.

        Raises:
            ValueError: If the flow speed is not in meter per second.
        """
        if not value.check(meter / second):
            raise ValueError(f"flow_speed must be in meter per second, but got {value.units}")
        return value

    @field_validator('flow_area')
    def _validate_flow_area(cls, value):
        """
        Validates that the flow area is provided in hertz.

        Parameters
        ----------
        value : Quantity
            The flow area to validate.

        Returns
        -------
        Quantity
            The validated flow area.

        Raises:
            ValueError: If the flow area is not in hertz.
        """
        if not value.check(meter ** 2):
            raise ValueError(f"flow_area must be in meter ** 2, but got {value.units}")
        return value

    @field_validator('run_time')
    def _validate_run_time(cls, value):
        """
        Validates that the total time is provided in second.

        Parameters
        ----------
        value : Quantity
            The total time to validate.

        Returns
        -------
        Quantity
            The validated total time.

        Raises:
            ValueError: If the total time is not in second.
        """
        if not value.check(second):
            raise ValueError(f"run_time must be in second, but got {value.units}")
        return value

    def __post_init__(self):
        """Initialize units for flow parameters."""
        self.flow_speed = Quantity(self.flow_speed, meter / second)
        self.flow_area = Quantity(self.flow_area, meter ** 2)
        self.run_time = Quantity(self.run_time, second)

        self.volume = self.flow_area * self.flow_speed * self.run_time

    def print_properties(self) -> None:
        """
        Print the core properties of the flow and particle interactions in the flow cytometer.
        """
        print("\nFlow Properties")
        print(tabulate(self.get_properties(), headers=["Property", "Value"], tablefmt="grid"))

    def get_properties(self) -> List[List[str]]:
        return [
            ['Flow Speed', f"{self.flow_speed:.2f~#P}"],
            ['Flow Area', f"{self.flow_area:.2f~#P}"],
            ['Total Time', f"{self.run_time:.2f~#P}"]
        ]
    
    def initialize(self, scatterer: object, size_units: str = 'micrometer') -> None:
        """
        Initializes particle size, refractive index, and medium refractive index distributions.

        Parameters
        ----------
        scatterer : Scatterer
            An instance of the Scatterer class that describes the scatterer collection being used.

        """        
        self.scatterer = scatterer

        for population in self.scatterer.populations:
            population.initialize(flow_cell=self)
            population.dataframe.Size = population.dataframe.Size.pint.to(size_units)
        
        if len(self.scatterer.populations) != 0:
            self.scatterer.dataframe = pandas.concat(
                [population.dataframe for population in self.scatterer.populations],
                axis=0,
                keys=[population.name for population in self.scatterer.populations],
            )
            self.scatterer.dataframe.index.names = ['Population', 'Index']

        else:
            dtypes = {
                'Time': PintType('second'),            # Time column with seconds unit
                'Position': PintType('meter'),         # Position column with meters unit
                'Size': PintType('meter'),        # Size column with micrometers unit
                'RefractiveIndex': PintType('meter')  # Dimensionless unit for refractive index
            }

            multi_index = pandas.MultiIndex.from_tuples([], names=["Population", "Index"])

            # Create an empty DataFrame with specified column types and a multi-index
            self.scatterer.dataframe = pandas.DataFrame(
                {col: pandas.Series(dtype=dtype) for col, dtype in dtypes.items()},
                index=multi_index
            )

        self.n_events = len(self.scatterer.dataframe)        

    def distribute_time_linearly(self, sequential_population: bool = False) -> None:
        """
        Distributes particle arrival times linearly across the total runtime of the flow cell.

        Optionally randomizes the order of times for all populations to simulate non-sequential particle arrivals.

        Parameters
        ----------
        sequential_population : bool, optional
            If `True`, organize the order of arrival times across all populations (default is `False`).

        """
        # Generate linearly spaced time values across the flow cell runtime
        linear_spacing = numpy.linspace(0, self.run_time, self.n_events)

        # Optionally randomize the linear spacing
        if not sequential_population:
            numpy.random.shuffle(linear_spacing)

        # Assign the linearly spaced or randomized times to the scatterer DataFrame
        self.scatterer.dataframe.Time = PintArray(linear_spacing, dtype=self.scatterer.dataframe.Time.pint.units)        