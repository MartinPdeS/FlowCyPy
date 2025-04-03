from PyMieSim import experiment
import numpy as np
import pytest
from FlowCyPy import units



def test_before_hand():
    source = experiment.source.PlaneWave(
        polarization=[0, 0, 0, 0] * units.degree,
        amplitude = [1, 1, 1, 1] * units.volt / units.meter,
        wavelength=[500, 500, 500, 500] * units.nanometer
    )

    sphere = experiment.scatterer.Sphere(
        source=source,
        diameter=[100, 200, 300, 400] * units.nanometer,
        property=[1.44, 1.44, 1.44, 1.44] * units.RIU,
        medium_property=[1.1, 1.1, 1.1, 1.1] * units.RIU
    )

    detector = experiment.detector.Photodiode(
        NA=[0.2, 0.2, 0.2, 0.2] * units.AU,
        phi_offset=[0, 0, 0, 0] * units.degree,
        gamma_offset=[0, 0, 0, 0] * units.degree,
        cache_NA=[0, 0, 0, 0] * units.AU,
        sampling=[100, 100, 100, 100] * units.AU,
        mode_number=['NC00', 'NC00', 'NC00', 'NC00'],
        polarization_filter=[np.nan, np.nan, np.nan, np.nan] * units.degree,
        rotation=[0, 0, 0, 0] * units.degree
    )

    # setup = experiment.Setup(
    #     source=source,
    #     scatterer=sphere,
    #     # detector=detector
    # )

    # setup.get_sequential('Qsca')


def test_before_hand_1():
    SIZE = 4
    source = experiment.source.PlaneWave.build_sequential(
        total_size=SIZE,
        polarization=0 * units.degree,
        amplitude = 1 * units.volt / units.meter,
        wavelength=500 * units.nanometer
    )

    sphere = experiment.scatterer.Sphere.build_sequential(
        total_size=SIZE,
        source=source,
        diameter=[100, 200, 300, 400] * units.nanometer,
        property=1.44 * units.RIU,
        medium_property=1.1 * units.RIU
    )

    detector = experiment.detector.Photodiode(
        NA=[0.2, 0.2, 0.2, 0.2] * units.AU,
        phi_offset=[0, 0, 0, 0] * units.degree,
        gamma_offset=[0, 0, 0, 0] * units.degree,
        cache_NA=[0, 0, 0, 0] * units.AU,
        sampling=[100, 100, 100, 100] * units.AU,
        mode_number=['NC00', 'NC00', 'NC00', 'NC00'],
        polarization_filter=[np.nan, np.nan, np.nan, np.nan] * units.degree,
        rotation=[0, 0, 0, 0] * units.degree
    )

    setup = experiment.Setup(
        source=source,
        scatterer=sphere,
        detector=detector
    )

    setup.get_sequential('coupling')




if __name__ == '__main__':
    pytest.main(["-W error", __file__])
