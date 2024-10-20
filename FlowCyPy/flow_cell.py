from typing import List
from FlowCyPy.units import meter, second, particle
from PyMieSim.units import Quantity
from tabulate import tabulate
from pydantic.dataclasses import dataclass
from pydantic import field_validator

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class FlowCell:
    """
    A class to model the flow parameters in a flow cytometer, including flow speed, flow area,
    and particle interactions. This class interacts with ScattererDistribution to simulate
    the flow of particles through the cytometer.

    Parameters
    ----------
    flow_speed : float
        The speed of the flow in meters per second (m/s).
    flow_area : float
        The cross-sectional area of the flow tube in square meters (m²).
    run_time : float
        The total duration of the flow simulation in seconds.
    scatterer_density : float
        The density of the scatterers (particles) in particles per cubic meter (particles/m³).
    """

    flow_speed: Quantity  # Flow speed in meters/second (default: 80 µm/s)
    flow_area: Quantity  # Cross-sectional area in square meters (default: 1 µm²)
    run_time: Quantity  # Total simulation time in seconds (default: 1 second)

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

    def calculate_number_of_events(self, concentration: Quantity) -> int:
        """
        Calculate the total number of particles based on the scatterer density, flow speed, and flow area.

        Returns
        -------
        int
            The total number of particles in the flow.
        """
        # Volume swept by the flow over the total time
        volume = self.flow_area * self.flow_speed * self.run_time

        # Calculate the total number of particles in this volume
        number_of_particles = concentration * volume

        return number_of_particles.to(particle).round()

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
