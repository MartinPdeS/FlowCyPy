from FlowCyPy.units import Quantity, nanometer, RIU, micrometer, particle
from FlowCyPy.population import Population
from FlowCyPy import distribution

class CallablePopulationMeta(type):
    def __getattr__(cls, attr):
        raise AttributeError(f"{cls.__name__} must be called as {cls.__name__}() to access its population instance.")


class CallablePopulation(metaclass=CallablePopulationMeta):
    def __init__(self, name, diameter_dist, ri_dist):
        self._name = name
        self._diameter_distribution = diameter_dist
        self._ri_distribution = ri_dist

    def __call__(self, particle_count: Quantity = 1 * particle):
        return Population(
            particle_count=particle_count,
            name=self._name,
            diameter=self._diameter_distribution,
            refractive_index=self._ri_distribution,
        )


# Define populations
_populations = (
    ('Exosome',          70 * nanometer, 2.0, 1.39 * RIU, 0.02 * RIU),
    ('MicroVesicle',    400 * nanometer, 1.5, 1.39 * RIU, 0.02 * RIU),
    ('ApoptoticBodies',  2 * micrometer, 1.2, 1.40 * RIU, 0.03 * RIU),
    ('HDL',              10 * nanometer, 3.5, 1.33 * RIU, 0.01 * RIU),
    ('LDL',              20 * nanometer, 3.0, 1.35 * RIU, 0.02 * RIU),
    ('VLDL',             50 * nanometer, 2.0, 1.445 * RIU, 0.0005 * RIU),
    ('Platelet',       2000 * nanometer, 2.5, 1.38 * RIU, 0.01 * RIU),
    ('CellularDebris',   3 * micrometer, 1.0, 1.40 * RIU, 0.03 * RIU),
)

# Dynamically create population classes
for (name, diameter, diameter_spread, ri, ri_spread) in _populations:
    diameter_distribution = distribution.RosinRammler(
        characteristic_property=diameter,
        spread=diameter_spread
    )

    ri_distribution = distribution.Normal(
        mean=ri,
        std_dev=ri_spread
    )

    # Create a class dynamically for each population
    cls = type(name, (CallablePopulation,), {})
    globals()[name] = cls(name, diameter_distribution, ri_distribution)


# Helper function for microbeads
def get_microbeads(diameter: Quantity, refractive_index: Quantity, name: str) -> Population:
    diameter_distribution = distribution.Delta(position=diameter)
    ri_distribution = distribution.Delta(position=refractive_index)

    microbeads = Population(
        name=name,
        diameter=diameter_distribution,
        refractive_index=ri_distribution
    )

    return microbeads
