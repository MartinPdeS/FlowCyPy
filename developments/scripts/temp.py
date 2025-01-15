"""
Workflow
========

This tutorial demonstrates how to simulate a flow cytometry experiment using the FlowCyPy library.
The simulation involves configuring a flow setup, defining a single population of particles, and
analyzing scattering signals from two detectors to produce a 2D density plot of scattering intensities.

Overview:
---------
1. Configure the flow cell and particle population.
2. Define the laser source and detector parameters.
3. Simulate the flow cytometry experiment.
4. Analyze the generated signals and visualize results.

"""

# %%
# Step 0: Import Necessary Libraries
# -----------------------------------
# Here, we import the necessary libraries and units for the simulation. The units module helps us
# define physical quantities like meters, seconds, and watts in a concise and consistent manner.

import numpy as np
from FlowCyPy import units


# %%
# Step 1: Configure Noise Settings
# ---------------------------------
# Noise settings are configured to simulate real-world imperfections. In this example, we include noise
# globally but exclude specific types, such as shot noise and thermal noise.

from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_thermal_noise = True
NoiseSetting.include_dark_current_noise = True
NoiseSetting.include_RIN_noise = True

np.random.seed(3)  # Ensure reproducibility


# %%
# Step 2: Configure the Laser Source
# ----------------------------------
# The laser source generates light that interacts with the particles. Its parameters, like numerical
# aperture and wavelength, affect how light scatters, governed by Mie theory.

from FlowCyPy import GaussianBeam

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,           # Numerical aperture
    wavelength=200 * units.nanometer,           # Wavelength
    optical_power=20 * units.milliwatt          # Optical power
)



from FlowCyPy import FlowCell

flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * units.meter / units.second,  # Flow speed
    flow_area=(10 * units.micrometer) ** 2,       # Cross-sectional area
)


from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, Population, distribution

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

custom_population = Population(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

# Add an Exosome population
scatterer_collection.add_population(exosome, custom_population)

scatterer_collection.dilute(factor=16)


from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_freq=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=1.2 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=1.2 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin,
)

from FlowCyPy import FlowCytometer

cytometer = FlowCytometer(
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell,
    background_power=0.001 * units.milliwatt
)

# Run the flow cytometry simulation
experiment = cytometer.get_acquisition(run_time=0.2 * units.millisecond)



experiment.run_triggering(
    threshold=0.2 * units.millivolt,
    trigger_detector_name='forward',
    max_triggers=35,
    pre_buffer=64,
    post_buffer=64
)

from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=2)

experiment.classify_dataset(
    classifier=classifier,
    features=['Height', 'widths'],
    detectors=['side', 'forward']
)


experiment.plot.classifier()

