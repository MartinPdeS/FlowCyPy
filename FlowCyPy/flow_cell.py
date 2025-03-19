from typing import List
import numpy as np
import warnings
import pandas as pd
from pydantic.dataclasses import dataclass
from pint_pandas import PintArray
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from pydantic import field_validator
from FlowCyPy.population import BasePopulation
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.units import Quantity
from FlowCyPy import units
from FlowCyPy.helper import validate_units
from FlowCyPy.dataframe_subclass import ScattererDataFrame

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


class NameSpace():
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)



@dataclass(config=config_dict, kw_only=True)
class FlowCell:
    r"""
    Represents a rectangular flow cell in which the velocity field is computed from an
    analytical Fourier series solution for pressure-driven flow. The focused sample region
    is estimated from the volumetric flow rates of the sample and sheath fluids.

    The analytical solution for the x-direction velocity in a rectangular channel is given by:

    .. math::

       u(y,z) = \frac{16b^2}{\pi^3 \mu}\left(-\frac{dp}{dx}\right)
       \sum_{\substack{n=1,3,5,\ldots}}^{\infty} \frac{1}{n^3}
       \left[ 1 - \frac{\cosh\left(\frac{n\pi y}{2b}\right)}
       {\cosh\left(\frac{n\pi a}{2b}\right)} \right]
       \sin\left(\frac{n\pi (z+b)}{2b}\right)

    where:

       - ``a`` is the half-width of the channel (in the y-direction),
       - ``b`` is the half-height of the channel (in the z-direction),
       - ``mu`` is the dynamic viscosity,
       - ``dp/dx`` is the pressure gradient driving the flow,
       - the summation is over odd integers (i.e. ``n = 1, 3, 5, ...``).

    The derivation of this solution is based on the method of separation of variables and
    eigenfunction expansion applied to the Poisson equation for fully developed laminar flow.
    The validity of this approach and the resulting solution for rectangular ducts is well documented
    in classical fluid mechanics texts.

    **References**

    - Shah, R.K. & London, A.L. (1978). *Laminar Flow in Ducts*. Academic Press.
    - White, F.M. (2006). *Viscous Fluid Flow* (3rd ed.). McGraw-Hill.
    - Happel, J. & Brenner, H. (1983). *Low Reynolds Number Hydrodynamics*. Martinus Nijhoff.
    - Di Carlo, D. (2009). "Inertial Microfluidics," *Lab on a Chip*, 9, 3038-3046.

    In flow cytometry, hydrodynamic focusing is used to narrow the sample stream for optimal optical interrogation.
    The same theoretical framework for rectangular duct flow is applied to these microfluidic devices.

    Parameters
    ----------
    width : Quantity
        Width of the channel in the y-direction (m).
    height : Quantity
        Height of the channel in the z-direction (m).
    mu : Quantity
        Dynamic viscosity of the fluid (Pa·s).
    sample_volume_flow : Quantity
        Volumetric flow rate of the sample fluid (m³/s).
    sheath_volume_flow : Quantity
        Volumetric flow rate of the sheath fluid (m³/s).
    N_terms : int, optional
        Number of odd terms to use in the Fourier series solution (default: 25).
    n_int : int, optional
        Number of grid points for numerical integration over the channel cross-section (default: 200).

    Attributes
    ----------
    Q_total : Quantity
        Total volumetric flow rate (m³/s).
    dpdx : float
        Computed pressure gradient (Pa/m) driving the flow.
    u_center : float
        Centerline velocity, i.e. u(0,0) (m/s).
    width_sample : Quantity
        Width of the focused sample region (m).
    height_sample : Quantity
        Height of the focused sample region (m).
    """
    width: Quantity
    height: Quantity
    sample_volume_flow: Quantity
    sheath_volume_flow: Quantity
    mu: Quantity = 1e-3 * units.pascal * units.second
    N_terms: int = 25
    n_int: int = 200

    event_scheme: str = 'poisson'

    @field_validator('width', 'height', mode='plain')
    def validate_polarization(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with length units [<prefix>meter].")

        if not value.check('meter'):
            raise ValueError(f"{field} must be a Quantity with meter units [<prefix>meter], but got {value.units}.")

        return value

    @field_validator('sample_volume_flow', 'sheath_volume_flow', mode='plain')
    def validate_polarization(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with volume flow [<prefix>liter / second].")

        if not value.check('liter / second'):
            raise ValueError(f"{field} must be a Quantity with volume flow units [<prefix>liter / second], but got {value.units}.")

        return value

    @validate_units(run_time=units.second)
    def get_sample_volume(self, run_time: Quantity) -> Quantity:
        """
        Computes the volume passing through the flow cell over the given run time.
        """
        return (self.sample.area * self.sample.average_flow_speed * run_time).to_compact()

    def __post_init__(self):
        # Total volumetric flow rate: Q_total = Q_sample + Q_sheath.
        self.Q_total = self.sample_volume_flow + self.sheath_volume_flow

        # Compute dp/dx using the linearity of the solution (u ∝ -dp/dx)
        # with a reference pressure gradient of -1 Pa/m.
        self.dpdx_ref = -1.0  # Reference pressure gradient in Pa/m.
        Q_ref = self._compute_channel_flow(self.dpdx_ref, self.n_int)
        # The actual pressure gradient is given by:
        self.dpdx = self.dpdx_ref * (self.Q_total / Q_ref)

        # Compute the center velocity u(0,0)
        self.u_center = self.velocity(0.0 * units.meter, 0.0 * units.meter)

        # Estimate the sample region area: A_sample = Q_sample / u(0,0)
        area_sample = self.sample_volume_flow / self.u_center
        # Assuming the sample region is a centered rectangle with:
        #   A_sample = (2 * a_sample) * (2 * b_sample) = 4 * a_sample * b_sample,
        # and preserving the aspect ratio: a_sample / b_sample = a / b,
        # compute:
        height_sample = np.sqrt((area_sample * self.height) / (4 * self.width)) * 2
        width_sample = (self.width / self.height) * height_sample
        average_flow_speed_sample = self.sample_volume_flow / area_sample

        self.sample = NameSpace(
            height=height_sample,
            width=width_sample,
            area=area_sample,
            volume_flow=self.sample_volume_flow,
            max_flow_speed=self.u_center,
            average_flow_speed=average_flow_speed_sample
        )

    def velocity(self, y: float, z: float) -> float:
        r"""
        Compute the local x-direction velocity at the point (y, z) using the Fourier series solution.

        The velocity is computed as:

        .. math::

           u(y,z) = \frac{16b^2}{\pi^3 \mu}\left(-\frac{dp}{dx}\right)
           \sum_{\substack{n=1,3,5,\ldots}}^{\infty} \frac{1}{n^3}
           \left[ 1 - \frac{\cosh\left(\frac{n\pi y}{2b}\right)}
           {\cosh\left(\frac{n\pi a}{2b}\right)} \right]
           \sin\left(\frac{n\pi (z+b)}{2b}\right)

        Parameters
        ----------
        y : float or array_like
            y-coordinate (m). Can be a scalar or a NumPy array.
        z : float or array_like
            z-coordinate (m). Can be a scalar or a NumPy array.

        Returns
        -------
        u : float or ndarray
            Local velocity (m/s) at (y, z).
        """
        u = np.zeros_like(y, dtype=np.float64)
        prefactor = (4 * self.height**2 / (np.pi**3 * self.mu)) * (-self.dpdx)
        n_values = np.arange(1, 2 * self.N_terms, 2)  # n = 1, 3, 5, ...
        for n in n_values:
            term_y = 1 - np.cosh((n * np.pi * y) / self.height) / np.cosh((n * np.pi * self.width / 2) / self.height)
            term_z = np.sin((n * np.pi * (z + (self.height / 2))) / self.height)
            u += term_y * term_z / n**3
        return prefactor * u

    def _compute_channel_flow(self, dpdx: float, n_int: int) -> float:
        r"""
        Numerically compute the total volumetric flow rate in the channel for a given pressure gradient.

        The volumetric flow rate is defined as:

        .. math::

           Q = \int_{-b}^{b}\int_{-a}^{a} u(y,z) \, dy \, dz

        where :math:`u(y,z)` is the local velocity computed from the Fourier series solution.

        Parameters
        ----------
        dpdx : float
            Pressure gradient (Pa/m).
        n_int : int
            Number of grid points per dimension for integration.

        Returns
        -------
        Q : float
            Total volumetric flow rate (m³/s).
        """
        # Temporarily set dpdx to the provided value.
        dpdx_saved = self.dpdx if hasattr(self, 'dpdx') else None
        self.dpdx = dpdx

        y_vals = np.linspace(-self.width / 2, self.width / 2, n_int)
        z_vals = np.linspace(-self.height / 2, self.height / 2, n_int)
        Y, Z = np.meshgrid(y_vals, z_vals)
        U = self.velocity(Y, Z)

        # Compute the 2D integral over the channel cross-section using the composite trapezoidal rule.
        Q = np.trapz(np.trapz(U, y_vals, axis=1), z_vals)

        # Restore the original dpdx if it was set.
        if dpdx_saved is not None:
            self.dpdx = dpdx_saved
        return Q

    def sample_particles(self, n_samples: int) -> tuple:
        r"""
        Sample particles from the focused sample stream.

        The sample stream is assumed to be uniformly distributed over a centered rectangular region
        defined by:

        .. math::

           y \in [-a_{\text{sample}}, a_{\text{sample}}] \quad \text{and} \quad
           z \in [-b_{\text{sample}}, b_{\text{sample}}]

        The area of the sample region is given by:

        .. math::

           A_{\text{sample}} = 4\,a_{\text{sample}}\,b_{\text{sample}}

        and is estimated as:

        .. math::

           A_{\text{sample}} = \frac{Q_{\text{sample}}}{u(0,0)}.

        Parameters
        ----------
        n_samples : int
            Number of particles to sample.

        Returns
        -------
        positions : ndarray
            A NumPy array of shape (n_samples, 2) containing the [y, z] coordinates (in m).
        velocities : ndarray
            A NumPy array of shape (n_samples,) containing the local x-direction velocities (in m/s).
        """
        # Here we assume that the "Quantity" type has attributes 'magnitude' and 'units'.
        # Adjust this section for your specific unit system.
        y_samples = np.random.uniform(-self.sample.width.magnitude / 2, self.sample.width.magnitude / 2, n_samples) * self.sample.width.units
        z_samples = np.random.uniform(-self.sample.height.magnitude / 2, self.sample.height.magnitude / 2, n_samples) * self.sample.height.units

        velocities = self.velocity(y_samples, z_samples).to('meter / second')
        return y_samples, z_samples, velocities.to(velocities.max().to_compact().units)

    @validate_units(run_time=units.second)
    def get_population_sampling(self, run_time: Quantity, scatterer_collection: ScattererCollection) -> List[Quantity]:
        """
        Calculates the number of events (particle counts) for each population based on run time.
        """
        return [
            p.particle_count.calculate_number_of_events(
                flow_area=self.sample.area,
                flow_speed=self.sample.average_flow_speed,
                run_time=run_time
            )
            for p in scatterer_collection.populations
        ]

    @validate_units(run_time=units.second)
    def _generate_poisson_events(self, run_time: Quantity, population: BasePopulation) -> pd.DataFrame:
        """
        Generates particle arrival times using a Poisson process and samples a velocity for each event.
        """
        particle_flux = population.particle_count.compute_particle_flux(
            flow_speed=self.sample.average_flow_speed,
            flow_area=self.sample.area,
            run_time=run_time
        )
        expected_particles = particle_flux * run_time

        inter_arrival_times = np.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.magnitude)
        ) / (particle_flux.units) * units.particle

        arrival_times = np.cumsum(inter_arrival_times)
        arrival_times = arrival_times[arrival_times <= run_time]

        dataframe = pd.DataFrame()
        dataframe['Time'] = PintArray(arrival_times, dtype=arrival_times.units)

        # Sample velocity for each event using the geometry-specific velocity profile.
        x, y, velocities = self.sample_particles(len(arrival_times))

        dataframe['Velocity'] = PintArray(velocities, dtype=velocities.units)

        dataframe['x'] = PintArray(x, dtype=x.units)
        dataframe['y'] = PintArray(y, dtype=y.units)

        if len(dataframe) == 0:
            warnings.warn("Population has been initialized with 0 events.")

        return dataframe

    @validate_units(run_time=units.second)
    def _generate_event_dataframe(self, populations: List[BasePopulation], run_time: Quantity) -> pd.DataFrame:
        """
        Generates a DataFrame of event times and sampled velocities for each population based on the specified scheme.
        """
        population_event_frames = [
            self._generate_poisson_events(run_time=run_time, population=population)
            for population in populations
        ]

        # Loop over each dataframe to make sure they share the same units
        ref_dataframe = population_event_frames[0]
        for df in population_event_frames:
            for col in df.columns:
                df[col] = df[col].pint.to(ref_dataframe[col].pint.units)

        event_dataframe = pd.concat(population_event_frames, keys=[pop.name for pop in populations])

        event_dataframe.index.names = ["Population", "Index"]

        if self.event_scheme.lower() in ['uniform-random', 'uniform-sequential']:
            total_events = len(event_dataframe)
            start_time = 0 * run_time.units
            end_time = run_time
            time_interval = (end_time - start_time) / total_events
            evenly_spaced_times = np.arange(0, total_events) * time_interval

            if self.event_scheme.lower() == 'uniform-random':
                np.random.shuffle(evenly_spaced_times.magnitude)
            event_dataframe['Time'] = PintArray(evenly_spaced_times.to(units.second).magnitude, units.second)

        scatterer_dataframe = ScattererDataFrame(event_dataframe)
        scatterer_dataframe.attrs['run_time'] = run_time
        return scatterer_dataframe

    def plot(self, n_samples: int) -> None:
        r"""
        Plot the spatial distribution of sampled particles and color-code them by their local x-direction velocity.

        This method samples a specified number of particles from the focused sample stream and
        generates a scatter plot of their positions in the y-z plane. In addition, the plot includes overlays
        for the channel boundaries (representing the full flow cell, i.e. sheath + sample regions) and the sample
        region boundaries.

        Parameters
        ----------
        n_samples : int
            Number of particles to sample and plot.
        """
        y_vals, z_vals, velocities = self.sample_particles(n_samples)

        length_units = self.width.units

        # Create plot
        with plt.style.context(mps):
            _, ax = plt.subplots()

        sc = ax.scatter(
            y_vals.to(length_units).magnitude,
            z_vals.to(length_units).magnitude,
            c=velocities.magnitude,
            cmap="viridis",
            edgecolor="black",
            label='Particle sampling'
        )

        plt.colorbar(sc, label=f"Velocity [{velocities.units}]")

        ax.set(
            xlabel=f"y [{length_units}]",
            ylabel=f"z [{length_units}]",
            title="Particle Spatial Distribution and Speed"
        )

        from matplotlib.patches import Rectangle

        # Plot channel boundary.
        channel_rect = Rectangle(
            (-self.width.to(length_units).magnitude / 2, -self.height.to(length_units).magnitude / 2),
            self.width.to(length_units).magnitude,
            self.height.to(length_units).magnitude,
            fill=True,
            edgecolor='black',
            facecolor='lightblue',
            alpha=0.8,
            zorder=-1,
            linewidth=1,
            label="Sheath fluid"
        )
        ax.add_patch(channel_rect)

        # Plot sample region boundary.
        sample_rect = Rectangle(
            (-self.sample.width.to(length_units).magnitude / 2, -self.sample.height.to(length_units).magnitude / 2),
            self.sample.width.to(length_units).magnitude,
            self.sample.height.to(length_units).magnitude,
            fill=True,
            edgecolor='black',
            alpha=0.8,
            facecolor='green',
            linewidth=1,
            zorder=-1,
            label="Sample Region"
        )
        ax.add_patch(sample_rect)

        ax.set_aspect('equal')

        plt.tight_layout()

        ax.legend(loc='upper right')

        plt.show()
