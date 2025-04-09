import numpy as np
import pytest
from PyMieSim.binary.interface_experiment import EXPERIMENT
from FlowCyPy.binary.interface_dummy import Dummy
from PyMieSim.binary.interface_sets import CppSourceSet, CppSphereSet, CppScattererProperties, CppMediumProperties

def test_clash_with_pymiesim():
    source_binding = CppSourceSet(
        wavelength=np.linspace(0.1, 1, 10).astype(float),
        jones_vector=np.atleast_2d([[1, 1]]).astype(complex),
        NA=np.atleast_1d([0.1]).astype(float),
        optical_power=np.atleast_1d([0.1]).astype(float),
        is_sequential=False
    )

    medium_properties = CppMediumProperties(index_properties=[1.0])
    scatterer_properties =  CppScattererProperties(index_properties=[1.1, 1.2])

    sphere_binding = CppSphereSet(
        diameter=np.linspace(0.1, 1, 10).astype(float),
        scatterer_properties=scatterer_properties,
        medium_properties=medium_properties,
        is_sequential=False
    )

    binding = EXPERIMENT(debug_mode=True)

    binding.set_Source(source_binding)

    binding.set_Sphere(sphere_binding)

    # a = binding.get_Sphere_Qsca()

    # print(a)

    # a = Dummy()

if __name__ == '__main__':
    pytest.main(["-W error", "-s", __file__])
