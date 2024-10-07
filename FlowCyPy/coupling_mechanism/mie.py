import numpy as np
from FlowCyPy import Scatterer, Detector, Source
from FlowCyPy import ureg
from PyMieSim.single.scatterer import Sphere as PMS_SPHERE
from PyMieSim.single.source import Gaussian as PMS_GAUSSIAN
from PyMieSim.single.detector import Photodiode as PMS_PHOTODIODE
from FlowCyPy.units import meter, watt, degree

# Initialize a cache (dictionary) to store computed results for (size, ri) pairs
_cache = {}

def cache_key(size, ri, detector, tolerance: float = 0):
    """
    Generates a cache key based on size and refractive index, rounding based on a tolerance.

    Parameters
    ----------
    size : float
        The particle size (in meters).
    ri : float
        The refractive index of the particle.
    tolerance : float, optional
        The tolerance for determining if two values are close enough to be considered identical.

    Returns
    -------
    tuple
        A tuple representing the cached key based on size and refractive index.
    """
    if tolerance == 0:
        return (size, detector, ri)
    # Round size and ri to the specified tolerance
    size_rounded = np.round(size / tolerance) * tolerance
    ri_rounded = np.round(ri / tolerance) * tolerance
    return (size_rounded, detector, ri_rounded)

def compute_detected_signal(source: Source, detector: Detector, scatterer: Scatterer, tolerance: float = 1e-5) -> float:
    """
    Computes the detected signal by analyzing the scattering properties of particles.

    This function uses caching to avoid recomputing values for particle sizes and refractive indices
    that are approximately the same, based on a specified tolerance.

    Parameters
    ----------
    source : Source
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
    from PyMieSim.units import degree, AU
    pms_source = PMS_GAUSSIAN(
        wavelength=source.wavelength,
        polarization=0 * degree,
        optical_power=source.optical_power,
        NA=source.numerical_aperture
    )

    size_list = scatterer.dataframe['Size']
    ri_list = scatterer.dataframe['RefractiveIndex']
    couplings = np.empty_like(size_list).astype(float)

    for index, (size, ri) in enumerate(zip(size_list, ri_list)):
        # Generate a cache key based on the size and refractive index, using tolerance
        cache_key_ = cache_key(size, ri, detector, tolerance)

        # Check if the result for this key is already cached
        if cache_key_ in _cache:
            couplings[index] = _cache[cache_key_]
        else:
            # If not cached, compute the scattering and store it in the cache
            pms_scatterer = PMS_SPHERE(
                diameter=size,
                property=ri,
                medium_property=scatterer.medium_refractive_index,
                source=pms_source
            )

            pms_detector = PMS_PHOTODIODE(
                NA=detector.numerical_aperture,
                gamma_offset=detector.gamma_angle,
                phi_offset=detector.phi_angle,
                polarization_filter=None,
                sampling=detector.sampling
            )

            # Compute the coupling
            coupling_value = pms_detector.coupling(pms_scatterer)

            # Store in the cache
            _cache[cache_key_] = coupling_value
            couplings[index] = coupling_value

    return couplings * ureg.watt
