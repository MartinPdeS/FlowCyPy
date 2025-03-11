import numpy as np
from FlowCyPy import Detector
from FlowCyPy.source import BaseBeam
from PyMieSim.units import Quantity, degree, watt
from FlowCyPy import units
import pandas as pd
from PyMieSim import experiment as _PyMieSim
import pint_pandas


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
    amplitude_with_rin = source.get_amplitude_signal(
        size=total_size,
        bandwidth=detector.signal_digitizer.bandwidth,
        x=scatterer_dataframe['x'],
        y=scatterer_dataframe['y']
    )

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

    # Compute the coupling value array for the selected rows.
    amplitude_with_rin = source.get_amplitude_signal(
        size=total_size,
        bandwidth=detector.signal_digitizer.bandwidth,
        x=scatterer_dataframe['x'],
        y=scatterer_dataframe['y']
    )

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
