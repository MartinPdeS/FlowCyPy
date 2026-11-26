"""Shared definition for populations with a distributed sphere diameter."""

from dataclasses import dataclass
from FlowCyPy.fluidics import distributions
from FlowCyPy.fluidics.populations import ExplicitModel, SpherePopulation
from FlowCyPy.units import ureg


@dataclass(frozen=True, kw_only=True)
class SpherePreset:
    """Build independent spherical populations from a reference parameter set.

    Parameters
    ----------
    name : str
        Default population name in simulation results.
    diameter_scale : length quantity
        Scale of the Rosin-Rammler diameter distribution.
    diameter_shape : float
        Dimensionless shape of the diameter distribution.
    refractive_index_mean, refractive_index_std : float
        Mean and standard deviation of the normal refractive-index distribution.
    """

    name: str
    diameter_scale: ureg.Quantity
    diameter_shape: float
    refractive_index_mean: float
    refractive_index_std: float

    def __call__(
        self,
        concentration: ureg.Quantity = 1 * ureg.particle / ureg.milliliter,
        *,
        name: str | None = None,
        medium_refractive_index=1.33,
        sampling_method=None,
        labels=(),
    ) -> SpherePopulation:
        """Create a population with fresh diameter and refractive-index samplers.

        Parameters
        ----------
        concentration : quantity, optional
            Particle count per unit volume.
        name : str, optional
            Override the preset name for this population.
        medium_refractive_index : float or distribution, optional
            Refractive index of the suspending medium.
        sampling_method : BaseSamplingMethod, optional
            Particle sampling strategy. Defaults to explicit event sampling.
        labels : sequence of Label, optional
            Fluorescent labels for explicit sampling.

        Returns
        -------
        SpherePopulation
            Population ready to add to a scatterer collection.
        """
        return SpherePopulation(
            name=self.name if name is None else name,
            concentration=concentration,
            diameter=distributions.RosinRammler(
                scale=self.diameter_scale, shape=self.diameter_shape
            ),
            refractive_index=distributions.Normal(
                mean=self.refractive_index_mean,
                standard_deviation=self.refractive_index_std,
            ),
            medium_refractive_index=medium_refractive_index,
            sampling_method=ExplicitModel()
            if sampling_method is None
            else sampling_method,
            labels=labels,
        )
