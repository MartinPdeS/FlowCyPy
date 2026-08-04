from TypedUnit import ureg

from FlowCyPy.fluidics import distributions
from FlowCyPy.fluidics.populations import SpherePopulation


class CallablePopulationMeta(type):
    """Metaclass used to make preset populations callable but not class-like."""

    def __getattr__(cls, attr):
        """Raise a clearer error when preset populations are accessed as classes."""
        raise AttributeError(
            f"{cls.__name__} must be called as {cls.__name__}() to access its population instance."
        )


class CallablePopulation(metaclass=CallablePopulationMeta):
    def __init__(self, name, diameter_dist, ri_dist):
        """Store the preset metadata used to build a population instance."""
        self._name = name
        self._diameter_distribution = diameter_dist
        self._ri_distribution = ri_dist

    def __call__(
        self,
        concentration: ureg.Quantity = 1 * ureg.particle / ureg.milliliter,
    ):
        """Instantiate the preset as a :class:`SpherePopulation`.

        Parameters
        ----------
        concentration : ureg.Quantity, optional
            Particle concentration assigned to the created population.

        Returns
        -------
        SpherePopulation
            Population instance configured with the preset distributions.
        """
        return SpherePopulation(
            concentration=concentration,
            name=self._name,
            diameter=self._diameter_distribution,
            refractive_index=self._ri_distribution,
            medium_refractive_index=1.33,
        )


# Define populations
_populations = (
    ("Exosome", 70 * ureg.nanometer, 20, 1.39, 0.02),
    ("MicroVesicle", 400 * ureg.nanometer, 15, 1.39, 0.02),
    ("ApoptoticBodies", 2 * ureg.micrometer, 12, 1.40, 0.03),
    ("HDL", 10 * ureg.nanometer, 35, 1.33, 0.01),
    ("LDL", 20 * ureg.nanometer, 30, 1.35, 0.02),
    ("VLDL", 50 * ureg.nanometer, 20, 1.445, 0.0005),
    ("Platelet", 2000 * ureg.nanometer, 25, 1.38, 0.01),
    ("CellularDebris", 3 * ureg.micrometer, 10, 1.40, 0.03),
)

# Dynamically create population classes
for name, diameter, diameter_spread, ri, ri_spread in _populations:
    diameter_distribution = distributions.RosinRammler(
        scale=diameter, shape=diameter_spread
    )

    ri_distribution = distributions.Normal(mean=ri, standard_deviation=ri_spread)

    # Create a class dynamically for each population
    cls = type(name, (CallablePopulation,), {})
    globals()[name] = cls(name, diameter_distribution, ri_distribution)


# Helper function for microbeads
def get_microbeads(
    diameter: ureg.Quantity,
    refractive_index: ureg.Quantity,
    name: str,
    concentration: ureg.Quantity = 1 * ureg.particle / ureg.milliliter,
) -> SpherePopulation:
    """Create a monodisperse microbead population.

    Parameters
    ----------
    diameter : ureg.Quantity
        Bead diameter used for a delta distribution.
    refractive_index : ureg.Quantity
        Bead refractive index used for a delta distribution.
    name : str
        Population name.
    concentration : ureg.Quantity, optional
        Particle concentration, by default 1 particle / milliliter.

    Returns
    -------
    SpherePopulation
        Population with fixed diameter and refractive index.
    """
    diameter_distribution = distributions.Delta(value=diameter)
    ri_distribution = distributions.Delta(value=refractive_index)

    microbeads = SpherePopulation(
        name=name,
        concentration=concentration,
        medium_refractive_index=distributions.Delta(value=1.33),
        diameter=diameter_distribution,
        refractive_index=ri_distribution,
    )

    return microbeads
