from FlowCyPy.units import Quantity, nanometer, RIU, micrometer
from FlowCyPy.population import Population
from FlowCyPy import distribution

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


for (name, size, size_spread, ri, ri_spread) in _populations:
    size_distribution = distribution.RosinRammler(
        characteristic_size=size,
        spread=size_spread
    )

    ri_distribution = distribution.Normal(
        mean=ri,
        std_dev=ri_spread
    )

    population = Population(
        name=name,
        size=size_distribution,
        refractive_index=ri_distribution,
    )

    locals()[name] = population


def get_microbeads(size: Quantity, refractive_index: Quantity, name: str) -> Population:

    size_distribution = distribution.Delta(position=size)

    ri_distribution = distribution.Delta(position=refractive_index)

    microbeads = Population(
        name=name,
        size=size_distribution,
        refractive_index=ri_distribution
    )

    return microbeads
