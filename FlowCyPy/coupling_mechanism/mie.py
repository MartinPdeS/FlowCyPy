import numpy as np
from PyMieSim.experiment.detector import CoherentMode
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import Gaussian, PlaneWave
from PyMieSim import units
from PyMieSim.experiment import Setup
from FlowCyPy import Detector
from FlowCyPy.source import BaseBeam
from PyMieSim.units import Quantity, degree, watt, AU, hertz
from FlowCyPy.noises import NoiseSetting
import pandas as pd



def apply_rin_noise(source: BaseBeam, total_size: int, bandwidth: float) -> np.ndarray:
    r"""
    Applies Relative Intensity Noise (RIN) to the source amplitude if enabled, accounting for detection bandwidth.

    Parameters
    ----------
    source : BaseBeam
        The light source containing amplitude and RIN information.
    total_size : int
        The number of particles being simulated.
    bandwidth : float
        The detection bandwidth in Hz.

    Returns
    -------
    np.ndarray
        Array of amplitudes with RIN noise applied.

    Equations
    ---------
    1. Relative Intensity Noise (RIN):
        RIN quantifies the fluctuations in the laser's intensity relative to its mean intensity.
        RIN is typically specified as a power spectral density (PSD) in units of dB/Hz:
        \[
        \text{RIN (dB/Hz)} = 10 \cdot \log_{10}\left(\frac{\text{Noise Power (per Hz)}}{\text{Mean Power}}\right)
        \]

    2. Conversion from dB/Hz to Linear Scale:
        To compute noise power, RIN must be converted from dB to a linear scale:
        \[
        \text{RIN (linear)} = 10^{\text{RIN (dB/Hz)} / 10}
        \]

    3. Total Noise Power:
        The total noise power depends on the bandwidth (\(B\)) of the detection system:
        \[
        P_{\text{noise}} = \text{RIN (linear)} \cdot B
        \]

    4. Standard Deviation of Amplitude Fluctuations:
        The noise standard deviation for amplitude is derived from the total noise power:
        \[
        \sigma_{\text{amplitude}} = \sqrt{P_{\text{noise}}} \cdot \text{Amplitude}
        \]
        Substituting \(P_{\text{noise}}\), we get:
        \[
        \sigma_{\text{amplitude}} = \sqrt{\text{RIN (linear)} \cdot B} \cdot \text{Amplitude}
        \]

    Implementation
    --------------
    - The RIN value from the source is converted to linear scale using:
        \[
        \text{RIN (linear)} = 10^{\text{source.RIN} / 10}
        \]
    - The noise standard deviation is scaled by the detection bandwidth (\(B\)) in Hz:
        \[
        \sigma_{\text{amplitude}} = \sqrt{\text{RIN (linear)} \cdot B} \cdot \text{source.amplitude}
        \]
    - Gaussian noise with mean \(0\) and standard deviation \(\sigma_{\text{amplitude}}\) is applied to the source amplitude.

    Notes
    -----
    - The bandwidth parameter (\(B\)) must be in Hz and reflects the frequency range of the detection system.
    - The function assumes that RIN is specified in dB/Hz. If RIN is already in linear scale, the conversion step can be skipped.
    """
    amplitude_with_rin = np.ones(total_size) * source.amplitude

    if NoiseSetting.include_RIN_noise and NoiseSetting.include_noises:
        # Convert RIN from dB/Hz to linear scale if necessary
        rin_linear = 10**(source.RIN / 10)

        # Compute noise standard deviation, scaled by bandwidth
        std_dev_amplitude = np.sqrt(rin_linear * bandwidth.to(hertz).magnitude) * source.amplitude

        # Apply Gaussian noise to the amplitude
        amplitude_with_rin += np.random.normal(
            loc=0,
            scale=std_dev_amplitude.to(source.amplitude.units).magnitude,
            size=total_size
        ) * source.amplitude.units

    return amplitude_with_rin


