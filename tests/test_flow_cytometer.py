#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import numpy as np
from PyMieSim import units
from PyMieSim.experiment.detector import CoherentMode
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import Gaussian
from PyMieSim.experiment import Setup


def test_get_measure():
    source = Gaussian(
        wavelength=np.linspace(600, 1000, 150) * units.nanometer,
        polarization=0 * units.degree,
        NA=0.2 * units.AU,
        optical_power=1e-3 * units.watt,
    )

    # Configure the spherical scatterer
    scatterer = Sphere(
        diameter=np.linspace(400, 1400, 10) * units.nanometer,
        source=source,
        property=1.4 * units.RIU,
        medium_property=1.1 * units.RIU
    )

    # Configure the detector
    detector = CoherentMode(
        mode_number='LP01',
        rotation=0 * units.degree,
        NA=[0.1] * units.AU,
        polarization_filter=None,
        gamma_offset=[0, 1] * units.degree,
        phi_offset=0 * units.degree,
        sampling=100 * units.AU
    )

    # Set up and run the experiment
    experiment = Setup(scatterer=scatterer, source=source, detector=detector)

    experiment.get('coupling', drop_unique_level=True, scale_unit=True)


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
