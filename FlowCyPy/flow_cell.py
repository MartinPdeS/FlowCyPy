from typing import List
import numpy as np
import pandas as pd
import pint_pandas
from pydantic.dataclasses import dataclass
from pint_pandas import PintArray
from pydantic import field_validator
from FlowCyPy.population import BasePopulation
from FlowCyPy.units import Quantity
from FlowCyPy import units
from FlowCyPy.sub_frames.scatterer import ScattererDataFrame
from FlowCyPy import helper
from matplotlib.patches import Rectangle

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict, kw_only=True)
class FluidRegion:
    height: Quantity
    width: Quantity
    volume_flow: Quantity
    max_flow_speed: Quantity = None
    average_flow_speed: Quantity = None

    @property
    def area(self) -> Quantity:
        return self.height * self.width

    def _add_to_plot(self, ax, length_units, color, label=None):
        rect = Rectangle(
            (-self.width.to(length_units).magnitude / 2, -self.height.to(length_units).magnitude / 2),
            self.width.to(length_units).magnitude,
            self.height.to(length_units).magnitude,
            fill=True,
            edgecolor='black',
            facecolor=color,
            alpha=0.8,
            linewidth=1,
            zorder=-1,
            label=label
        )
        ax.add_patch(rect)



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
            \left[
                1 - \frac{
                        \cosh\left(\frac{n\pi y}{2b}\right)
                    }{
                        \cosh\left(\frac{n\pi a}{2b}\right)
                    }
            \right]
       \sin\left(\frac{n\pi (z+b)}{2b}\right)

    where:

       - :math:`a` is the half-width of the channel (in the y-direction),
       - :math:`b` is the half-height of the channel (in the z-direction),
       - :math:`mu` is the dynamic viscosity,
       - :math:`dp/dx` is the pressure gradient driving the flow,
       - the summation is over odd integers (i.e. :math:`n = 1, 3, 5, ...`).

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

    @helper.validate_units(run_time=units.second)
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

        self.sample = FluidRegion(
            height=height_sample,
            width=width_sample,
            volume_flow=self.sample_volume_flow,
            max_flow_speed=self.u_center,
            average_flow_speed=average_flow_speed_sample,
        )

        self.sheath = FluidRegion(
            height=self.height,
            width=self.width,
            volume_flow=self.sheath_volume_flow,
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
            u += term_y * term_z / n ** 3

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
        Q = np.trapezoid(np.trapezoid(U, y_vals, axis=1), z_vals)

        # Restore the original dpdx if it was set.
        if dpdx_saved is not None:
            self.dpdx = dpdx_saved
        return Q

    def sample_transverse_profile(self, n_samples: int) -> tuple:
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
        x_samples = np.random.uniform(-self.sample.width.magnitude / 2, self.sample.width.magnitude / 2, n_samples) * self.sample.width.units
        y_samples = np.random.uniform(-self.sample.height.magnitude / 2, self.sample.height.magnitude / 2, n_samples) * self.sample.height.units

        velocities = self.velocity(x_samples, y_samples).to('meter / second')
        if len(velocities) !=0:
            velocities = velocities.to(velocities.max().to_compact().units)

        return x_samples, y_samples, velocities

    @helper.validate_units(run_time=units.second)
    def _generate_event_dataframe(self, populations: List[BasePopulation], run_time: Quantity) -> pd.DataFrame:
        """
        Generates a DataFrame of event times and sampled velocities for each population based on the specified scheme.
        """
        sampling_dict = {
            p.name: {} for p in populations
        }

        for population in populations:
            sub_dict = sampling_dict[population.name]

            arrival_time = self._get_population_arrival_time(run_time=run_time, population=population)

            n_events = len(arrival_time)

            sub_dict['n_elements'] = len(arrival_time)

            sub_dict['Time'] = arrival_time

            sub_dict.update(
                population.generate_property_sampling(n_events)
            )

            sub_dict["x"], sub_dict["y"], sub_dict["Velocity"] = self.sample_transverse_profile(n_events)


        scatterer_dataframe = self.get_dataframe_from_dict(
            dictionnary=sampling_dict,
            level_names=['Population', 'ScattererID']
        )

        scatterer_dataframe = ScattererDataFrame(scatterer_dataframe)

        self.order_events(
            scatterer_dataframe=scatterer_dataframe,
            event_scheme=self.event_scheme
        )

        return scatterer_dataframe

    def order_events(self, scatterer_dataframe: pd.DataFrame, event_scheme: str) -> pd.DataFrame:
        """
        Orders the events in the DataFrame by their arrival time.

        Parameters
        ----------
        scatterer_dataframe : pd.DataFrame
            DataFrame containing the events with a 'Time' column.
        event_scheme : str
            The scheme used to generate the events, e.g., 'uniform-random' or 'uniform-sequential'.

        Returns
        -------
        pd.DataFrame
            Ordered DataFrame with events sorted by 'Time'.
        """
        if scatterer_dataframe.empty:
            return

        start_time = scatterer_dataframe['Time'].min() * 1.1
        stop_time = scatterer_dataframe['Time'].max() * 0.9

        if not scatterer_dataframe.empty and event_scheme.lower() in ['uniform-random', 'uniform-sequential']:
            total_events = len(scatterer_dataframe)

            evenly_spaced_times = np.linspace(start_time, stop_time, total_events)

            if self.event_scheme.lower() == 'uniform-random':
                np.random.shuffle(evenly_spaced_times.magnitude)

            scatterer_dataframe['Time'] = PintArray(evenly_spaced_times.to(units.second).magnitude, units.second)

    def _get_population_arrival_time(self, run_time: Quantity, population: BasePopulation) -> pd.DataFrame:
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

        return arrival_times


    def get_dataframe_from_dict(self, dictionnary: dict, level_names: list = None) -> pd.DataFrame:
        dfs = []
        for pop_name, inner_dict in dictionnary.items():

            df_pop = pd.DataFrame(
                index=range(inner_dict.pop('n_elements'))
            )

            df_pop.index = pd.MultiIndex.from_product(
                [[pop_name], df_pop.index],
                names=level_names
            )

            for k, v in inner_dict.items():
                df_pop[k] = pint_pandas.PintArray(v.magnitude, v.units)

            dfs.append(df_pop)

        if len(dfs) == 0:
            return pd.DataFrame(columns=level_names).set_index(level_names)

        return pd.concat(dfs)