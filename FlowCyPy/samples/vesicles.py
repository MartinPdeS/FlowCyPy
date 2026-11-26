"""Reference sphere populations for vesicles."""

from FlowCyPy.samples._sphere import SpherePreset
from FlowCyPy.units import ureg

exosome = SpherePreset(
    name="Exosome",
    diameter_scale=70 * ureg.nanometer,
    diameter_shape=20,
    refractive_index_mean=1.39,
    refractive_index_std=0.02,
)


microvesicle = SpherePreset(
    name="MicroVesicle",
    diameter_scale=400 * ureg.nanometer,
    diameter_shape=15,
    refractive_index_mean=1.39,
    refractive_index_std=0.02,
)


apoptotic_bodies = SpherePreset(
    name="ApoptoticBodies",
    diameter_scale=2 * ureg.micrometer,
    diameter_shape=12,
    refractive_index_mean=1.4,
    refractive_index_std=0.03,
)
