
from FlowCyPy import units
from FlowCyPy.detector import Detector
from FlowCyPy.population import Sphere
from FlowCyPy import distribution


class PMT():
    def __new__(cls,
        name: str,
        phi_angle: units.Quantity,
        numerical_aperture: units.Quantity,
        responsivity: units.Quantity = units.Quantity(0.2, units.ampere / units.watt),
        dark_current: units.Quantity = units.Quantity(1e-9, units.ampere),
        **kwargs):

        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )

# Predefined PIN Photodiode Detector
class PIN():
    def __new__(cls,
        name: str,
        phi_angle: units.Quantity,
        numerical_aperture: units.Quantity,
        responsivity=units.Quantity(0.5, units.ampere / units.watt),  # Higher responsivity for PIN
        dark_current=units.Quantity(1e-8, units.ampere),               # Slightly higher dark current
        **kwargs):

        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )


# Predefined Avalanche Photodiode (APD) Detector
class APD():
    def __new__(cls,
        name: str,
        phi_angle: units.Quantity,
        numerical_aperture: units.Quantity,
        responsivity=units.Quantity(0.7, units.ampere / units.watt),  # APDs often have high responsivity
        dark_current=units.Quantity(5e-9, units.ampere),
        **kwargs):

        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )


class CallablePopulationMeta(type):
    def __getattr__(cls, attr):
        raise AttributeError(f"{cls.__name__} must be called as {cls.__name__}() to access its population instance.")


class CallablePopulation(metaclass=CallablePopulationMeta):
    def __init__(self, name, diameter_dist, ri_dist):
        self._name = name
        self._diameter_distribution = diameter_dist
        self._ri_distribution = ri_dist

    def __call__(self, particle_count: units.Quantity = 1 * units.particle):
        return Sphere(
            particle_count=particle_count,
            name=self._name,
            diameter=self._diameter_distribution,
            refractive_index=self._ri_distribution,
        )


# Define populations
_populations = (
    ('Exosome',          70 * units.nanometer, 2.0, 1.39 * units.RIU, 0.02 * units.RIU),
    ('MicroVesicle',    400 * units.nanometer, 1.5, 1.39 * units.RIU, 0.02 * units.RIU),
    ('ApoptoticBodies',  2 * units.micrometer, 1.2, 1.40 * units.RIU, 0.03 * units.RIU),
    ('HDL',              10 * units.nanometer, 3.5, 1.33 * units.RIU, 0.01 * units.RIU),
    ('LDL',              20 * units.nanometer, 3.0, 1.35 * units.RIU, 0.02 * units.RIU),
    ('VLDL',             50 * units.nanometer, 2.0, 1.445 * units.RIU, 0.0005 * units.RIU),
    ('Platelet',       2000 * units.nanometer, 2.5, 1.38 * units.RIU, 0.01 * units.RIU),
    ('CellularDebris',   3 * units.micrometer, 1.0, 1.40 * units.RIU, 0.03 * units.RIU),
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
def get_microbeads(diameter: units.Quantity, refractive_index: units.Quantity, name: str) -> Sphere:
    diameter_distribution = distribution.Delta(position=diameter)
    ri_distribution = distribution.Delta(position=refractive_index)

    microbeads = Sphere(
        name=name,
        diameter=diameter_distribution,
        refractive_index=ri_distribution
    )

    return microbeads
