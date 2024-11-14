
import numpy as np
from FlowCyPy import Scatterer, Detector
from FlowCyPy.source import BaseBeam
from FlowCyPy.units import meter


def compute_scattering_cross_section(scatterer: Scatterer, source: BaseBeam, detector: Detector) -> np.ndarray:
    r"""
    Computes the Rayleigh scattering cross-section for a spherical particle with angle dependency.

    The Rayleigh scattering cross-section depends on the angle at which the scattered light is observed.
    The total scattering cross-section is modified by a factor of :math:`\sin^2(\theta)`, where :math:`\theta`
    is the angle between the direction of the incident light and the scattered light, as observed by the detector.

    The Rayleigh scattering cross-section is given by the formula:

    .. math::
        \sigma_s(\theta) = \sigma_0 \sin^2(\theta)

    Where:
        - :math:`\sigma_s(\theta)` is the scattering cross-section at angle :math:`\theta` (in m²),
        - :math:`\sigma_0 = \frac{8 \pi}{3} \left( \frac{2 \pi}{\lambda} \right)^4 \left( \frac{n^2 - 1}{n^2 + 2} \right)^2 r^6` is the total Rayleigh scattering cross-section (in m²),
        - :math:`r` is the radius of the particle (in m),
        - :math:`\lambda` is the wavelength of the incident light (in m),
        - :math:`n` is the refractive index of the scatterer (dimensionless),
        - :math:`\theta` is the angle of observation (in radians).

    Parameters
    ----------
    scatterer : Scatterer
        An instance of `Scatterer` containing the scatterer properties such as size and refractive index.
    source : BaseBeam
        An instance of `BaseBeam` containing the laser properties, including the wavelength.
    detector : Detector
        An instance of `Detector` that contains the angle of observation (`theta_angle` in radians).

    Returns
    -------
    np.ndarray
        The angle-dependent Rayleigh scattering cross-section (in square meters, m²).
    """

    size_list = scatterer.dataframe['Size'].pint.to(meter).values.numpy_data
    ri_list = scatterer.dataframe['RefractiveIndex'].values.numpy_data

    # Extract properties
    wavelength = source.wavelength
    phi = detector.phi_angle  # Angle of observation in radians

    # Rayleigh scattering cross-section formula components
    factor_0 = 8 * np.pi / 3
    factor_1 = (2 * np.pi / wavelength) ** 4

    factor_2 = ((ri_list ** 2 - 1) / (ri_list ** 2 + 2)) ** 2

    # Compute the total Rayleigh scattering cross-section (assuming size in meters)
    sigma_0 = factor_0 * factor_1 * factor_2 * size_list ** 6

    # Modify by the angular dependency: sin^2(theta)
    cross_section = sigma_0 * np.sin(phi * np.pi / 180) ** 2

    return cross_section.magnitude * meter**2


def compute_detected_signal(source: BaseBeam, detector: Detector, scatterer: Scatterer) -> float:
    r"""
    Computes the power detected by a detector from a Rayleigh scattering event.

    The power scattered by a particle is proportional to the power density of the incident light
    and the scattering cross-section of the particle:

    .. math::
        P_s = I_{\text{incident}} \cdot \sigma_s

    The power detected by the detector depends on the solid angle subtended by the detector
    and the total solid angle over which the power is scattered (assumed to be \( 4\pi \) steradians):

    .. math::
        P_{\text{detected}} = P_s \cdot \frac{\Omega}{4 \pi} \cdot \eta

    Where:
    - :math:`P_{\text{detected}}` is the power detected by the detector (in watts, W).
    - :math:`\Omega` is the solid angle subtended by the detector (in steradians, sr).
    - :math:`\eta` is the detector efficiency (dimensionless, between 0 and 1).

    Parameters
    ----------
    source : BaseBeam
        An instance of `BaseBeam` containing the laser properties, including the optical power and numerical aperture.
    detector : Detector
        An instance of `Detector` containing the detector properties, including numerical aperture and responsitivity.

    Returns
    -------
    float
        The power detected by the detector (in watts, W).
    """
    scattering_cross_section = compute_scattering_cross_section(
        source=source,
        scatterer=scatterer,
        detector=detector
    )

    # Calculate incident power density at the beam waist
    incident_power_density = (2 * source.optical_power) / (np.pi * source.waist ** 2)

    # Calculate the scattered power using the scattering cross-section
    scattered_power = incident_power_density * scattering_cross_section

    # Detector captures a portion of scattered power proportional to its solid angle over 4π steradians
    solid_angle = detector.numerical_aperture ** 2
    detected_power = scattered_power * (solid_angle / (4 * np.pi))

    return detected_power
