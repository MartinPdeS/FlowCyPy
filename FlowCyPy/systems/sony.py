"""RosettaX scattering configurations for Sony Biosciences."""

from FlowCyPy.systems._assembly import ScatterChannel, ScatterSystem
from FlowCyPy.units import ureg

id7000_488 = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="FSC",
            numerical_aperture=0.18,
            sampling=700,
            phi_angle=0.0 * ureg.degree,
            cache_numerical_aperture=0.08,
        ),
    ),
)


id7000_405 = ScatterSystem(
    wavelength=405 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)
