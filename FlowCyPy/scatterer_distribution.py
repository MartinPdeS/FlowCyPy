from typing import List, Optional, Tuple
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from collections.abc import Iterable
from dataclasses import dataclass
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns
import numpy as np
from FlowCyPy.distribution import BaseDistribution, DeltaDistribution
from FlowCyPy.units import Quantity, meter, refractive_index_unit
from FlowCyPy.flow import FlowCell
from FlowCyPy.utils import array_to_compact
from FlowCyPy.population import Population
from FlowCyPy.joint_plot import JointPlotWithMarginals

@dataclass
class ScattererDistribution:
    """
    Defines and manages the size and refractive index distributions of scatterers (particles)
    passing through a flow cytometer. This class generates random scatterer sizes and refractive
    indices based on a list of provided distributions (e.g., Normal, LogNormal, Uniform, etc.).

    Attributes
    ----------
    flow : object
        The flow setup used to determine the number of particles (n_events).
    refractive_index : Union[float, List[BaseDistribution]]
        A single refractive index or a list of refractive index distributions.
    size : Union[float, List[BaseDistribution]]
        A single particle size or a list of size distributions.
    coupling_factor : str, optional
        The type of coupling factor to use. Options are 'rayleigh' or 'uniform'. Default is 'rayleigh'.
    """

    flow: FlowCell  # Flow object defining flow properties
    populations: List[Population]
    coupling_factor: Optional[str] = 'mie'  # Coupling factor type ('rayleigh', 'uniform')
    medium_refractive_index: List[float | BaseDistribution] = 1.0 # Refractive index or refractive index distributions

    def __post_init__(self) -> None:
        """Initializes particle size, refractive index, and medium refractive index distributions."""

        for population in self.populations:
            population.initialize(flow_cell=self.flow)

        self.size_list = np.concatenate(
            [p.size_list for p in self.populations]
        )

        self.refractive_index_list = np.concatenate(
            [p.refractive_index_list for p in self.populations]
        )

    def plot(self) -> None:
        """
        Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn `jointplot`.

        This method plots the relationship between the scatterer sizes and refractive indices, including both
        their marginal distributions (as Kernel Density Estimates, KDEs) and a scatter plot overlay.

        The `jointplot` displays:
        - **Marginal KDE plots** for scatterer sizes (on the x-axis) and refractive indices (on the y-axis).
        - **Scatter plot** showing the relationship between the sizes and refractive indices.
        - **Joint KDE plot** to highlight the density of points in the scatter plot.

        The marginal and joint KDEs are filled to provide better visualization of density.
        """
        size_common_units = self.populations[0].size_list.units
        ri_common_units = self.populations[0].refractive_index_list.units

        with plt.style.context(mps):
            # Create the jointplot using seaborn
            joint_plot = JointPlotWithMarginals(
                xlabel=f'Scatterer size [{size_common_units}]',
                ylabel=f'Scatterer refractive index'
            )

            for n, population in enumerate(self.populations):
                joint_plot.add_dataset(
                    x=population.size_list.to(size_common_units).magnitude,
                    y=population.refractive_index_list.to(ri_common_units).magnitude,
                    label=population.name,
                    alpha=0.9,
                )

            joint_plot.show_plot()


    def print_properties(self) -> None:
        """
        Prints the core properties of the scatterer distribution and flow cytometer setup using `tabulate`.

        This method includes properties such as the refractive index distribution, mean scatterer size,
        and the number of events. It gathers relevant information from both the flow and scatterer distributions
        to provide a concise summary.
        """
        from tabulate import tabulate

        # Ensure size and refractive indices have been initialized
        if self.size_list is None or self.refractive_index_list is None:
            raise ValueError("Scatterer sizes or refractive indices have not been initialized. Use 'initialize_samples()' first.")

        # Gather flow properties
        print("Flow Properties")
        self.flow.print_properties()  # Assuming `self.flow` has its own `print_properties()` method

        # Compute additional scatterer properties
        mean_size = np.mean(self.size_list).to_compact()  # Mean size in compact units
        mean_refractive_index = np.mean(self.refractive_index_list)

        # Gather scatterer distribution properties
        properties = [
            ["Mean Refractive Index", f"{mean_refractive_index:.2f}"],  # Mean refractive index
            ["Mean Size", f"{mean_size:.2e~P}"],  # Mean size with unit formatting
            ["Number of Events", f"{len(self.size_list)}"],  # Number of scatterer events
            ["Coupling Factor", self.coupling_factor],  # Coupling factor (e.g., 'rayleigh', 'mie')
        ]

        # Print scatterer properties in tabulated format
        print("\nScatterer Properties")
        print(tabulate(properties, headers=["Property", "Value"], tablefmt="grid"))
