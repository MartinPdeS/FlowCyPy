"""
Sphere: Goniometer
==================

"""


# %%
# Importing the package dependencies: numpy, PyMieSim
import numpy
from PyMieSim.experiment.detector import Photodiode
from PyMieSim.experiment.scatterer import Sphere
from PyMieSim.experiment.source import Gaussian
from PyMieSim.experiment import Setup
from PyOptik import UsualMaterial
from PyMieSim.experiment import measure

# %%
# Defining the source to be employed.
source = Gaussian(
    wavelength=numpy.linspace(440e-9, 600e-9, 100),
    polarization=0,
    optical_power=1e-3,
    NA=0.2
)
# %%
# Defining the ranging parameters for the scatterer distribution
scatterer = Sphere(
    diameter=[100e-9, 200e-9],
    material=UsualMaterial.polystyren,
    medium_index=1,
    source=source
)

# %%
# Defining the detector to be employed.
detector = Photodiode(
    NA=[0.2],
    phi_offset=[0],
    gamma_offset=0,
    sampling=400,
    polarization_filter=None
)

# %%
# Defining the experiment setup
experiment = Setup(
    scatterer=scatterer,
    source=source,
    detector=detector
)

# %%
# Measuring the properties
data = experiment.get(measure.coupling)

# %%
# Plotting the results
data.plot(
    x=source.wavelength,
)
