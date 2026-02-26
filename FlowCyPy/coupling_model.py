from typing import List
import numpy as np
import pandas as pd
import pint_pandas
import PyMieSim.experiment as _PyMieSim
from TypedUnit import Frequency, ureg

from FlowCyPy.source import BaseBeam


class ScatteringModel:
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
        """
        self.source = source
        self.detector = detector
        self.bandwidth = bandwidth

    def run(
        self, event_frames: List[pd.DataFrame], compute_cross_section: bool = False
    ) -> None:
        """
        Run the scattering simulation on the provided DataFrame.

        Parameters
        ----------
        event_dataframes : List[pd.DataFrame]
            List of DataFrame of events containing particle types and properties.
        compute_cross_section : bool, optional
            Whether to compute and store the scattering cross section.
        """
        for event_dataframe in event_frames:
            _dict = dict(
                event_dataframe=event_dataframe,
                compute_cross_section=compute_cross_section,
            )
            if event_dataframe.scatterer_type == "SpherePopulation":
                self._process_sphere(**_dict)
            elif event_dataframe.scatterer_type == "CoreShellPopulation":
                self._process_coreshell(**_dict)
            else:
                raise ValueError(
                    f"Unknown scatterer type: {event_dataframe.scatterer_type.iloc[0]}"
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

        source = _PyMieSim.source.PlaneWave.build_sequential(
            total_size=num_particles,
            wavelength=self.source.wavelength,
            polarization=0 * ureg.degree,
            amplitude=amplitude,
        )

        detector = _PyMieSim.detector.Photodiode.build_sequential(
            total_size=num_particles,
            NA=self.detector.numerical_aperture,
            cache_NA=self.detector.cache_numerical_aperture,
            gamma_offset=self.detector.gamma_angle,
            phi_offset=self.detector.phi_angle,
            polarization_filter=np.nan * ureg.degree,
            sampling=self.detector.sampling,
            medium_refractive_index=1.0 * ureg.dimensionless,  # TODO: make configurable
        )

        return source, detector

    def _process_sphere(
        self,
        event_dataframe: pd.DataFrame,
        compute_cross_section: bool,
    ):
        """
        Process and simulate scattering from spherical particles.

        Parameters
        ----------
        event_dataframes : pd.DataFrame
            The full event DataFrame.
        compute_cross_section : bool
            Whether to compute the scattering cross section.
        """
        num_particles = len(event_dataframe)

        if num_particles == 0:
            return

        source, detector = self._build_source_and_detector(
            event_dataframe, num_particles
        )

        print(event_dataframe["Diameter"].values.quantity)

        scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
            total_size=num_particles,
            diameter=event_dataframe["Diameter"].values.quantity,
            refractive_index=event_dataframe["RefractiveIndex"].values.quantity,
            medium_refractive_index=event_dataframe[
                "MediumRefractiveIndex"
            ].values.quantity,
            source=source,
        )

        experiment = _PyMieSim.Setup(
            source=source, scatterer=scatterer, detector=detector
        )

        event_dataframe.loc[:, self.detector.name] = pint_pandas.PintArray(
            experiment.get_sequential("coupling"), dtype=ureg.watt
        )

        if compute_cross_section:
            event_dataframe.loc[:, "Csca"] = pint_pandas.PintArray(
                experiment.get_sequential("Csca"), dtype=ureg.meter * ureg.meter
            )

    def _process_coreshell(
        self,
        event_dataframe: pd.DataFrame,
        compute_cross_section: bool,
    ):
        """
        Process and simulate scattering from core-shell particles.

        Parameters
        ----------
        event_dataframe : pd.DataFrame
            The full event DataFrame.
        compute_cross_section : bool
            Whether to compute the scattering cross section.
        """

        num_particles = len(event_dataframe)

        if num_particles == 0:
            return

        source, detector = self._build_source_and_detector(
            event_dataframe, num_particles
        )

        scatterer = _PyMieSim.scatterer.CoreShell.build_sequential(
            total_size=num_particles,
            core_diameter=event_dataframe["CoreDiameter"].values.quantity,
            core_refractive_index=event_dataframe[
                "CoreRefractiveIndex"
            ].values.quantity,
            shell_thickness=event_dataframe["ShellThickness"].values.quantity,
            shell_refractive_index=event_dataframe[
                "ShellRefractiveIndex"
            ].values.quantity,
            medium_refractive_index=event_dataframe.medium_refractive_index,
            source=source,
        )

        experiment = _PyMieSim.Setup(
            source=source, scatterer=scatterer, detector=detector
        )

        event_dataframe.loc[:, self.detector.name] = pint_pandas.PintArray(
            experiment.get_sequential("coupling"), dtype=ureg.watt
        )

        if compute_cross_section:
            event_dataframe.loc[:, "Csca"] = pint_pandas.PintArray(
                experiment.get_sequential("Csca"), dtype=ureg.meter * ureg.meter
            )
