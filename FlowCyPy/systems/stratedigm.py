"""RosettaX scattering configurations for Stratedigm."""

from FlowCyPy.systems._assembly import ScatterChannel, ScatterSystem
from FlowCyPy.units import ureg

s1313ex = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=800,
            phi_angle=90.0 * ureg.degree,
        ),
        ScatterChannel(
            name="FSC",
            numerical_aperture=0.185518,
            sampling=800,
            phi_angle=0.0 * ureg.degree,
            cache_numerical_aperture=0.023264,
        ),
    ),
)


s1000ex = ScatterSystem(
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
