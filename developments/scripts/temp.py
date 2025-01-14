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

NoiseSetting.include_noises = False
NoiseSetting.include_shot_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_dark_current_noise = False

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


# %%
# Step 3: Set Up the Flow Cell
# ----------------------------
# The flow cell models the movement of particles in the cytometer. For example, the volume of fluid
# passing through the cross-sectional area is calculated as:
#
# .. math::
#     \text{Flow Volume} = \text{Flow Speed} \times \text{Flow Area} \times \text{Run Time}

from FlowCyPy import FlowCell

flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * units.meter / units.second,  # Flow speed
    flow_area=(10 * units.micrometer) ** 2,       # Cross-sectional area
)


# %%
# Step 4: Define ScattererCollection and Population
# -------------------------------------------------
# The scatterer represents particles in the flow. The concentration of particles in the flow cell is
# given by:
#
# .. math::
#     \text{Concentration} = \frac{\text{Number of Particles}}{\text{Volume of Flow}}

from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, LDL, Population, distribution

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

population_0 = Population(
    name='Pop 0',
    particle_count=3e+8 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=100 * units.nanometer, spread=16),
    refractive_index=distribution.Normal(mean=1.42 * units.RIU, std_dev=0.002 * units.RIU)
)

population_1 = Population(
    name='Pop 1',
    particle_count=3e+8 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=150 * units.nanometer, spread=416),
    refractive_index=distribution.Normal(mean=1.39 * units.RIU, std_dev=0.002 * units.RIU)
)

# Add an Exosome population
scatterer_collection.add_population(population_0, population_1)

scatterer_collection.dilute(factor=2)

# Initialize the scatterer with the flow cell
scatterer_collection.plot()  # Visualize the particle population

# %%
# Step 5: Define Detectors
# ------------------------
# Detectors measure light intensity. Parameters like responsitivity define the conversion of optical
# power to electronic signals, and saturation level represents the maximum signal they can handle.

from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    # saturation_levels=[0 * units.volt, 20 * units.millivolt],
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

# %%
# Step 6: Simulate Flow Cytometry Experiment
# ------------------------------------------
# The FlowCytometer combines all components to simulate scattering. The interaction between light
# and particles follows Mie theory:
#
# .. math::
#     \sigma_s = \frac{2 \pi}{k} \sum_{n=1}^\infty (2n + 1) (\lvert a_n \rvert^2 + \lvert b_n \rvert^2)

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

# experiment.plot.scatterer()


experiment.plot.coupling_distribution()

# Visualize the scatter signals from both detectors
# experiment.plot.signals()

# %%
# Step 7: Analyze Detected Signals
# --------------------------------
# The Peak algorithm detects peaks in signals by analyzing local maxima within a defined
# window size and threshold.
experiment.run_triggering(
    threshold=1 * units.millivolt,
    trigger_detector_name='forward',
    max_triggers=35,
    pre_buffer=64,
    post_buffer=64
)

experiment.plot.trigger()

# experiment.plot.peaks(
#     x_detector='side',
#     y_detector='forward'
# )


from FlowCyPy.classifier import KmeansClassifier
# %%
classifier = KmeansClassifier(
    dataframe=experiment.data.peaks
)

df = classifier.run(
    number_of_cluster=2,
    features=['Height'],
    detectors=['side', 'forward']
)

import seaborn as sns
import matplotlib.pyplot as plt


sns.jointplot(
    data=df,
    x='side',
    hue='Label',
    y='forward'
)

plt.show()