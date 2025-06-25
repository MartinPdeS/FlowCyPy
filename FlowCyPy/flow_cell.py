from typing import List
import pandas as pd
import pint_pandas
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy.population import BasePopulation
from FlowCyPy.units import Quantity
from FlowCyPy import units
from FlowCyPy.sub_frames.scatterer import ScattererDataFrame
from FlowCyPy import helper
from FlowCyPy.binary.interface_flow_cell import FLOWCELL
from FlowCyPy.fluid_region import FluidRegion

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)

@dataclass(config=config_dict, kw_only=True)
class FlowCell(FLOWCELL):
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
    event_scheme : str
        Scheme for event sampling, 'uniform-random', 'sorted', 'poisson', 'preserve' (default: 'preserve').
    """
    width: Quantity
    height: Quantity
    sample_volume_flow: Quantity
    sheath_volume_flow: Quantity
    mu: Quantity = 1e-3 * units.pascal * units.second
    N_terms: int = 25
    n_int: int = 200
    event_scheme: str = 'preserve'

    @field_validator('width', 'height', mode='plain')
    def validate_length(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with length units [<prefix>meter].")

        if not value.check('meter'):
            raise ValueError(f"{field} must be a Quantity with meter units [<prefix>meter], but got {value.units}.")

        return value

    @field_validator('sample_volume_flow', 'sheath_volume_flow', mode='plain')
    def validate_volumn_flow(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with volume flow [<prefix>liter / second].")

        if not value.check('liter / second'):
            raise ValueError(f"{field} must be a Quantity with volume flow units [<prefix>liter / second], but got {value.units}.")

        return value

    @helper.validate_input_units(run_time=units.second)
    def get_sample_volume(self, run_time: Quantity) -> Quantity:
        """
        Computes the volume passing through the flow cell over the given run time.
        """
        return (self.sample.area * self.sample.average_flow_speed * run_time).to_compact()

    def __post_init__(self):
        super().__init__(
            width=self.width.to('meter').magnitude,
            height=self.height.to('meter').magnitude,
            sample_volume_flow=self.sample_volume_flow.to('meter**3 / second').magnitude,
            sheath_volume_flow=self.sheath_volume_flow.to('meter**3 / second').magnitude,
            viscosity=self.mu.to('pascal * second').magnitude,
            N_terms=self.N_terms,
            n_int=self.n_int,
        )

        self.sample = FluidRegion(self._cpp_sample)
        self.sheath = FluidRegion(self._cpp_sheath)

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
        x, y, velocities = self._cpp_sample_transverse_profile(n_samples)

        return x * units.meter, y * units.meter, velocities * units.meter / units.second

    @helper.validate_input_units(run_time=units.second)
    def _generate_event_dataframe(self, populations: List[BasePopulation], run_time: Quantity) -> ScattererDataFrame:
        """
        Generates a DataFrame of event times and sampled velocities for each population based on the specified scheme.
        """
        sampling_dict = {
            p.name: {} for p in populations
        }

        for population in populations:
            sub_dict = sampling_dict[population.name]

            particle_flux = population.particle_count.compute_particle_flux(
                flow_speed=self.sample.average_flow_speed,
                flow_area=self.sample.area,
                run_time=run_time
            )

            arrival_time = self._cpp_sample_arrival_times(
                run_time=run_time.to('second').magnitude,
                particle_flux=particle_flux.to('particle / second').magnitude,
            ) * units.second

            n_events = len(arrival_time)

            sub_dict['n_elements'] = len(arrival_time)

            sub_dict['Time'] = arrival_time

            sub_dict.update(
                population.generate_property_sampling(n_events)
            )

            sub_dict["x"], sub_dict["y"], sub_dict["Velocity"] = self.sample_transverse_profile(n_events)


        event_dataframe = self._get_dataframe_from_dict(
            dictionnary=sampling_dict,
            level_names=['Population', 'ScattererID']
        )

        event_dataframe.re_order_events(
            event_scheme=self.event_scheme,
        )

        return event_dataframe

    def _get_dataframe_from_dict(self, dictionnary: dict, level_names: list = None) -> ScattererDataFrame:
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

        return ScattererDataFrame(pd.concat(dfs))