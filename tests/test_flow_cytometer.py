import numpy as np
import pytest
from FlowCyPy import units
import PyMieSim
PyMieSim.debug_mode = True
from PyMieSim.experiment.detector import CoherentMode
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import Gaussian
from PyMieSim.experiment import Setup
from PyMieSim.units import watt, AU




def test_debug():
    TOTAL_SIZE = 100

    source = Gaussian(
        wavelength=np.linspace(600, 1000, TOTAL_SIZE) * units.nanometer,
        polarization=0 * units.degree,
        optical_power=1e-3 * units.watt,
        NA=0.2 * units.AU,
        # total_size=TOTAL_SIZE
    )

    scatterer = Sphere(
        source=source,
        diameter=np.linspace(400, 1400, 2) * units.nanometer,
        property=1.4 * units.RIU,
        medium_property=1.0 * units.RIU,
        # total_size=TOTAL_SIZE
    )

    detector = CoherentMode(
        mode_number='LP01',
        rotation=0 * units.degree,
        NA=0.2 * units.AU,
        cache_NA=0 * AU,
        polarization_filter=np.nan * units.degree,
        gamma_offset=0 * units.degree,
        phi_offset=0 * units.degree,
        sampling=100 * units.AU,
        # total_size=TOTAL_SIZE
    )

    experiment = Setup(scatterer=scatterer, source=source, detector=detector)

    experiment.get('coupling')



if __name__ == '__main__':
    pytest.main(["-W error", __file__])
