from typing import List, Tuple
import numpy as np
import warnings
import pandas as pd
from pydantic.dataclasses import dataclass
from dataclasses import field
from pint_pandas import PintArray
import matplotlib.pyplot as plt
from MPSPlots.styles import mps

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

@dataclass(config=config_dict, kw_only=True)
class BaseFlowCell:
    """
    Base class for modeling the flow parameters in a flow cytometer.

    This class initializes with a volumetric flow rate (volume_flow) and a flow area,
    and computes the average flow speed as:
        flow_speed = volume_flow / flow_area

    Parameters
    ----------
    volume_flow : Quantity
        The volumetric flow rate (in m³/s).
    flow_area : Quantity
        The cross-sectional area of the flow cell (in m²).
    event_scheme : str, optional
        The event timing scheme, by default 'poisson'.
    """
    # Computed in __post_init__
    flow_speed: Quantity = field(init=False)  # type: ignore

    def __post_init__(self):
        # Compute flow_speed from volume_flow and flow_area
        self.flow_speed = (self.volume_flow / self.flow_area)

    @classmethod
    def _validate_flow_area(cls, value):
        if not value.check(units.meter ** 2):
            raise ValueError(f"flow_area must be in meter**2, but got {value.units}")
        return value

    @validate_units(run_time=units.second)
    def get_volume(self, run_time: Quantity) -> Quantity:
        """
        Computes the volume passing through the flow cell over the given run time.
        """
        return (self.volume_flow * run_time).to_compact()

    @validate_units(run_time=units.second)
    def get_population_sampling(self, run_time: Quantity, scatterer_collection: ScattererCollection) -> List[Quantity]:
        """
        Calculates the number of events (particle counts) for each population based on run time.
        """
        return [
            p.particle_count.calculate_number_of_events(
                flow_area=self.flow_area,
                flow_speed=self.flow_speed,
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
            flow_speed=self.flow_speed,
            flow_area=self.flow_area,
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
        x, y, velocities = self.sample_parameters(len(arrival_times))

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

    def sample_velocity(self) -> Quantity:
        """
        Abstract method to sample a velocity from the flow cell's velocity distribution.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement sample_velocity.")

    def plot_transverse_distribution(self, n_samples: int = 300, show: bool = True, ax: plt.Axes = None) -> None:
        """
        Generates a 3D visualization of particle positions and velocities in a rectangular flow cell.

        This method samples particle positions and their local velocities using the cell's
        sampling routine, then creates a 3D scatter plot where each particle is represented as a blue dot
        at \(z = 0\) (the channel cross-section) and its local velocity is depicted as a red vertical line.
        The boundary of the rectangular channel is overlaid as a green line connecting the four corners.

        The particle positions are sampled over the rectangular area \([-w/2, w/2] \times [-h/2, h/2]\),
        with hydrodynamic focusing applied via the focusing_factor parameter. The local velocity is computed
        using the bi-parabolic profile:

        \[
        v(x, y) = v_{\max} \left(1 - \left(\frac{2x}{w}\right)^2\right) \left(1 - \left(\frac{2y}{h}\right)^2\right),
        \]

        where \(v_{\max} \approx 1.5\,v_{\text{avg}}\) and \(v_{\text{avg}} = \frac{\text{volume\_flow}}{w \times h}\).

        Parameters
        ----------
        n_samples : int
            The number of particle samples to generate for the visualization.

        Returns
        -------
        None
        """
        # Sample particle parameters: positions (x, y) and local velocity v.
        x, y, v = self.sample_parameters(n_samples=n_samples)

        # Create a new 3D figure
        if ax is None:
            with plt.style.context(mps):
                figure = plt.figure(figsize=(10, 8))
                ax = figure.add_subplot(111, projection='3d')

        # Plot particle positions at z = 0
        ax.scatter(x, y, np.zeros_like(x), color='blue', label='Particle Position')

        # Convert Pint quantities to numerical arrays for plotting
        x_m = x.magnitude
        y_m = y.to(x.units).magnitude
        v_m = v.magnitude

        # Plot velocity vectors using quiver without arrowheads; vectors extend vertically.
        ax.quiver(
            x_m, y_m, np.zeros_like(x_m),
            np.zeros_like(x_m), np.zeros_like(y_m), v_m,
            arrow_length_ratio=0.0, normalize=False, color='red', label='Velocity'
        )

        self._add_boundary_to_ax(ax=ax, length_units=x.units)

        ax.set_xlabel(f'x [{x.units}]')
        ax.set_ylabel(f'y [{y.units}]')
        ax.set_zlabel(f'Velocity [{v.units}]')
        ax.set_title('3D Visualization of Particle Positions and Velocities in Rectangular Flow Cell')
        ax.set_zlim([0, v_m.max()])
        ax.legend()

        plt.tight_layout()

        if show:
            plt.show()

        return ax



@dataclass(config=config_dict, kw_only=True)
class CircularFlowCell(BaseFlowCell):
    """
    Models a circular flow cell, where the cross-section is assumed to be a circle.
    The velocity profile is derived from Poiseuille flow:
        v(r) = v_max * (1 - (r/R)^2),
    where R is the tube radius and v_max = 2 * v_avg.

    This class now provides an option for hydrodynamic focusing. The parameter
    'focusing_factor' (between 0 and 1) adjusts the probability density function (PDF)
    for particle radial positions. With focusing_factor = 0, particles are uniformly distributed
    over the area, following:
        P(r) = 2r / R^2.
    With focusing_factor = 1, particles are ideally focused at the center (r = 0). Intermediate values
    interpolate between these distributions.

    Parameters
    ----------
    volume_flow : Quantity
        The volumetric flow rate (in m³/s).
    radius : Quantity
        The tube radius (in meters).
    event_scheme : str, optional
        The event timing scheme, by default 'poisson'.
    focusing_factor : float, optional
        A value between 0 (no focusing, uniform distribution) and 1 (ideal focusing at the center).
        Default is 0.
    """
    volume_flow: Quantity
    radius: Quantity
    event_scheme: str = 'poisson'
    focusing_factor: float = 1.0  # 0: uniform; 1: all at center

    def __post_init__(self):
        self.flow_area = np.pi * self.radius ** 2
        return super().__post_init__()

    def get_velocity_profile(self, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes the velocity profile for a circular flow cell using Poiseuille flow.

        For a circular tube, the velocity profile is given by:
            v(r) = v_max * (1 - (r / R)^2)
        where:
            - r is the radial distance from the center of the tube,
            - R is the tube radius,
            - v_max is the maximum velocity at the center, which is 2 * v_avg,
            - v_avg is the average flow speed (computed as volume_flow / flow_area).

        Parameters
        ----------
        num_points : int, optional
            The number of discrete points along the radius to compute the velocity (default is 100).

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            r: 1D numpy array of radial positions from 0 to R (in meters).
            velocities: 1D numpy array of corresponding velocities (in m/s).
        """
        r = np.linspace(0, self.radius, num_points)
        velocities = 2 * self.flow_speed * (1 - (r / self.radius)**2)
        return r, velocities.to(units.meter / units.second)

    def sample_velocity(self, n_samples: int = 1) -> Quantity:
        """
        Samples a velocity for a particle in a circular flow cell from the Poiseuille flow distribution,
        with an option to apply hydrodynamic focusing.

        The standard PDF for the radial position in a uniformly distributed circular channel is:
            P(r) = 2r / R^2   for 0 ≤ r ≤ R,
        where R is the tube radius. To incorporate hydrodynamic focusing, we scale the sampled radial position
        by (1 - focusing_factor). With focusing_factor = 0, particles are uniformly distributed (r = R * sqrt(u)).
        With focusing_factor = 1, particles are ideally focused at the center (r = 0).

        The local velocity is computed from the effective radial position using:
            v(r) = 2 * v_avg * (1 - (r / R)^2),
        where v_avg is the average flow speed.

        Parameters
        ----------
        n_samples : int, optional
            The number of velocity samples to generate (default is 1).

        Returns
        -------
        Quantity
            A Quantity representing the sampled velocity (or velocities) in meters per second.
        """
        # Uniform sampling: u ~ U(0,1)
        u = np.random.uniform(0, 1, size=n_samples)
        # Apply hydrodynamic focusing by scaling the sampled radial position.
        # If focusing_factor = 0: r_sample = R * sqrt(u) (uniform distribution)
        # If focusing_factor = 1: r_sample = 0 (perfect focusing)
        r_sample = (1 - self.focusing_factor) * self.radius * np.sqrt(u)
        # Compute local velocity using the Poiseuille profile: v(r) = 2 * v_avg * (1 - (r/R)^2)
        v_sample = 2 * self.flow_speed * (1 - (r_sample / self.radius)**2)
        return v_sample

    def sample_parameters(self, n_samples: int = 1) -> Quantity:

        # Uniform sampling: u ~ U(0,1)
        u = np.random.uniform(0, 1, size=n_samples)
        # Apply hydrodynamic focusing by scaling the sampled radial position.
        # If focusing_factor = 0: r_sample = R * sqrt(u) (uniform distribution)
        # If focusing_factor = 1: r_sample = 0 (perfect focusing)
        r_sample = (1 - self.focusing_factor) * self.radius * np.sqrt(u)

        theta = np.random.uniform(0, 2 * np.pi, size=n_samples)  # theta uniformly in [0, 2pi]
        x = r_sample * np.cos(theta)
        y = r_sample * np.sin(theta)


        # Compute local velocity using the Poiseuille profile: v(r) = 2 * v_avg * (1 - (r/R)^2)
        v_sample = 2 * self.flow_speed * (1 - (r_sample / self.radius)**2)
        v_max_units = v_sample.max().to('meter/second').to_compact().units
        return x, y, v_sample.to(v_max_units)

    def _add_boundary_to_ax(self, ax: plt.Axes, length_units: Quantity) -> None:
        """
        Adds a visual representation of the circular channel boundary to a 3D Axes object.

        This method draws a circle in the \(xy\)-plane (at \(z=0\)) that represents the boundary
        of the circular flow cell. The circle is defined by the equation
        \[
        x = R \cos(\theta), \quad y = R \sin(\theta), \quad \theta \in [0, 2\pi],
        \]
        where \(R\) is the tube radius (converted to the specified length units). The circle is drawn
        as a green line to delineate the channel boundary.

        Parameters
        ----------
        ax : plt.Axes
            The Matplotlib 3D Axes object on which the boundary will be plotted.
        length_units : Quantity
            The desired length unit (e.g., \texttt{units.meter}) to which the radius will be converted.

        Returns
        -------
        None
            This method adds the boundary plot to the provided Axes object in-place.
        """
        # Convert the radius to the specified units and extract its numerical value
        R_val = self.radius.to(length_units).magnitude

        # Generate points on the circle using polar coordinates
        theta = np.linspace(0, 2 * np.pi, 200)
        x_circle = R_val * np.cos(theta)
        y_circle = R_val * np.sin(theta)
        z_circle = np.zeros_like(x_circle)

        # Plot the circle on the Axes
        ax.plot(x_circle, y_circle, z_circle, color='green', lw=2, label='Channel Boundary (R)')



@dataclass(config=config_dict, kw_only=True)
class RectangularFlowCell(BaseFlowCell):
    """
    Models a rectangular flow cell.

    The velocity profile follows a **bi-parabolic** distribution:
        v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

    where:
        - `w` is the channel width (in meters),
        - `h` is the channel height (in meters),
        - `x` and `y` are coordinates inside the cross-section (-w/2 ≤ x ≤ w/2, -h/2 ≤ y ≤ h/2),
        - `v_max ≈ 1.5 * v_avg` is the maximum velocity at the center,
        - `v_avg = volume_flow / (w * h)` is the average flow speed.

    This model assumes **low Reynolds number laminar flow** inside the flow cell.

    Hydrodynamic focusing is enabled using the `focusing_factor` parameter, where:
        - `focusing_factor = 0` results in **uniform** particle distribution across the area.
        - `focusing_factor = 1` forces **perfect focusing** at the center (`x = y = 0`).

    Attributes:
    -----------
    width : Quantity
        The width of the rectangular channel (in meters).
    height : Quantity
        The height of the rectangular channel (in meters).
    volume_flow : Quantity
        The total volumetric flow rate (in m³/s).
    event_scheme : str
        The event timing scheme, by default 'poisson'.
    focusing_factor : float
        A value between 0 (uniform distribution) and 1 (perfect focusing at the center).
    """
    width: Quantity  # in meters
    height: Quantity  # in meters
    volume_flow: Quantity
    event_scheme: str = 'poisson'
    focusing_factor: float = 1.0  # Default: perfect focusing

    def __post_init__(self):
        self.flow_area = self.width * self.height
        return super().__post_init__()

    def get_velocity_profile(self, num_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes the **bi-parabolic** velocity profile for a rectangular flow cell.

        The velocity distribution is given by:

            v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

        where `x` and `y` represent positions inside the channel cross-section.

        Parameters:
        -----------
        num_points : int, optional
            The number of points along each axis for velocity calculation (default: 50).

        Returns:
        --------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            - `X`: 2D numpy array representing the x-coordinates in the cross-section.
            - `Y`: 2D numpy array representing the y-coordinates in the cross-section.
            - `velocities`: 2D numpy array containing the velocity values at each (x, y) position.
        """
        x = np.linspace(- self.width / 2, + self.width / 2, num_points)
        y = np.linspace(- self.height / 2, + self.height / 2, num_points)
        X, Y = np.meshgrid(x, y)
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg
        velocities = v_max * (1 - (2 * X / self.width) ** 2) * (1 - (2 * Y / self.height) ** 2)
        return X, Y, velocities.to(units.meter / units.second)

    def sample_velocity(self, n_samples: int) -> Quantity:
        """
        Samples a velocity for a particle in a **rectangular flow cell**, with optional hydrodynamic focusing.

        **Standard Uniform Sampling:**
        - If `focusing_factor = 0`, particles are **uniformly** distributed over the area.
        - The **(x, y) positions** are drawn from a uniform distribution:
            x ~ U(-w/2, w/2),  y ~ U(-h/2, h/2).

        **Hydrodynamic Focusing:**
        - As `focusing_factor → 1`, particles are increasingly concentrated toward (x, y) = (0, 0).
        - We modify the sampling using an exponential scaling:
            x_sample = w/2 * (1 - focusing_factor) * sign(U) * |U|^focusing_factor
            y_sample = h/2 * (1 - focusing_factor) * sign(V) * |V|^focusing_factor
          where U, V ~ U(-1, 1) (uniform random variables).

        **Velocity Calculation:**
        - The velocity at (x, y) is computed using:
            v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

        Parameters:
        -----------
        n_samples : int, optional
            Number of velocity samples to generate (default: 1).

        Returns:
        --------
        Quantity
            A Quantity representing the sampled velocities in meters per second.
        """
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg  # Max velocity in center

        # Generate uniform random variables U, V in [-1, 1]
        U = np.random.uniform(-1, 1, size=n_samples)
        V = np.random.uniform(-1, 1, size=n_samples)

        # Apply hydrodynamic focusing transformation
        x_sample = (self.width / 2) * (1 - self.focusing_factor) * np.sign(U) * np.abs(U) ** self.focusing_factor
        y_sample = (self.height / 2) * (1 - self.focusing_factor) * np.sign(V) * np.abs(V) ** self.focusing_factor

        # Compute velocity at sampled positions
        v_sample = v_max * (1 - (2 * x_sample / self.width) ** 2) * (1 - (2 * y_sample / self.height) ** 2)

        return v_sample

    def sample_parameters(self, n_samples: int) -> Quantity:
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg  # Max velocity in center

        # Generate uniform random variables U, V in [-1, 1]
        U = np.random.uniform(-1, 1, size=n_samples)
        V = np.random.uniform(-1, 1, size=n_samples)

        # Apply hydrodynamic focusing transformation
        x_sample = (self.width / 2) * (1 - self.focusing_factor) * np.sign(U) * np.abs(U) ** self.focusing_factor
        y_sample = (self.height / 2) * (1 - self.focusing_factor) * np.sign(V) * np.abs(V) ** self.focusing_factor

        # Compute velocity at sampled positions
        v_sample = v_max * (1 - (2 * x_sample / self.width) ** 2) * (1 - (2 * y_sample / self.height) ** 2)
        v_max_units = v_sample.max().to('meter/second').to_compact().units
        return x_sample, y_sample, v_sample.to(v_max_units)

    def _add_boundary_to_ax(self, ax: plt.Axes, length_units: Quantity) -> None:
        """
        Adds a visual representation of the rectangular channel boundary to a 3D Axes object.

        This method plots the boundary of a rectangular flow cell as a green line on the provided
        Matplotlib Axes object. The boundary is defined by the four corners of the rectangle, calculated
        using the cell's width \(w\) and height \(h\). Specifically, the rectangle's corners are:

        \[
        \left(-\frac{w}{2}, -\frac{h}{2}\right), \quad \left(-\frac{w}{2}, \frac{h}{2}\right), \quad
        \left(\frac{w}{2}, \frac{h}{2}\right), \quad \left(\frac{w}{2}, -\frac{h}{2}\right), \quad
        \left(-\frac{w}{2}, -\frac{h}{2}\right)
        \]

        The width and height are converted to the specified `length_units` before plotting. The resulting line is
        drawn at \(z = 0\) (i.e., in the channel cross-section).

        Parameters
        ----------
        ax : plt.Axes
            The Matplotlib 3D Axes object on which the channel boundary will be plotted.
        length_units : Quantity
            The desired length unit (e.g., `units.meter`) for converting the width and height values.

        Returns
        -------
        None
            This method directly adds the boundary plot to the provided Axes object without returning a value.
        """
        # Plot the rectangular channel boundary. The rectangle has corners at:
        # (-w/2, -h/2), (-w/2, h/2), (w/2, h/2), (w/2, -h/2), and back to (-w/2, -h/2).
        w_val = self.width.to(length_units).magnitude
        h_val = self.height.to(length_units).magnitude
        rect_x = [-w_val/2, -w_val/2, w_val/2, w_val/2, -w_val/2]
        rect_y = [-h_val/2, h_val/2, h_val/2, -h_val/2, -h_val/2]
        rect_z = np.zeros_like(rect_x)
        ax.plot(rect_x, rect_y, rect_z, color='green', lw=2, label='Channel Boundary')



@dataclass(config=config_dict)
class SquareFlowCell(RectangularFlowCell):
    """
    Models a square flow cell, which is a special case of a rectangular flow cell where:
        width = height = side

    The velocity profile follows a bi-parabolic distribution:

        v(x, y) = v_max * (1 - (2x / side)^2) * (1 - (2y / side)^2)

    where:
      - side is the side length of the square channel (in meters),
      - x and y are coordinates in the channel cross-section (-side/2 ≤ x, y ≤ side/2),
      - v_max ≈ 1.5 * v_avg is the maximum velocity at the center,
      - v_avg = volume_flow / (side^2) is the average flow speed.

    Hydrodynamic focusing is enabled using the focusing_factor parameter, where:
      - focusing_factor = 0 produces a uniform distribution,
      - focusing_factor = 1 forces perfect focusing at the center.

    Attributes
    ----------
    side : Quantity
        The side length of the square channel (in meters).
    volume_flow : Quantity
        The total volumetric flow rate (in m³/s).
    event_scheme : str
        The event timing scheme, by default 'poisson'.
    focusing_factor : float
        A value between 0 (uniform distribution) and 1 (perfect focusing at the center).
    """
    side: Quantity  # in meters
    # Override inherited width and height so that they are not required during initialization.
    width: Quantity = field(init=False)
    height: Quantity = field(init=False)

    def __post_init__(self):
        """
        Initializes the square flow cell by setting width and height equal to the provided side,
        computing the flow area as side^2, and then invoking the parent class initializer.
        """
        self.width = self.side
        self.height = self.side
        self.flow_area = self.side * self.side
        return super().__post_init__()
