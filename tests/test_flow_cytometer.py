#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import numpy as np

from PyMieSim.experiment.detector import CoherentMode
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import PlaneWave
from PyMieSim.experiment import Setup
from PyMieSim.units import nanometer, degree, AU, RIU, volt, meter


def test_get_measure():
    source = PlaneWave(
        wavelength=np.linspace(600, 1000, 150) * nanometer,
        polarization=0 * degree,
        amplitude=1 * volt / meter,
    )

    # Configure the spherical scatterer
    scatterer = Sphere(
        diameter=np.linspace(400, 1400, 10) * nanometer,
        source=source,
        property=1.4 * RIU,
        medium_property=1.1 * RIU
    )

    # Configure the detector
    detector = CoherentMode(
        mode_number='LP01',
        rotation=0 * degree,
        NA=[0.1] * AU,
        polarization_filter=None,
        gamma_offset=[0, 1] * degree,
        phi_offset=0 * degree,
        sampling=100 * AU
    )

    # Set up and run the experiment
    experiment = Setup(scatterer=scatterer, source=source, detector=detector)

    experiment.get('coupling', drop_unique_level=True, scale_unit=True)


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
