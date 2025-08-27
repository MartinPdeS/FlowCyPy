# from FlowCyPy import units
from TypedUnit import ureg

from FlowCyPy import distribution
from FlowCyPy.population import Sphere


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
        return Sphere(
            particle_count=particle_count,
            name=self._name,
            diameter=self._diameter_distribution,
            refractive_index=self._ri_distribution,
        )


# Define populations
_populations = (
    ("Exosome", 70 * ureg.nanometer, 20, 1.39 * ureg.RIU, 0.02 * ureg.RIU),
    ("MicroVesicle", 400 * ureg.nanometer, 15, 1.39 * ureg.RIU, 0.02 * ureg.RIU),
    ("ApoptoticBodies", 2 * ureg.micrometer, 12, 1.40 * ureg.RIU, 0.03 * ureg.RIU),
    ("HDL", 10 * ureg.nanometer, 35, 1.33 * ureg.RIU, 0.01 * ureg.RIU),
    ("LDL", 20 * ureg.nanometer, 30, 1.35 * ureg.RIU, 0.02 * ureg.RIU),
    ("VLDL", 50 * ureg.nanometer, 20, 1.445 * ureg.RIU, 0.0005 * ureg.RIU),
    ("Platelet", 2000 * ureg.nanometer, 25, 1.38 * ureg.RIU, 0.01 * ureg.RIU),
    ("CellularDebris", 3 * ureg.micrometer, 10, 1.40 * ureg.RIU, 0.03 * ureg.RIU),
)

# Dynamically create population classes
for name, diameter, diameter_spread, ri, ri_spread in _populations:
    diameter_distribution = distribution.RosinRammler(
        characteristic_property=diameter, spread=diameter_spread
    )

    ri_distribution = distribution.Normal(mean=ri, std_dev=ri_spread)

    # Create a class dynamically for each population
    cls = type(name, (CallablePopulation,), {})
    globals()[name] = cls(name, diameter_distribution, ri_distribution)


# Helper function for microbeads
def get_microbeads(
    diameter: ureg.Quantity, refractive_index: ureg.Quantity, name: str
) -> Sphere:
    diameter_distribution = distribution.Delta(position=diameter)
    ri_distribution = distribution.Delta(position=refractive_index)

    microbeads = Sphere(
        name=name, diameter=diameter_distribution, refractive_index=ri_distribution
    )

    return microbeads
