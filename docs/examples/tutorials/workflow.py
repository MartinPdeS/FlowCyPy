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
# NoiseSetting.include_shot_noise = False
# NoiseSetting.include_thermal_noise = False
# NoiseSetting.include_dark_current_noise = False

np.random.seed(3)  # Ensure reproducibility


# %%
# Step 2: Configure the Laser Source
# ----------------------------------
# The laser source generates light that interacts with the particles. Its parameters, like numerical
# aperture and wavelength, affect how light scatters, governed by Mie theory.

from FlowCyPy import GaussianBeam

source = GaussianBeam(
    numerical_aperture=0.1 * units.AU,           # Numerical aperture
    wavelength=450 * units.nanometer,           # Wavelength
    optical_power=200 * units.milliwatt          # Optical power
)


# %%
# Step 3: Set Up the Flow Cell
# ----------------------------
# The flow cell models the movement of particles in the cytometer. For example, the volume of fluid
# passing through the cross-sectional area is calculated as:
#
# .. math::
#     \text{Flow Volume} = \text{Flow Speed} \times \text{Flow Area} \times \text{Run Time}

from FlowCyPy.flow_cell import FlowCell

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=100 * units.micrometer,
    height=100 * units.micrometer,
)

flow_cell.plot(n_samples=300)


# %%
# Step 4: Define ScattererCollection and Population
# -------------------------------------------------
# The scatterer represents particles in the flow. The concentration of particles in the flow cell is
# given by:
#
# .. math::
#     \text{Concentration} = \frac{\text{Number of Particles}}{\text{Volume of Flow}}

from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, Sphere, distribution

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

custom_population = Sphere(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

# Add an Exosome population
scatterer_collection.add_population(exosome, custom_population)

scatterer_collection.dilute(factor=8)

# Initialize the scatterer with the flow cell
df = scatterer_collection.get_population_dataframe(total_sampling=600, use_ratio=False)  # Visualize the particle population

df.plot(x='Diameter', bins='auto')

# %%
# Step 5: Define Detectors
# ------------------------
# Detectors measure light intensity. Parameters like responsivity define the conversion of optical
# power to electronic signals, and saturation level represents the maximum signal they can handle.

from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin,
)


detector_2 = Detector(
    name='det_2',
    phi_angle=30 * units.degree,                 # Side scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
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
from FlowCyPy import FlowCytometer, circuits

cytometer = FlowCytometer(
    source=source,
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1, detector_2],
    flow_cell=flow_cell,
    background_power=0.001 * units.milliwatt
)

processing_steps = [
    circuits.BaselineRestorator(window_size=1000 * units.microsecond),
    circuits.BesselLowPass(cutoff=3 * units.megahertz, order=4, gain=2)
]

# Run the flow cytometry simulation
cytometer.prepare_acquisition(run_time=0.1 * units.millisecond)
acquisition = cytometer.get_acquisition(processing_steps=processing_steps)

_ = acquisition.scatterer.plot(
    x='side',
    y='forward',
    z='RefractiveIndex'
)

# %%
# Visualize the scatter signals from both detectors
acquisition.analog.plot()

# %%
# Step 7: Analyze Detected Signals
# --------------------------------
# The Peak algorithm detects peaks in signals by analyzing local maxima within a defined
# window size and threshold.
triggered_acquisition = acquisition.run_triggering(
    threshold=3 * units.microvolt,
    trigger_detector_name='forward',
    max_triggers=35,
    pre_buffer=20,
    post_buffer=20
)

triggered_acquisition.analog.plot()


# %%
# Getting and plotting the extracted peaks.
from FlowCyPy import peak_locator
peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=True)


peaks = triggered_acquisition.detect_peaks(peak_algorithm)


peaks.plot(feature='Height', x='side', y='forward')

# %%
# Step 8: Classifying the collected dataset
from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=2)

data = classifier.run(
    dataframe=peaks.unstack('Detector'),
    features=['Height'],
    detectors=['side', 'forward']
)

_ = data.plot(feature='Height', x='side', y='forward')