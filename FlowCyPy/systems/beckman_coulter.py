"""RosettaX scattering configurations for Beckman Coulter Life Sciences."""

from FlowCyPy.systems._assembly import ScatterChannel, ScatterSystem
from FlowCyPy.units import ureg


cytoflex = ScatterSystem(
    wavelength=405 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.3,
            sampling=1000,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


gallios = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


navios = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.3,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)