def _compute_detected_signal(source: BaseBeam, detector: Detector, scatterer_dataframe: pd.DataFrame, medium_refractive_index: Quantity) -> np.ndarray:
    """
    Computes the detected signal by analyzing the scattering properties of particles.

    Parameters
    ----------
    source : BaseBeam
        The light source object containing wavelength, power, and other optical properties.
    detector : Detector
        The detector object containing properties such as numerical aperture and angles.
    scatterer : ScattererCollection
        The scatterer object containing particle size and refractive index data.
    tolerance : float, optional
        The tolerance for deciding if two values of size and refractive index are "close enough" to be cached.

    Returns
    -------
    np.ndarray
        Array of coupling values for each particle, based on the detected signal.
    """
    from PyMieSim import experiment as _PyMieSim

    size_list = scatterer_dataframe['Size'].values

    if len(size_list) == 0:
        return np.array([]) * watt

    total_size = len(size_list)
    amplitude_with_rin = apply_rin_noise(source, total_size, detector.signal_digitizer.bandwidth)

    pms_source = _PyMieSim.source.PlaneWave.build_sequential(
        total_size=total_size,
        wavelength=source.wavelength,
        polarization=0 * degree,
        amplitude=amplitude_with_rin
    )

    pms_scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
        total_size=total_size,
        diameter=scatterer_dataframe['Size'].values.quantity.magnitude * scatterer_dataframe['Size'].values.quantity.units,
        property=scatterer_dataframe['RefractiveIndex'].values.quantity.magnitude * scatterer_dataframe['RefractiveIndex'].values.quantity.units,
        medium_property=medium_refractive_index,
        source=pms_source
    )

    pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
        mode_number='NC00',
        total_size=total_size,
        NA=detector.numerical_aperture,
        cache_NA=0 * AU,
        gamma_offset=detector.gamma_angle,
        phi_offset=detector.phi_angle,
        polarization_filter=np.nan * degree,
        sampling=detector.sampling,
        rotation=0 * degree
    )

    # Set up the experiment
    experiment = _PyMieSim.Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    # Compute coupling values
    coupling_value = experiment.get_sequential('coupling').squeeze()
    return np.atleast_1d(coupling_value) * watt


def compute_detected_signal(source: BaseBeam, detector: Detector, scatterer_dataframe: pd.DataFrame, medium_refractive_index: Quantity) -> np.ndarray:
    """
    Computes the detected signal by analyzing the scattering properties of particles.

    Parameters
    ----------
    source : BaseBeam
        The light source object containing wavelength, power, and other optical properties.
    detector : Detector
        The detector object containing properties such as numerical aperture and angles.
    scatterer : ScattererCollection
        The scatterer object containing particle size and refractive index data.
    tolerance : float, optional
        The tolerance for deciding if two values of size and refractive index are "close enough" to be cached.

    Returns
    -------
    np.ndarray
        Array of coupling values for each particle, based on the detected signal.
    """

    size_list = scatterer_dataframe['Size'].values

    TOTAL_SIZE = len(size_list)

    source = Gaussian.build_sequential(
        wavelength=np.linspace(600, 1000, TOTAL_SIZE) * units.nanometer,
        polarization=0 * units.degree,
        optical_power=1e-3 * units.watt,
        NA=0.2 * units.AU,
        total_size=TOTAL_SIZE
    )

    scatterer = Sphere.build_sequential(
        source=source,
        diameter=np.linspace(400, 1400, TOTAL_SIZE) * units.nanometer,
        property=1.4 * units.RIU,
        medium_property=1.0 * units.RIU,
        total_size=TOTAL_SIZE
    )

    detector = CoherentMode.build_sequential(
        mode_number='LP01',
        rotation=0 * units.degree,
        NA=0.2 * units.AU,
        cache_NA=0 * AU,
        polarization_filter=np.nan * units.degree,
        gamma_offset=0 * units.degree,
        phi_offset=0 * units.degree,
        sampling=100 * units.AU,
        total_size=TOTAL_SIZE
    )

    experiment = Setup(scatterer=scatterer, source=source, detector=detector)

    # This call should complete without raising an error.
    coupling = experiment.get_sequential('coupling')

    return np.atleast_1d(coupling) * watt
