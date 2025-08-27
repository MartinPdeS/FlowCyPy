import numpy as np
import pandas as pd
import pint_pandas
import PyMieSim.experiment as _PyMieSim
from TypedUnit import Frequency, RefractiveIndex, ureg

from FlowCyPy.source import BaseBeam


class ScatteringSimulator:
    """
    A simulation interface for computing light scattering signals using PyMieSim based on particle types.

    This class handles the setup of source, detector, and scatterer configurations for sphere and core-shell
    particles using PyMieSim's sequential interface, and updates a DataFrame of scattering events accordingly.
    """

    def __init__(
        self,
        source: BaseBeam,
        detector: object,
        bandwidth: Frequency,
        medium_refractive_index: RefractiveIndex,
    ):
        """
        Initialize the scattering simulator with source, detector, digitizer, and medium refractive index.

        Parameters
        ----------
        source : BaseBeam
            The light source object.
        detector : object
            The detector configuration.
        bandwidth : Frequency
            Signal bandwidth.
        medium_refractive_index : RefractiveIndex
            Refractive index of the ambient medium.
        """
        self.source = source
        self.detector = detector
        self.bandwidth = bandwidth
        self.medium_refractive_index = medium_refractive_index

    def run(self, event_df: pd.DataFrame, compute_cross_section: bool = False) -> None:
        """
        Run the scattering simulation on the provided DataFrame.

        Parameters
        ----------
        event_df : pd.DataFrame
            DataFrame of events containing particle types and properties.
        compute_cross_section : bool, optional
            Whether to compute and store the scattering cross section.
        """
        if event_df.empty:
            return

        masks = {
            "Sphere": event_df["type"] == "Sphere",
            "CoreShell": event_df["type"] == "CoreShell",
        }

        for kind, mask in masks.items():
            if mask.any():
                getattr(self, f"_process_{kind.lower()}")(
                    event_df, mask, compute_cross_section
                )

    def _build_source_and_detector(self, event_df: pd.DataFrame, num_particles: int):
        """
        Construct PyMieSim source and detector objects.

        Parameters
        ----------
        event_df : pd.DataFrame
            Event DataFrame containing x/y positions for amplitude computation.
        num_particles : int
            Number of particles to simulate.

        Returns
        -------
        tuple
            (PyMieSim PlaneWave source, PyMieSim Photodiode detector)
        """
        amplitude = self.source.get_amplitude_signal(
            bandwidth=self.bandwidth, x=event_df["x"], y=event_df["y"]
        )

        pms_source = _PyMieSim.source.PlaneWave.build_sequential(
            total_size=num_particles,
            wavelength=self.source.wavelength,
            polarization=0 * ureg.degree,
            amplitude=amplitude,
        )

        pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
            total_size=num_particles,
            mode_number="NC00",
            NA=self.detector.numerical_aperture,
            cache_NA=self.detector.cache_numerical_aperture,
            gamma_offset=self.detector.gamma_angle,
            phi_offset=self.detector.phi_angle,
            polarization_filter=np.nan * ureg.degree,
            sampling=self.detector.sampling,
            rotation=0 * ureg.degree,
        )

        return pms_source, pms_detector

    def _process_sphere(
        self, event_df: pd.DataFrame, mask: pd.Series, compute_cross_section: bool
    ):
        """
        Process and simulate scattering from spherical particles.

        Parameters
        ----------
        event_df : pd.DataFrame
            The full event DataFrame.
        mask : pd.Series
            Boolean mask selecting sphere-type particles.
        compute_cross_section : bool
            Whether to compute the scattering cross section.
        """
        df = event_df[mask]
        num_particles = len(df)

        pms_source, pms_detector = self._build_source_and_detector(df, num_particles)

        scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
            total_size=num_particles,
            diameter=df["Diameter"].values.quantity,
            property=df["RefractiveIndex"].values.quantity,
            medium_property=self.medium_refractive_index,
            source=pms_source,
        )

        experiment = _PyMieSim.Setup(
            source=pms_source, scatterer=scatterer, detector=pms_detector
        )

        event_df.loc[mask, self.detector.name] = pint_pandas.PintArray(
            experiment.get_sequential("coupling"), dtype=ureg.watt
        )

        if compute_cross_section:
            event_df.loc[mask, "Csca"] = pint_pandas.PintArray(
                experiment.get_sequential("Csca"), dtype=ureg.meter * ureg.meter
            )

    def _process_coreshell(
        self, event_df: pd.DataFrame, mask: pd.Series, compute_cross_section: bool
    ):
        """
        Process and simulate scattering from core-shell particles.

        Parameters
        ----------
        event_df : pd.DataFrame
            The full event DataFrame.
        mask : pd.Series
            Boolean mask selecting core-shell-type particles.
        compute_cross_section : bool
            Whether to compute the scattering cross section.
        """
        df = event_df[mask]
        num_particles = len(df)

        pms_source, pms_detector = self._build_source_and_detector(df, num_particles)

        scatterer = _PyMieSim.scatterer.CoreShell.build_sequential(
            total_size=num_particles,
            core_diameter=df["CoreDiameter"].values.quantity,
            core_property=df["CoreRefractiveIndex"].values.quantity,
            shell_thickness=df["ShellThickness"].values.quantity,
            shell_property=df["ShellRefractiveIndex"].values.quantity,
            medium_property=self.medium_refractive_index,
            source=pms_source,
        )

        experiment = _PyMieSim.Setup(
            source=pms_source, scatterer=scatterer, detector=pms_detector
        )

        event_df.loc[mask, self.detector.name] = pint_pandas.PintArray(
            experiment.get_sequential("coupling"), dtype=ureg.watt
        )

        if compute_cross_section:
            event_df.loc[mask, "Csca"] = pint_pandas.PintArray(
                experiment.get_sequential("Csca"), dtype=ureg.meter * ureg.meter
            )
