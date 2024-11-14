import numpy as np
from FlowCyPy import Scatterer, Detector
from FlowCyPy.source import BaseBeam
from PyMieSim.experiment.scatterer import Sphere as PMS_SPHERE
from PyMieSim.experiment.source import PlaneWave
from PyMieSim.experiment.detector import Photodiode as PMS_PHOTODIODE
from PyMieSim.experiment import Setup
from PyMieSim.units import degree, watt, AU


def compute_detected_signal(source: BaseBeam, detector: Detector, scatterer: Scatterer, tolerance: float = 1e-5) -> float:
    """
    Computes the detected signal by analyzing the scattering properties of particles.

    This function uses caching to avoid recomputing values for particle sizes and refractive indices
    that are approximately the same, based on a specified tolerance.

    Parameters
    ----------
    source : BaseBeam
        The light source object containing wavelength, power, and other optical properties.
    detector : Detector
        The detector object containing properties such as numerical aperture and angles.
    scatterer : Scatterer
        The scatterer object containing particle size and refractive index data.
    tolerance : float, optional
        The tolerance for deciding if two values of size and refractive index are "close enough" to be cached.

    Returns
    -------
    np.ndarray
        Array of coupling values for each particle, based on the detected signal.
    """

    size_list = scatterer.dataframe['Size'].values
    ri_list = scatterer.dataframe['RefractiveIndex'].values

    if len(size_list) == 0:
        return np.array([]) * watt

    size_list = size_list.quantity.magnitude * size_list.units
    ri_list = ri_list.quantity.magnitude * ri_list.units

    total_size = ri_list.size
    ONES = np.ones(total_size)

    pms_source = PlaneWave(
        wavelength=ONES * source.wavelength,
        polarization=ONES * 0 * degree,
        amplitude=ONES * source.amplitude
    )

    pms_scatterer = PMS_SPHERE(
        diameter=size_list,
        property=ri_list,
        medium_property=ONES * scatterer.medium_refractive_index,
        source=pms_source
    )

    pms_detector = PMS_PHOTODIODE(
        NA=ONES * detector.numerical_aperture,
        cache_NA=ONES * 0 * AU,
        gamma_offset=ONES * detector.gamma_angle,
        phi_offset=ONES * detector.phi_angle,
        polarization_filter=ONES * np.nan * degree,
        sampling=ONES * detector.sampling
    )

    pms_detector.mode_number = ['NC00'] * total_size
    pms_detector.rotation = ONES * 0 * degree

    pms_detector.__post_init__()

    experiment = Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    coupling_value = experiment.get_sequential('coupling').squeeze() * watt

    return coupling_value
