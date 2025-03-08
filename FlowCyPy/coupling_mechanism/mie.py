import numpy as np
from FlowCyPy import Detector
from FlowCyPy.source import BaseBeam
from PyMieSim.units import Quantity, degree, watt, hertz
from FlowCyPy import units
from FlowCyPy.noises import NoiseSetting
import pandas as pd
from PyMieSim import experiment as _PyMieSim
import pint_pandas


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
        The scatterer object containing particle diameter and refractive index data.
    tolerance : float, optional
        The tolerance for deciding if two values of diameter and refractive index are "close enough" to be cached.

    Returns
    -------
    np.ndarray
        Array of coupling values for each particle, based on the detected signal.
    """
    # Create a boolean mask for 'Sphere' particles.
    sphere_mask = scatterer_dataframe['type'] == 'Sphere'
    # Similarly, if needed for coreshell, create its mask:
    coreshell_mask = scatterer_dataframe['type'] == 'CoreShell'

    # Process sphere particles in-place using the mask.
    process_sphere(source, detector, scatterer_dataframe, sphere_mask, medium_refractive_index)

    process_coreshell(source, detector, scatterer_dataframe, coreshell_mask, medium_refractive_index)

def process_sphere(source: BaseBeam, detector: Detector, scatterer_dataframe: pd.DataFrame, sphere_mask: pd.Series, medium_refractive_index: Quantity) -> None:
    """
    Processes the 'Sphere' type particles and updates the original DataFrame in-place.

    Parameters
    ----------
    source : BaseBeam
        The light source.
    detector : Detector
        The detector.
    scatterer_dataframe : pd.DataFrame
        The original DataFrame to update.
    sphere_mask : pd.Series
        Boolean mask selecting rows of type 'Sphere'.
    medium_refractive_index : Quantity
        The refractive index of the medium.
    """
    df = scatterer_dataframe[sphere_mask]
    total_size = len(df)

    if total_size == 0:
        return

    # Compute the coupling value array for the selected rows.
    amplitude_with_rin = apply_rin_noise(source, total_size, detector.signal_digitizer.bandwidth)

    pms_source = _PyMieSim.source.PlaneWave.build_sequential(
        total_size=int(total_size),
        wavelength=source.wavelength,
        polarization=0 * degree,
        amplitude=amplitude_with_rin
    )

    pms_scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
        total_size=total_size,
        diameter=df.loc[sphere_mask, 'Diameter'].values.quantity,
        property=df.loc[sphere_mask, 'RefractiveIndex'].values.quantity,
        medium_property=medium_refractive_index,
        source=pms_source
    )

    pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
        mode_number='NC00',
        total_size=total_size,
        NA=detector.numerical_aperture,
        cache_NA=detector.cache_numerical_aperture,
        gamma_offset=detector.gamma_angle,
        phi_offset=detector.phi_angle,
        polarization_filter=np.nan * degree,
        sampling=detector.sampling,
        rotation=0 * degree
    )

    # Set up the experiment
    experiment = _PyMieSim.Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    # Compute coupling values (an array of length equal to total_size)
    coupling_value = experiment.get_sequential('coupling')

    # Here we update the original DataFrame in-place using the mask.

    scatterer_dataframe.loc[sphere_mask, detector.name] = pint_pandas.PintArray(coupling_value, dtype=units.watt)


def process_coreshell(source: BaseBeam, detector: Detector, scatterer_dataframe: pd.DataFrame, coreshell_mask: pd.Series, medium_refractive_index: Quantity) -> None:
    df = scatterer_dataframe[coreshell_mask]
    total_size = len(df)

    if total_size == 0:
        return np.array([]) * watt

    amplitude_with_rin = apply_rin_noise(source, total_size, detector.signal_digitizer.bandwidth)

    pms_source = _PyMieSim.source.PlaneWave.build_sequential(
        total_size=total_size,
        wavelength=source.wavelength,
        polarization=0 * degree,
        amplitude=amplitude_with_rin
    )

    pms_scatterer = _PyMieSim.scatterer.CoreShell.build_sequential(
        total_size=total_size,
        core_diameter=df['CoreDiameter'].values.quantity,
        core_property=df['CoreRefractiveIndex'].values.quantity,
        shell_thickness=df['ShellThickness'].values.quantity,
        shell_property=df['ShellRefractiveIndex'].values.quantity,
        medium_property=medium_refractive_index,
        source=pms_source
    )

    pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
        mode_number='NC00',
        total_size=total_size,
        NA=detector.numerical_aperture,
        cache_NA=detector.cache_numerical_aperture,
        gamma_offset=detector.gamma_angle,
        phi_offset=detector.phi_angle,
        polarization_filter=np.nan * degree,
        sampling=detector.sampling,
        rotation=0 * degree
    )

    # Set up the experiment
    experiment = _PyMieSim.Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    # Compute coupling values
    coupling_value = experiment.get_sequential('coupling')

    scatterer_dataframe.loc[coreshell_mask, detector.name] = pint_pandas.PintArray(coupling_value, dtype=units.watt)
