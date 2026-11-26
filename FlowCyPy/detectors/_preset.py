"""Reference electrical settings shared by detector channel factories."""

from dataclasses import dataclass
from FlowCyPy.opto_electronics.detector import Detector
from FlowCyPy.units import ureg


@dataclass(frozen=True, kw_only=True)
class DetectorPreset:
    """Build detector channels from a common set of electrical defaults.

    Parameters
    ----------
    responsivity : quantity
        Photocurrent per unit optical power, in A/W.
    dark_current : quantity
        Mean dark current, in A.
    current_noise_density : quantity, optional
        Current noise amplitude density, in A/√Hz. Defaults to zero.
    """

    responsivity: ureg.Quantity
    dark_current: ureg.Quantity
    current_noise_density: ureg.Quantity = 0 * ureg.ampere / ureg.hertz**0.5

    def __call__(
        self,
        *,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: float,
        **detector_options,
    ) -> Detector:
        """Create a fresh detector with the requested geometry.

        Parameters
        ----------
        name : str
            Channel name used in the acquisition.
        phi_angle : angle quantity
            Angular position of the detector.
        numerical_aperture : float
            Dimensionless outer collection aperture.
        **detector_options
            Additional Detector keywords, including signals, optical_filter,
            bandwidth, and overrides for the preset's electrical settings.

        Returns
        -------
        Detector
            Configured detector channel.
        """
        settings = {
            "responsivity": self.responsivity,
            "dark_current": self.dark_current,
            "current_noise_density": self.current_noise_density,
        }
        settings.update(detector_options)
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            **settings,
        )
