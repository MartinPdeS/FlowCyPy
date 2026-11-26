"""RosettaX scattering configurations for nanoFCM."""

from FlowCyPy.systems._assembly import ScatterChannel, ScatterSystem
from FlowCyPy.units import ureg

nanoanalyzer = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=0.85,
            sampling=1000,
            phi_angle=90.0 * ureg.degree,
        ),
        ScatterChannel(
            name="FSC",
            numerical_aperture=0.14,
            sampling=800,
            phi_angle=0.0 * ureg.degree,
            cache_numerical_aperture=0.06,
        ),
    ),
)
