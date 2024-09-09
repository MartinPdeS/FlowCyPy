from typing import List, Optional, Tuple, Union
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from dataclasses import dataclass
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns
import numpy as np
from FlowCyPy.distribution import BaseDistribution, DeltaDistribution
from FlowCyPy import ureg

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


    flow: object  # Flow object defining flow properties
    refractive_index: Union[float, List[BaseDistribution]]  # Refractive index or refractive index distributions
    size: Union[float, List[BaseDistribution]]  # Particle size or size distributions
    coupling_factor: Optional[str] = 'mie'  # Coupling factor type ('rayleigh', 'uniform')


    def __post_init__(self) -> None:
        """Initializes particle size and refractive index distributions and generates the samples."""
        self.size_list = None  # Placeholder for generated sizes
        self.refractive_index_list = None  # Placeholder for generated refractive indices
        self.initialize_sizes(n_samples=self.flow.n_events)
        self.initialize_refractive_indices(n_samples=self.flow.n_events)


    def initialize_sizes(self, n_samples: int) -> None:
        """
        Generates random scatterer sizes based on the provided size distributions.

        If a single size is provided, it will be treated as a delta distribution (constant value).
        Multiple distributions are combined to generate the final sample list.

        Parameters
        ----------
        n_samples : int
            The number of scatterer sizes to generate.
        """
        # Convert single size value to DeltaDistribution if necessary
        self.size = [
            d if isinstance(d, BaseDistribution) else DeltaDistribution(size_value=d) for d in self.size
        ]

        # Generate sizes from each distribution
        size_list = [d.generate(n_samples) for d in self.size]

        # Concatenate all generated sizes and sample from the combined distribution
        self.size_list = np.concatenate(size_list)

        # Randomly sample the final size list from the combined distribution
        self.size_list = np.random.choice(
            self.size_list.magnitude,
            size=n_samples.magnitude,
            replace=True
        ) * ureg.meter

    def initialize_refractive_indices(self, n_samples: int) -> None:
        """
        Generates random scatterer refractive indices based on the provided refractive index distributions.

        If a single refractive index is provided, it will be treated as a delta distribution (constant value).
        Multiple distributions are combined to generate the final sample list.

        Parameters
        ----------
        n_samples : int
            The number of refractive index samples to generate.
        """
        # Convert single refractive index value to DeltaDistribution if necessary
        self.refractive_index = [
            d if isinstance(d, BaseDistribution) else DeltaDistribution(size_value=d) for d in self.refractive_index
        ]

        # Generate refractive indices from each distribution
        refractive_index_list = [d.generate(n_samples) for d in self.refractive_index]

        # Concatenate all generated refractive indices and sample from the combined distribution
        self.refractive_index_list = np.concatenate(refractive_index_list)

        # Randomly sample the final refractive index list from the combined distribution
        self.refractive_index_list = np.random.choice(
            self.refractive_index_list.magnitude,
            size=n_samples.magnitude,
            replace=True
        ) * ureg.refractive_index_unit


    def get_size_pdf(self, sampling: Optional[int] = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Combines the PDFs of all size distributions, applying their respective scale factors.

        This method calculates the combined probability density function (PDF) for the particle sizes generated
        from all size distributions.

        Parameters
        ----------
        sampling : int, optional
            The number of points to sample for plotting the continuous PDF (default is 1000).

        Returns
        -------
        x : np.ndarray
            The x-values (particle sizes) for the combined PDF.
        pdf : np.ndarray
            The combined PDF values corresponding to the x-values.
        """
        if self.size_list is None:
            raise ValueError("Sizes have not been generated. Use 'initialize_sizes()' first.")

        # Generate x-values for the PDF based on min/max of size_list
        x_min = self.size_list.min().magnitude
        x_max = self.size_list.max().magnitude
        x = np.linspace(x_min, x_max, sampling)

        # Initialize the PDF array with zeros
        pdf = np.zeros_like(x)

        # Combine the PDFs of all size distributions
        for distribution in self.size:
            dist_x, dist_pdf = distribution.get_pdf(x)  # Get the PDF for each distribution
            pdf += dist_pdf  # Sum the PDFs from all distributions

        return x, pdf

    def get_refractive_index_pdf(self, sampling: Optional[int] = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Combines the PDFs of all refractive index distributions, applying their respective scale factors.

        This method calculates the combined probability density function (PDF) for the refractive indices generated
        from all refractive index distributions.

        Parameters
        ----------
        sampling : int, optional
            The number of points to sample for plotting the continuous PDF (default is 1000).

        Returns
        -------
        x : np.ndarray
            The x-values (refractive indices) for the combined PDF.
        pdf : np.ndarray
            The combined PDF values corresponding to the x-values.
        """
        if self.refractive_index_list is None:
            raise ValueError("Refractive indices have not been generated. Use 'initialize_refractive_indices()' first.")

        # Generate x-values for the PDF based on min/max of refractive_index_list
        x_min = self.refractive_index_list.min().magnitude
        x_max = self.refractive_index_list.max().magnitude
        x = np.linspace(x_min, x_max, sampling)

        # Initialize the PDF array with zeros
        pdf = np.zeros_like(x)

        # Combine the PDFs of all refractive index distributions
        for distribution in self.refractive_index:
            dist_x, dist_pdf = distribution.get_pdf(x)  # Get the PDF for each distribution
            pdf += dist_pdf  # Sum the PDFs from all distributions

        return x, pdf

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
        with plt.style.context(mps):
            # Create the jointplot using seaborn
            joint_plot = sns.jointplot(
                x=self.size_list.magnitude,
                y=self.refractive_index_list.magnitude,
                kind='kde',
                cmap='Blues',
                fill=True,
                marginal_kws=dict(fill=True, warn_singular=False),
            )

            joint_plot.figure.set_size_inches((10, 8))

            # Set axis labels for the plot
            joint_plot.set_axis_labels(
                f'Scatterer size [{self.size_list.units}]',
                f'Scatterer refractive index  [{self.refractive_index_list.units}]'
            )

            joint_plot.plot_joint(sns.scatterplot, color='blue', alpha=0.5)

            # Add a title above the plot
            joint_plot.figure.suptitle('2D Density Plot of scatterer properties', fontsize=14)

            if len(joint_plot.ax_joint.collections) == 2:
                # Create a divider for the axis to place the colorbar at the bottom
                divider = make_axes_locatable(joint_plot.ax_joint)
                cax = divider.append_axes("bottom", size="5%", pad=0.5)

                # Add a horizontal colorbar at the bottom
                plt.colorbar(
                    joint_plot.ax_joint.collections[0],
                    cax=cax,
                    orientation="horizontal",
                    label='Density',
                )

            plt.tight_layout()

            plt.show()

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
