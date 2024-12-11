
import numpy as np
from typing import Union
from FlowCyPy import distribution
import pandas as pd
from dataclasses import field
import pint_pandas
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy.units import particle
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.utils import PropertiesReport
import logging
from PyMieSim.units import Quantity, RIU, meter
import warnings
from FlowCyPy.particle_count import ParticleCount


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Population(PropertiesReport):
    """
    A class representing a population of scatterers in a flow cytometry setup.

    Parameters
    ----------
    name : str
        Name of the population distribution.
    refractive_index : Union[distribution.Base, Quantity]
        Refractive index or refractive index distributions.
    size : Union[distribution.Base, Quantity]
        Particle size or size distributions.
    particle_count : ParticleCount
        Scatterer density in particles per cubic meter, default is 1 particle/m³.

    """
    name: str
    refractive_index: Union[distribution.Base, Quantity]
    size: Union[distribution.Base, Quantity]
    particle_count: ParticleCount = field(init=False)

    def __post_init__(self):
        """
        Automatically converts all Quantity attributes to their base SI units (i.e., without any prefixes).
        This strips units like millimeter to meter, kilogram to gram, etc.
        """
        # Convert all Quantity attributes to base SI units (without any prefixes)
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Quantity):
                # Convert the quantity to its base unit (strip prefix)
                setattr(self, attr_name, attr_value.to_base_units())

    @field_validator('concentration')
    def _validate_concentration(cls, value):
        """
        Validates that the concentration is expressed in units of inverse volume.

        Parameters
        ----------
        value : Quantity
            The concentration to validate.

        Returns
        -------
        Quantity
            The validated concentration.

        Raises
        ------
            ValueError: If the concentration is not expressed in units of inverse volume.
        """
        if not value.check('particles / [length]**3'):
            raise ValueError(f"concentration must be in units of particles per volume (e.g., particles/m^3), but got {value.units}")
        return value

    @field_validator('refractive_index')
    def _validate_refractive_index(cls, value):
        """
        Validates that the refractive index is either a Quantity or a valid distribution.Base instance.

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The refractive index to validate.

        Returns
        -------
        Union[distribution.Base, Quantity]
            The validated refractive index.

        Raises
        ------
        TypeError
            If the refractive index is not of type Quantity or distribution.Base.
        """
        if isinstance(value, Quantity):
            assert value.check(RIU), "The refractive index value provided does not have refractive index units [RIU]"
            return distribution.Delta(position=value)

        if isinstance(value, distribution.Base):
            return value

        raise TypeError(f"refractive_index must be of type Quantity<RIU or refractive_index_units> or distribution.Base, but got {type(value)}")

    @field_validator('size')
    def _validate_size(cls, value):
        """
        Validates that the size is either a Quantity or a valid distribution.Base instance.

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The size to validate.

        Returns
        -------
        Union[distribution.Base, Quantity]
            The validated size.

        Raises
        ------
        TypeError
            If the size is not of type Quantity or distribution.Base.
        """
        if isinstance(value, Quantity):
            assert value.check(meter), "The size value provided does not have length units [meter]"
            return distribution.Delta(position=value)

        if isinstance(value, distribution.Base):
            return value

        raise TypeError(f"suze must be of type Quantity or distribution.Base, but got {type(value)}")

    def initialize(self, flow_cell: FlowCell) -> None:
        self.dataframe = pd.DataFrame()

        if isinstance(self.size, Quantity):
            self.size = distribution.Delta(size_value=self.size)

        self.flow_cell = flow_cell

        self.n_events = self.particle_count.calculate_number_of_events(
            flow_area=self.flow_cell.flow_area,
            flow_speed=self.flow_cell.flow_speed,
            run_time=self.flow_cell.run_time
        )

        self._generate_longitudinal_positions()

        logging.info(f"Population [{self.name}] initialized with an estimated {self.n_events}.")

        size = self.size.generate(self.n_events)
        self.dataframe['Size'] = pint_pandas.PintArray(size, dtype=size.units)

        ri = self.refractive_index.generate(self.n_events)
        self.dataframe['RefractiveIndex'] = pint_pandas.PintArray(ri, dtype=ri.units)

    def _generate_longitudinal_positions(self) -> None:
        r"""
        Generate particle arrival times over the entire experiment duration based on a Poisson process.

        In flow cytometry, the particle arrival times can be modeled as a Poisson process, where the time
        intervals between successive particle arrivals follow an exponential distribution. The average rate
        of particle arrivals (the particle flux) is given by:

        .. math::
            \text{Particle Flux} = \rho \cdot v \cdot A

        where:
        - :math:`\rho` is the scatterer density (particles per cubic meter),
        - :math:`v` is the flow speed (meters per second),
        - :math:`A` is the cross-sectional area of the flow tube (square meters).

        The number of particles arriving in a given time interval follows a Poisson distribution, and the
        time between successive arrivals follows an exponential distribution. The mean inter-arrival time
        is the inverse of the particle flux:

        .. math::
            \Delta t \sim \text{Exponential}(1/\lambda)

        where:
            - :math:`\Delta t` is the time between successive particle arrivals,
            - :math:`\lambda` is the particle flux (particles per second).

        Steps:
            1. Compute the particle flux, which is the average number of particles passing through the detection
            region per second.
            2. Calculate the expected number of particles over the entire experiment duration.
            3. Generate random inter-arrival times using the exponential distribution.
            4. Compute the cumulative arrival times by summing the inter-arrival times.
            5. Ensure that all arrival times fall within the total experiment duration.

        Returns
        -------
        np.ndarray
            An array of particle arrival times (in seconds) for the entire experiment duration, based on the Poisson process.
        """
        # Step 1: Compute the average particle flux (particles per second)
        particle_flux = self.particle_count.compute_particle_flux(
            flow_speed=self.flow_cell.flow_speed,
            flow_area=self.flow_cell.flow_area,
            run_time=self.flow_cell.run_time
        )

        # Step 2: Calculate the expected number of particles over the entire experiment
        expected_particles = self.n_events

        # Step 3: Generate inter-arrival times (exponentially distributed)
        inter_arrival_times = np.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.magnitude)
        ) / (particle_flux.units / particle)

        # Step 4: Compute cumulative arrival times
        arrival_times = np.cumsum(inter_arrival_times)

        # Step 5: Limit the arrival times to the total experiment duration
        arrival_times = arrival_times[arrival_times <= self.flow_cell.run_time]

        time = arrival_times[arrival_times <= self.flow_cell.run_time]
        self.dataframe['Time'] = pint_pandas.PintArray(time, dtype=time.units)

        position = arrival_times * self.flow_cell.flow_speed

        self.dataframe['Position'] = pint_pandas.PintArray(position, dtype=position.units)

        self.n_events = len(arrival_times) * particle

        if self.n_events == 0:
            warnings.warn("Population has been initialized with 0 events.")

from FlowCyPy.populations_instances import *  # noqa F403
