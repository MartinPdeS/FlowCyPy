#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch

from PyMieSim.experiment.detector import CoherentMode
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import Gaussian, PlaneWave

from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import distribution
from FlowCyPy.population import Population
from FlowCyPy import units
from FlowCyPy import peak_locator
import PyMieSim
PyMieSim.debug_mode = True
from FlowCyPy import distribution

# ----------------- FIXTURES -----------------

@pytest.fixture
def default_digitizer():
    """Fixture for creating a default signal digitizer."""
    return SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=5e6 * units.hertz,
    )

@pytest.fixture
def detector_0():
    """Fixture for creating the first default detector."""
    return Detector(
        name='default',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def detector_1():
    """Fixture for creating the second default detector."""
    return Detector(
        name='default_bis',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def flow_cell():
    """Fixture for creating a default flow cell."""
    source = GaussianBeam(
        numerical_aperture=1 * units.AU,
        wavelength=1550 * units.nanometer,
        optical_power=100e-3 * units.watt,
    )

    return FlowCell(
        source=source,
        volume_flow=0.1 * units.microliter / units.second,
        flow_area=(12 * units.micrometer) ** 2,
        event_scheme='uniform-sequential'
    )

@pytest.fixture
def size_distribution():
    """Fixture for creating a normal size distribution."""
    return distribution.Normal(
        mean=1.0 * units.micrometer,
        std_dev=0.1 * units.micrometer
    )

@pytest.fixture
def ri_distribution():
    """Fixture for creating a normal refractive index distribution."""
    return distribution.Normal(
        mean=1.5 * units.RIU,
        std_dev=0.1 * units.RIU
    )

@pytest.fixture
def population(size_distribution, ri_distribution):
    """Fixture for creating a default population."""
    return Population(
        particle_count=110 * units.particle,
        size=size_distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

@pytest.fixture
def scatterer_collection(population):
    """Fixture for creating a scatterer collection with a default population."""
    scatterer = ScattererCollection()
    scatterer.add_population(population)
    return scatterer

@pytest.fixture
def flow_cytometer(detector_0, detector_1, scatterer_collection, flow_cell, default_digitizer):
    """Fixture for creating a default Flow Cytometer."""
    return FlowCytometer(
        signal_digitizer=default_digitizer,
        scatterer_collection=scatterer_collection,
        detectors=[detector_0, detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

def test_get_measure(flow_cytometer):
    from PyMieSim import experiment as _PyMieSim

    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    size_list = acquisition.scatterer['Size'].values

    total_size = len(size_list)
    source = Gaussian.build_sequential(
        total_size=total_size,
        wavelength=np.linspace(600, 1000, total_size) * units.nanometer,
        polarization=0 * units.degree,
        NA=0.2 * units.AU,
        optical_power=1e-3 * units.watt,
    )

    # Configure the spherical scatterer
    scatterer = Sphere.build_sequential(
        total_size=total_size,
        diameter=10 * units.nanometer,
        source=source,
        property=1.4 * units.RIU,
        medium_property=1.1 * units.RIU
    )

    # Configure the detector
    detector = CoherentMode.build_sequential(
        mode_number='LP01',
        rotation=0 * units.degree,
        NA=0.1 * units.AU,
        polarization_filter=np.nan * units.degree,
        gamma_offset=0 * units.degree,
        phi_offset=0 * units.degree,
        sampling=100 * units.AU,
        cache_NA=0. *  units.AU,
        total_size=total_size
    )

    # Set up and run the experiment
    experiment = Setup(scatterer=scatterer, source=source, detector=detector)

    coupling_value = experiment.get_sequential('coupling').squeeze()

    output = np.atleast_1d(coupling_value) * units.watt


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
