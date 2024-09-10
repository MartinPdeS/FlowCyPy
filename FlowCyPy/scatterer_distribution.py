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
    refractive_index: List[float | BaseDistribution]  # Refractive index or refractive index distributions
    size: List[float | BaseDistribution]  # Particle size or size distributions
    coupling_factor: Optional[str] = 'mie'  # Coupling factor type ('rayleigh', 'uniform')
    medium_refractive_index: List[float | BaseDistribution] = 1.0 # Refractive index or refractive index distributions

    def __post_init__(self) -> None:
        """Initializes particle size, refractive index, and medium refractive index distributions."""
        self.size_list, self.size_dist = self._initialize_distribution(
            distributions=self.size,
            unit=meter
        )

        self.refractive_index_list, self.refractive_index_dist = self._initialize_distribution(
            distributions=self.refractive_index,
            unit=refractive_index_unit
        )

        self.medium_refractive_index_list, self.medium_refractive_index_dist = self._initialize_distribution(
            distributions=self.medium_refractive_index,
            unit=refractive_index_unit
        )

    def _initialize_distribution(self, distributions: List[float | BaseDistribution], unit) -> Quantity:
        """
        General method to initialize a distribution (sizes, refractive indices, etc.) based on the provided distributions.

        Parameters
        ----------
        distributions : List[float | BaseDistribution]
            List of values or distribution objects.
        n_samples : int
            Number of samples to generate.
        unit : Unit
            The unit associated with the distribution (e.g., meter, refractive_index_unit).

        Returns
        -------
        Quantity
            The generated samples as a Quantity object with the appropriate unit.
        """
        if not isinstance(distributions, Iterable):
            distributions = [distributions]

        # Convert single value inputs to DeltaDistribution if necessary
        distributions = [
            d if isinstance(d, BaseDistribution) else DeltaDistribution(size_value=d) for d in distributions
        ]

        # Generate values from each distribution
        value_list = [d.generate(self.flow.n_events) for d in distributions]

        # Concatenate the generated values and sample from the combined distribution
        combined_list = np.concatenate(value_list)

        sampled_values = np.random.choice(
            combined_list,
            size=self.flow.n_events.magnitude,
            replace=True
        )

        return Quantity(sampled_values, unit), distributions

    def get_pdf(self, value_list: Quantity, distributions: List[BaseDistribution], sampling: Optional[int] = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Combines the PDFs of all provided distributions (e.g., sizes or refractive indices) and returns the combined PDF.

        This method generates a combined probability density function (PDF) from a list of distributions (size or refractive index),
        and calculates it over a given number of sample points. The combined PDF is the sum of the PDFs from the individual distributions.

        Parameters
        ----------
        value_list : Quantity
            The list of generated values from the distributions (e.g., size or refractive indices).
            This is expected to have been initialized and contain the generated values.
        distributions : List[BaseDistribution]
            A list of `BaseDistribution` objects, each representing a distribution from which the values were drawn.
            Each distribution must implement the `get_pdf` method to return its own PDF.
        sampling : int, optional
            The number of points to sample for plotting the continuous PDF (default is 1000).
            This controls the resolution of the PDF graph.

        Returns
        -------
        x : np.ndarray
            The x-values for the PDF. These correspond to the sample points used to evaluate the combined PDF
            and represent the range of the generated values (e.g., sizes or refractive indices).
        pdf : np.ndarray
            The combined PDF values corresponding to the x-values. This array contains the sum of the PDFs from
            all the individual distributions and provides the overall probability density function.

        Raises
        ------
        ValueError
            If `value_list` has not been initialized (i.e., is `None`), indicating that the necessary values were
            not generated prior to calling this method.
        """
        if value_list is None:
            raise ValueError("Values have not been generated. Initialize values first.")

        # Generate x-values for the PDF based on min/max of value_list
        x_min = value_list.min().magnitude
        x_max = value_list.max().magnitude
        x = np.linspace(x_min, x_max, sampling)

        # Initialize the PDF array with zeros
        pdf = np.zeros_like(x)

        # Combine the PDFs of all distributions
        for distribution in distributions:
            _, dist_pdf = distribution.get_pdf(x)  # Get the PDF for each distribution
            pdf += dist_pdf  # Sum the PDFs from all distributions

        return x, pdf

    def get_size_pdf(self, sampling: Optional[int] = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates the combined PDF for scatterer sizes.

        This method computes the combined probability density function (PDF) for particle sizes using the size distributions
        that were initialized earlier. The PDF provides insight into the likelihood of different particle sizes based on the
        defined distributions.

        Parameters
        ----------
        sampling : int, optional
            The number of points to sample for plotting the continuous PDF (default is 1000).
            A higher number provides more precision but takes longer to compute.

        Returns
        -------
        x : np.ndarray
            The x-values for the size PDF. These correspond to particle sizes and range from the minimum to the maximum
            of the generated size values.
        pdf : np.ndarray
            The combined PDF values corresponding to the x-values. This array contains the probability density function
            for the particle sizes, combining all the individual size distributions.
        """
        return self.get_pdf(
            value_list=self.size_list,
            distributions=self.size_dist,
            sampling=sampling
        )

    def get_refractive_index_pdf(self, sampling: Optional[int] = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates the combined PDF for scatterer refractive indices.

        This method computes the combined probability density function (PDF) for particle refractive indices based on the
        initialized refractive index distributions. The PDF shows the likelihood of different refractive indices in the sample
        of scatterers.

        Parameters
        ----------
        sampling : int, optional
            The number of points to sample for plotting the continuous PDF (default is 1000).
            A higher number provides more precision but takes longer to compute.

        Returns
        -------
        x : np.ndarray
            The x-values for the refractive index PDF. These correspond to refractive indices and range from the minimum
            to the maximum of the generated refractive index values.
        pdf : np.ndarray
            The combined PDF values corresponding to the x-values. This array contains the probability density function
            for the particle refractive indices, combining all the individual refractive index distributions.
        """
        return self.get_pdf(
            value_list=self.refractive_index_list,
            distributions=self.refractive_index_dist,
            sampling=sampling
        )

    def get_medium_refractive_index_pdf(self, sampling: Optional[int] = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates the combined PDF for the medium refractive indices.

        This method computes the combined probability density function (PDF) for medium refractive indices, using the
        initialized medium refractive index distributions. The PDF indicates the likelihood of different refractive indices
        for the medium in which scatterers are located.

        Parameters
        ----------
        sampling : int, optional
            The number of points to sample for plotting the continuous PDF (default is 1000).
            A higher number provides more precision but takes longer to compute.

        Returns
        -------
        x : np.ndarray
            The x-values for the medium refractive index PDF. These correspond to refractive indices for the medium and range
            from the minimum to the maximum of the generated medium refractive index values.
        pdf : np.ndarray
            The combined PDF values corresponding to the x-values. This array contains the probability density function
            for the medium refractive indices, combining all the individual medium refractive index distributions.
        """
        return self.get_pdf(
            value_list=self.medium_refractive_index_list,
            distributions=self.medium_refractive_index_dist,
            sampling=sampling
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
