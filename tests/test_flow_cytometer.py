#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
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


def test_get_measure():
    total_size = 150
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
