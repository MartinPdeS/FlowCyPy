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
from FlowCyPy import NoiseSetting
from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, Population, distribution
from FlowCyPy import GaussianBeam
from FlowCyPy import FlowCell
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import FlowCytometer


NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_dark_current_noise = False

np.random.seed(3)  # Ensure reproducibility


source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,           # Numerical aperture
    wavelength=200 * units.nanometer,           # Wavelength
    optical_power=20 * units.milliwatt          # Optical power
)

flow_cell = FlowCell(
    source=source,
    volume_flow=10 * units.microliter / units.second,  # Flow volume
    flow_area=(60 * units.micrometer) ** 2,       # Cross-sectional area
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

# Add an Exosome population
scatterer_collection.add_population(exosome)

scatterer_collection.dilute(factor=160)


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

cytometer = FlowCytometer(
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell,
    background_power=0.001 * units.milliwatt
)


acquisition = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

# acquisition.scatterer.plot(x='forward', y='side')

triggered_acquisition = acquisition.run_triggering(
    threshold=0.2 * units.millivolt,
    trigger_detector_name='forward',
    max_triggers=35,
    pre_buffer=64,
    post_buffer=64
)


triggered_acquisition.signal.plot()
