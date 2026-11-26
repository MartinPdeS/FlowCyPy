"""Reference sphere populations for cells."""

from FlowCyPy.samples._sphere import SpherePreset
from FlowCyPy.units import ureg

platelet = SpherePreset(
    name="Platelet",
    diameter_scale=2000 * ureg.nanometer,
    diameter_shape=25,
    refractive_index_mean=1.38,
    refractive_index_std=0.01,
)


cellular_debris = SpherePreset(
    name="CellularDebris",
    diameter_scale=3 * ureg.micrometer,
    diameter_shape=10,
    refractive_index_mean=1.4,
    refractive_index_std=0.03,
)
