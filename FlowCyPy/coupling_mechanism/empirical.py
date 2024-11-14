import numpy as np
from FlowCyPy import Scatterer, Detector
from FlowCyPy.source import BaseBeam
from FlowCyPy.units import watt, meter


def compute_detected_signal(source: BaseBeam, detector: Detector, scatterer: Scatterer, granularity: float = 1.0, A: float = 1.5, n: float = 2.0) -> float:
    """
    Empirical model for scattering intensity based on particle size, granularity, and detector angle.

    This function models forward scatter (FSC) as proportional to the particle's size squared and
    side scatter (SSC) as proportional to the granularity and modulated by angular dependence
    (sin^n(theta)). Granularity is a dimensionless measure of the particle's internal complexity or
    surface irregularities:

    - A default value of 1.0 is used for moderate granularity (e.g., typical white blood cells).
    - Granularity values < 1.0 represent smoother particles with less internal complexity (e.g., bacteria).
    - Granularity values > 1.0 represent particles with higher internal complexity or surface irregularities (e.g., granulocytes).

    Parameters
    ----------
    detector : Detector
        The detector object containing theta_angle (in radians).
    particle_size : float
        The size of the particle (in meters).
    granularity : float, optional
        A measure of the particle's internal complexity or surface irregularities (dimensionless).
        Default is 1.0.
    A : float, optional
        Empirical scaling factor for angular dependence. Default is 1.5.
    n : float, optional
        Power of sine function for angular dependence. Default is 2.0.

    Returns
    -------
    float
        The detected scattering intensity for the given particle and detector.
    """
    size_list = scatterer.dataframe['Size'].pint.to(meter).values.numpy_data

    # Forward scatter is proportional to size^2
    fsc_intensity = size_list**2

    # Side scatter is proportional to granularity and modulated by angular dependence
    ssc_intensity = granularity * (1 + A * np.sin(np.radians(detector.phi_angle))**n) * np.ones_like(size_list)

    return fsc_intensity * watt if detector.phi_angle < np.radians(10) else ssc_intensity * watt
