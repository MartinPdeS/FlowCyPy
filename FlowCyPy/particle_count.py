# -*- coding: utf-8 -*-
from FlowCyPy.units import Quantity, particle, liter, second

class ParticleCount:
    """
    A class to represent the quantity of particles in a flow, which can be defined
    either as a concentration (particles per unit volume) or as a fixed number of particles.

    Parameters
    ----------
    value : Quantity
        The input quantity, either a concentration (e.g., particles/liter) or a fixed number of particles.
    """

    def __init__(self, value: Quantity):
        """
        Initializes the ParticleCount with either a concentration or a fixed number of particles.

        Parameters
        ----------
        value : Quantity
            A Quantity representing either a concentration (particles per unit volume)
            or a fixed number of particles.

        Raises
        ------
        ValueError
            If the input value does not have the expected dimensionality.
        """
        if isinstance(value, ParticleCount):
            self = value
            return

        if value.check(particle):
            # Fixed number of particles
            self.num_particles = value.to(particle)

        elif value.check(particle / liter):
            # Concentration of particles
            self.concentration = value.to(particle / liter)
        else:
            raise ValueError(
                "Value must have dimensions of either 'particles' or 'particles per unit volume'."
            )

    def calculate_number_of_events(self, flow_area: Quantity, flow_speed: Quantity, run_time: Quantity) -> Quantity:
        """
        Calculates the total number of particles based on the flow volume and the defined concentration.

        Parameters
        ----------
        flow_volume : Quantity
            The volume of the flow (e.g., in liters or cubic meters).

        Returns
        -------
        Quantity
            The total number of particles as a Quantity with the unit of 'particles'.

        Raises
        ------
        ValueError
            If no concentration is defined and the total number of particles cannot be calculated.
        """
        print('caluclate number of eecnts')
        if hasattr(self, 'concentration'):
            flow_volume = flow_area * flow_speed * run_time
            print('flow_volume', flow_volume)
            return (self.concentration * flow_volume).to(particle)
        elif hasattr(self, 'num_particles'):
            return self.num_particles
        else:
            raise ValueError("Either a number of particles or a concentration must be defined.")

    def compute_particle_flux(self, flow_speed: Quantity, flow_area: Quantity, run_time: Quantity) -> Quantity:
        """
        Computes the particle flux in the flow system, accounting for flow speed,
        flow area, and either the particle concentration or a predefined number of particles.

        Parameters
        ----------
        flow_speed : Quantity
            The speed of the flow (e.g., in meters per second).
        flow_area : Quantity
            The cross-sectional area of the flow tube (e.g., in square meters).
        run_time : Quantity
            The total duration of the flow (e.g., in seconds).

        Returns
        -------
        Quantity
            The particle flux in particles per second (particle/second).
        """
        if hasattr(self, 'num_particles'):
            return self.num_particles / run_time

        flow_volume_per_second = (flow_speed * flow_area).to(liter / second)
        particle_flux = (self.concentration * flow_volume_per_second).to(particle / second)
        return particle_flux

    def __repr__(self):
        if hasattr(self, 'concentration'):
            return f"{self.concentration}"
        else:
            return f"{self.num_particles}"

    def __truediv__(self, factor: float):
        if hasattr(self, 'concentration'):
            self.concentration /= factor
        else:
            self.num_particles /= factor

        return self

    def __mul__(self, factor: float):
        if hasattr(self, 'concentration'):
            self.concentration *= factor
        else:
            self.num_particles *= factor

        return self

    @property
    def value(self):
        if hasattr(self, 'concentration'):
            return self.concentration
        else:
            return self.num_particles

