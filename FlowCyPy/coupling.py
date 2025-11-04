from typing import List
import numpy as np
import pandas as pd
import pint_pandas
import PyMieSim.experiment as _PyMieSim
from TypedUnit import Frequency, ureg

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
        self, event_dataframes: List[pd.DataFrame], compute_cross_section: bool = False
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
        for event_dataframe in event_dataframes:
            _dict = dict(
                event_dataframe=event_dataframe,
                compute_cross_section=compute_cross_section,
            )
            if event_dataframe.population.__class__.__name__ == "Sphere":
                self._process_sphere(**_dict)
            elif event_dataframe.population.__class__.__name__ == "CoreShell":
                self._process_coreshell(**_dict)

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
            mode_number="NC00",
            NA=self.detector.numerical_aperture,
            cache_NA=self.detector.cache_numerical_aperture,
            gamma_offset=self.detector.gamma_angle,
            phi_offset=self.detector.phi_angle,
            polarization_filter=np.nan * ureg.degree,
            sampling=self.detector.sampling,
            rotation=0 * ureg.degree,
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

        source, detector = self._build_source_and_detector(
            event_dataframe, num_particles
        )

        scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
            total_size=num_particles,
            diameter=event_dataframe["Diameter"].values.quantity,
            property=event_dataframe["RefractiveIndex"].values.quantity,
            medium_property=event_dataframe.medium_refractive_index,
            source=source,
        )

        experiment = _PyMieSim.Setup(
            source=source, scatterer=scatterer, detector=detector
        )

        event_dataframe.loc[:, f"Detector:{self.detector.name}[SCATTERING]"] = (
            pint_pandas.PintArray(
                experiment.get_sequential("coupling"), dtype=ureg.watt
            )
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

        source, detector = self._build_source_and_detector(
            event_dataframe, num_particles
        )

        scatterer = _PyMieSim.scatterer.CoreShell.build_sequential(
            total_size=num_particles,
            core_diameter=event_dataframe["CoreDiameter"].values.quantity,
            core_property=event_dataframe["CoreRefractiveIndex"].values.quantity,
            shell_thickness=event_dataframe["ShellThickness"].values.quantity,
            shell_property=event_dataframe["ShellRefractiveIndex"].values.quantity,
            medium_property=event_dataframe.medium_refractive_index,
            source=source,
        )

        experiment = _PyMieSim.Setup(
            source=source, scatterer=scatterer, detector=detector
        )

        event_dataframe.loc[:, f"Detector:{self.detector.name}[SCATTERING]"] = (
            pint_pandas.PintArray(
                experiment.get_sequential("coupling"), dtype=ureg.watt
            )
        )

        if compute_cross_section:
            event_dataframe.loc[:, "Csca"] = pint_pandas.PintArray(
                experiment.get_sequential("Csca"), dtype=ureg.meter * ureg.meter
            )


class FluorescenceSimulator:
    """
    Compute per-particle fluorescence emission power seen by a given fluorescence detector.

    This does NOT call PyMieSim because fluorescence emission for subwavelength particles
    is (to first order) isotropic + spectral. Instead, we model:

        detected_power =  copies_per_particle
                        . quantum_yield
                        . excitation_intensity
                        . detector_coupling
                        . calibration_factor

    and fill event_df[detector.name] with that power [watt].

    Assumptions:
    ------------
    - Each row in event_df represents one particle event and has:
        - x, y positions (for excitation intensity)
        - columns describing which population / label(s) it carries
    - Each population has one or more FluorescenceLabel objects you can look up.
    """

    def __init__(self, source: BaseBeam, detector: object, bandwidth: Frequency):
        self.source = source
        self.detector = detector
        self.bandwidth = bandwidth

    def run(self, event_dataframes: List[pd.DataFrame]) -> None:
        """
        Parameters
        ----------
        event_dataframes : List[pd.DataFrame]
            List of DataFrames of events containing particle properties.

        Side effect:
        ------------
        Adds/overwrites a PintArray column event_df[detector.name] with optical power [watt].
        """
        for event_dataframe in event_dataframes:
            _dict = dict(event_dataframe=event_dataframe)
            if event_dataframe.population.__class__.__name__ == "Sphere":
                self._process_sphere(**_dict)
            elif event_dataframe.population.__class__.__name__ == "CoreShell":
                self._process_coreshell(**_dict)

    def _process_sphere(self, event_dataframe: pd.DataFrame):
        """
        Process and simulate scattering from spherical particles.

        Parameters
        ----------
        event_dataframes : pd.DataFrame
            The full event DataFrame.
        compute_cross_section : bool
            Whether to compute the scattering cross section.
        """
        number_of_dye = event_dataframe.loc[:, f"Dye:Green"]

        coupling = number_of_dye.pint.magnitude * 100

        event_dataframe.loc[:, f"Detector:{self.detector.name}"] = (
            pint_pandas.PintArray(coupling, dtype=ureg.watt)
        )

        print(event_dataframe.loc[:, f"Detector:{self.detector.name}"])
