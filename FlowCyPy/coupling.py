import PyMieSim.experiment as _PyMieSim
import numpy as np
import pandas as pd
import pint_pandas

from FlowCyPy.source import BaseBeam
from PyMieSim.units import Quantity, degree, watt
from FlowCyPy import units


def compute_detected_signal(
    source: BaseBeam,
    detector: object,
    scatterer_df: pd.DataFrame,
    medium_refractive_index: Quantity,
    compute_cross_section: bool = True
) -> None:
    """
    Computes the detected coupling signal for scatterers by analyzing their scattering properties and
    updates the DataFrame in place with the measured values.

    This function distinguishes between two scatterer types ('Sphere' and 'CoreShell') using a
    boolean mask on the 'type' column and then processes each type with dedicated helper functions.

    Parameters
    ----------
    source : BaseBeam
        Light source object providing optical properties like wavelength and power.
    detector : object
        Detector object that includes attributes such as numerical aperture, angles, and sampling
        configuration.
    scatterer_df : pd.DataFrame
        DataFrame containing scatterer properties. It must include a column named 'type' with values
        'Sphere' or 'CoreShell', and additional columns required for each scatterer type.
    medium_refractive_index : Quantity
        The refractive index of the surrounding medium.
    compute_cross_section : bool, optional
        If True, the scattering cross section (Csca) is computed and added to the DataFrame under the
        column 'Csca'.

    Returns
    -------
    None
        The input DataFrame is updated in place with new columns for the detected coupling signal and,
        optionally, the scattering cross section.
    """
    # Create boolean masks for each scatterer type.
    sphere_mask = scatterer_df["type"] == "Sphere"
    coreshell_mask = scatterer_df["type"] == "CoreShell"

    # Process sphere and core-shell scatterers.
    process_sphere(source, detector, scatterer_df, sphere_mask, medium_refractive_index, compute_cross_section)
    process_coreshell(source, detector, scatterer_df, coreshell_mask, medium_refractive_index, compute_cross_section)


def process_sphere(
    source: BaseBeam,
    detector: object,
    scatterer_df: pd.DataFrame,
    sphere_mask: pd.Series,
    medium_refractive_index: Quantity,
    compute_cross_section: bool = False
) -> None:
    """
    Processes scatterers of type 'Sphere' and updates the DataFrame with computed coupling and, optionally,
    scattering cross sections.

    The function:
      - Filters the DataFrame to extract rows corresponding to spherical particles.
      - Computes the spatial amplitude signal based on the (x, y) positions.
      - Sets up a simulation using PyMieSim for a plane wave source, sphere scatterers, and a photodiode detector.
      - Updates the DataFrame with the detected coupling values and, if requested, the scattering cross section.

    Parameters
    ----------
    source : BaseBeam
        Light source object.
    detector : object
        Detector object containing measurement settings.
    scatterer_df : pd.DataFrame
        DataFrame with scatterer data to be updated.
    sphere_mask : pd.Series
        Boolean mask that selects rows corresponding to 'Sphere' scatterers.
    medium_refractive_index : Quantity
        Refractive index of the ambient medium.
    compute_cross_section : bool, optional
        If True, the scattering cross section (Csca) is computed and added to the DataFrame.

    Returns
    -------
    None
    """
    # Extract rows for sphere scatterers.
    df_sphere = scatterer_df[sphere_mask]
    num_particles = len(df_sphere)
    if num_particles == 0:
        return

    # Compute amplitude signal using spatial positions.
    amplitude = source.get_amplitude_signal(
        size=num_particles,
        bandwidth=detector.signal_digitizer.bandwidth,
        x=scatterer_df["x"],
        y=scatterer_df["y"]
    )

    # Build the plane wave source for simulation.
    pms_source = _PyMieSim.source.PlaneWave.build_sequential(
        total_size=num_particles,
        wavelength=source.wavelength,
        polarization=0 * degree,
        amplitude=amplitude
    )

    # Build the sphere scatterer simulation.
    pms_scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
        total_size=num_particles,
        diameter=df_sphere["Diameter"].values.quantity,
        property=df_sphere["RefractiveIndex"].values.quantity,
        medium_property=medium_refractive_index,
        source=pms_source
    )

    # Build the photodiode detector simulation.
    pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
        total_size=num_particles,
        mode_number="NC00",
        NA=detector.numerical_aperture,
        cache_NA=detector.cache_numerical_aperture,
        gamma_offset=detector.gamma_angle,
        phi_offset=detector.phi_angle,
        polarization_filter=np.nan * degree,
        sampling=detector.sampling,
        rotation=0 * degree
    )

    # Set up the experiment combining source, scatterer, and detector.
    experiment = _PyMieSim.Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    # Compute the coupling signal.
    coupling_values = experiment.get_sequential("coupling")
    scatterer_df.loc[sphere_mask, detector.name] = pint_pandas.PintArray(coupling_values, dtype=units.watt)

    # Optionally compute the scattering cross section and update the DataFrame.
    if compute_cross_section:
        cross_section = experiment.get_sequential("Csca")
        scatterer_df.loc[sphere_mask, "Csca"] = pint_pandas.PintArray(cross_section, dtype=units.meter * units.meter)


