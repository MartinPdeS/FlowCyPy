import numpy as np
from FlowCyPy import ScattererDistribution, Detector, Source
from FlowCyPy import ureg
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import Gaussian
from PyMieSim.experiment.detector import Photodiode
from PyMieSim.experiment import measure, Setup


def compute_detected_signal(
        source: Source,
        detector: Detector,
        scatterer_distribution: ScattererDistribution) -> float:
    """
    Empirical model for scattering intensity based on particle size, granularity, and detector angle.

    This function models forward scatter (FSC) as proportional to the particle's size squared and
    side scatter (SSC) as proportional to the granularity and modulated by angular dependence
    (sin^n(phi)). Granularity is a dimensionless measure of the particle's internal complexity or
    surface irregularities:

    - A default value of 1.0 is used for moderate granularity (e.g., typical white blood cells).
    - Granularity values < 1.0 represent smoother particles with less internal complexity (e.g., bacteria).
    - Granularity values > 1.0 represent particles with higher internal complexity or surface irregularities (e.g., granulocytes).

    Parameters
    ----------
    detector : Detector
        The detector object containing phitheta_angle (in radians).
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
    pms_source = Gaussian(
        wavelength=source.wavelength.magnitude,
        polarization=0,
        optical_power=source.optical_power.magnitude,
        NA=source.NA
    )

    pms_scatterer = Sphere(
        diameter=scatterer_distribution.size_list.magnitude,
        index=scatterer_distribution.refractive_index_list.magnitude,
        medium_index=1.0,
        source=pms_source
    )

    pms_detector = Photodiode(
        NA=detector.NA,
        gamma_offset=0,
        phi_offset=detector.theta_angle,
        polarization_filter=None,
        sampling=100
    )

    experiment = Setup(
        source=pms_source,
        scatterer=pms_scatterer,
        detector=pms_detector
    )

    coupling = experiment.get(measure=measure.coupling, export_as_numpy=True).squeeze()

    coupling = np.diagonal(coupling)

    return coupling.ravel() * detector.responsitivity * ureg.watt
