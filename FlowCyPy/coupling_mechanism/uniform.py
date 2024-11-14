import numpy as np
from FlowCyPy import Scatterer, Detector, ureg
from FlowCyPy.source import BaseBeam


def compute_detected_signal(source: BaseBeam, detector: Detector, scatterer: Scatterer) -> np.ndarray:
    r"""
    Computes the power detected by a detector from a uniform distribution.

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
    return np.ones(len(scatterer.dataframe)) * ureg.watt