def process_coreshell(
    source: BaseBeam,
    detector: object,
    scatterer_df: pd.DataFrame,
    coreshell_mask: pd.Series,
    medium_refractive_index: Quantity,
    compute_cross_section: bool = False
) -> None:
    """
    Processes scatterers of type 'CoreShell' and updates the DataFrame with computed coupling and, optionally,
    scattering cross sections.

    The function:
      - Filters the DataFrame to extract rows corresponding to core-shell particles.
      - Computes the spatial amplitude signal based on the (x, y) positions.
      - Configures a simulation for a plane wave source, core-shell scatterers, and a photodiode detector.
      - Writes the computed coupling values (and optionally the scattering cross section) back to the DataFrame.

    Parameters
    ----------
    source : BaseBeam
        Light source object.
    detector : object
        Detector object containing measurement settings.
    scatterer_df : pd.DataFrame
        DataFrame with scatterer data to be updated.
    coreshell_mask : pd.Series
        Boolean mask that selects rows corresponding to 'CoreShell' scatterers.
    medium_refractive_index : Quantity
        Refractive index of the ambient medium.
    compute_cross_section : bool, optional
        If True, the scattering cross section (Csca) is computed and added to the DataFrame.

    Returns
    -------
    None
    """
    # Extract rows for core-shell scatterers.
    df_coreshell = scatterer_df[coreshell_mask]
    num_particles = len(df_coreshell)
    if num_particles == 0:
        return

    # Compute amplitude signal using spatial positions.
    amplitude = source.get_amplitude_signal(
        size=num_particles,
        bandwidth=detector.signal_digitizer.bandwidth,
        x=scatterer_df["x"],
        y=scatterer_df["y"]
    )

    # Build the plane wave source for simulation.
    pms_source = _PyMieSim.source.PlaneWave.build_sequential(
        total_size=num_particles,
        wavelength=source.wavelength,
        polarization=0 * degree,
        amplitude=amplitude
    )

    # Build the core-shell scatterer simulation.
    pms_scatterer = _PyMieSim.scatterer.CoreShell.build_sequential(
        total_size=num_particles,
        core_diameter=df_coreshell["CoreDiameter"].values.quantity,
        core_property=df_coreshell["CoreRefractiveIndex"].values.quantity,
        shell_thickness=df_coreshell["ShellThickness"].values.quantity,
        shell_property=df_coreshell["ShellRefractiveIndex"].values.quantity,
        medium_property=medium_refractive_index,
        source=pms_source
    )

    # Build the photodiode detector simulation.
    pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
        total_size=num_particles,
        mode_number="NC00",
        NA=detector.numerical_aperture,
        cache_NA=detector.cache_numerical_aperture,
        gamma_offset=detector.gamma_angle,
        phi_offset=detector.phi_angle,
        polarization_filter=np.nan * degree,
        sampling=detector.sampling,
        rotation=0 * degree
    )

    # Set up the experiment combining source, scatterer, and detector.
    experiment = _PyMieSim.Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    # Compute the coupling signal.
    coupling_values = experiment.get_sequential("coupling")
    scatterer_df.loc[coreshell_mask, detector.name] = pint_pandas.PintArray(coupling_values, dtype=units.watt)

    # Optionally compute the scattering cross section and update the DataFrame.
    if compute_cross_section:
        cross_section = experiment.get_sequential("Csca")
        scatterer_df.loc[coreshell_mask, "Csca"] = pint_pandas.PintArray(cross_section, dtype=units.meter * units.meter)
