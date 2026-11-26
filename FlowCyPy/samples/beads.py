"""Monodisperse reference beads."""

from FlowCyPy.fluidics.populations import ExplicitModel, SpherePopulation
from FlowCyPy.units import ureg


def microbeads(
    *,
    diameter: ureg.Quantity,
    refractive_index,
    name: str,
    concentration: ureg.Quantity = 1 * ureg.particle / ureg.milliliter,
    medium_refractive_index=1.33,
    sampling_method=None,
    labels=(),
) -> SpherePopulation:
    """Build a population of identical spherical beads.

    Parameters
    ----------
    diameter : length quantity
        Bead diameter.
    refractive_index : float or refractive-index quantity
        Bead refractive index.
    name : str
        Population name used in simulation results.
    concentration : quantity, optional
        Particle count per unit volume.
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
        name=name,
        diameter=diameter,
        refractive_index=refractive_index,
        concentration=concentration,
        medium_refractive_index=medium_refractive_index,
        sampling_method=ExplicitModel() if sampling_method is None else sampling_method,
        labels=labels,
    )
