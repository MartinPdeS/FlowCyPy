from typing import List, Any

import numpy as np
import pandas as pd
import PyMieSim.experiment as _PyMieSim

from TypedUnit import ureg
from FlowCyPy.opto_electronics.source import BaseSource
from FlowCyPy.sub_frames.events import EventDataFrame


class ScatteringModel:
    """
    Interface for computing scattering signals with PyMieSim from particle event frames.

    Each event frame is expected to represent a homogeneous scatterer population,
    such as spheres or core-shell particles, and must expose the columns required
    by the corresponding PyMieSim scatterer constructor.
    """

    def __init__(
        self,
        source: BaseSource,
        detector: object,
    ):
        self.source = source
        self.detector = detector

    def run(
        self,
        event_frames: List[EventDataFrame],
        compute_cross_section: bool = False,
    ) -> None:
        """
        Compute scattering for each event frame in place.

        Parameters
        ----------
        event_frames : List[EventDataFrame]
            Event frames containing particle properties and spatial coordinates.
        compute_cross_section : bool, optional
            Whether to compute and store the scattering cross section.
        """
        for event_dataframe in event_frames:
            if len(event_dataframe) == 0:
                continue

            experiment = self._build_experiment(event_dataframe=event_dataframe)

            self._write_results(
                event_dataframe=event_dataframe,
                experiment=experiment,
                compute_cross_section=compute_cross_section,
            )

    def _build_experiment(
        self,
        event_dataframe: EventDataFrame,
    ):
        num_particles = len(event_dataframe)

        source_set = self._build_source_set(
            event_dataframe=event_dataframe,
            num_particles=num_particles,
        )

        detector_set = self._build_detector_set(
            num_particles=num_particles,
        )

        scatterer_set = self._build_scatterer_set(
            event_dataframe=event_dataframe,
            num_particles=num_particles,
        )

        return _PyMieSim.Setup(
            source_set=source_set,
            scatterer_set=scatterer_set,
            detector_set=detector_set,
        )

    def _build_source_set(
        self,
        event_dataframe: EventDataFrame,
        num_particles: int,
    ):

        x_coordinates = event_dataframe["x"]
        y_coordinates = event_dataframe["y"]

        z_coordinates = np.zeros(len(event_dataframe)) * x_coordinates.units

        amplitude = self.source.get_amplitude_signal(
            x=x_coordinates,
            y=y_coordinates,
            z=z_coordinates,
        )

        return _PyMieSim.source_set.PlaneWaveSet.build_sequential(
            target_size=num_particles,
            wavelength=self.source.wavelength,
            polarization=0 * ureg.degree,
            amplitude=amplitude,
        )

    def _build_detector_set(
        self,
        num_particles: int,
    ):
        import PyMieSim.material as _

        return _PyMieSim.detector_set.PhotodiodeSet.build_sequential(
            target_size=num_particles,
            numerical_aperture=self.detector.numerical_aperture,
            cache_numerical_aperture=self.detector.cache_numerical_aperture,
            gamma_offset=self.detector.gamma_angle,
            phi_offset=self.detector.phi_angle,
            sampling=self.detector.sampling,
            medium=1.0,
        )

    def _build_scatterer_set(
        self,
        event_dataframe: EventDataFrame,
        num_particles: int,
    ):
        scatterer_type = event_dataframe.scatterer_type

        if scatterer_type == "SpherePopulation":
            return _PyMieSim.scatterer_set.SphereSet.build_sequential(
                target_size=num_particles,
                diameter=event_dataframe["Diameter"],
                material=event_dataframe["RefractiveIndex"].magnitude,
                medium=event_dataframe["MediumRefractiveIndex"].magnitude,
            )

        if scatterer_type == "CoreShellPopulation":
            return _PyMieSim.scatterer.CoreShellSet.build_sequential(
                target_size=num_particles,
                core_diameter=event_dataframe["CoreDiameter"],
                core_refractive_index=event_dataframe["CoreRefractiveIndex"],
                shell_thickness=event_dataframe["ShellThickness"],
                shell_refractive_index=event_dataframe["ShellRefractiveIndex"],
                medium_refractive_index=event_dataframe["MediumRefractiveIndex"],
            )

        raise ValueError(f"Unknown scatterer type: {scatterer_type}")

    def _write_results(
        self,
        event_dataframe: EventDataFrame,
        experiment,
        compute_cross_section: bool,
    ) -> None:
        coupling = experiment.get_sequential("coupling") * ureg.watt
        event_dataframe.dataframe.set_column(
            column_name=self.detector.name,
            values=coupling,
        )

        if compute_cross_section:
            scattering_cross_section = experiment.get_sequential("Csca") * (
                ureg.meter**2
            )

            event_dataframe.dataframe.set_column(
                column_name="Csca",
                values=scattering_cross_section,
            )
