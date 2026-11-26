"""Reference sphere populations for lipoproteins."""

from FlowCyPy.samples._sphere import SpherePreset
from FlowCyPy.units import ureg

hdl = SpherePreset(
    name="HDL",
    diameter_scale=10 * ureg.nanometer,
    diameter_shape=35,
    refractive_index_mean=1.33,
    refractive_index_std=0.01,
)


ldl = SpherePreset(
    name="LDL",
    diameter_scale=20 * ureg.nanometer,
    diameter_shape=30,
    refractive_index_mean=1.35,
    refractive_index_std=0.02,
)


vldl = SpherePreset(
    name="VLDL",
    diameter_scale=50 * ureg.nanometer,
    diameter_shape=20,
    refractive_index_mean=1.445,
    refractive_index_std=0.0005,
)
