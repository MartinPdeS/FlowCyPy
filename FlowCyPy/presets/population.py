from TypedUnit import ureg

from FlowCyPy.fluidics import distributions
from FlowCyPy.fluidics.populations import SpherePopulation


class CallablePopulationMeta(type):
    def __getattr__(cls, attr):
        raise AttributeError(
            f"{cls.__name__} must be called as {cls.__name__}() to access its population instance."
        )


class CallablePopulation(metaclass=CallablePopulationMeta):
    def __init__(self, name, diameter_dist, ri_dist):
        self._name = name
        self._diameter_distribution = diameter_dist
        self._ri_distribution = ri_dist

    def __call__(self, particle_count: ureg.Quantity = 1 * ureg.particle):
        return SpherePopulation(
            particle_count=particle_count,
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
    diameter: ureg.Quantity, refractive_index: ureg.Quantity, name: str
) -> SpherePopulation:
    diameter_distribution = distributions.Delta(position=diameter)
    ri_distribution = distributions.Delta(position=refractive_index)

    microbeads = SpherePopulation(
        name=name, diameter=diameter_distribution, refractive_index=ri_distribution
    )

    return microbeads
