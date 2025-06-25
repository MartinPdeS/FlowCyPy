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
NoiseSetting.include_dark_current_noise = True
NoiseSetting.include_source_noise = True
NoiseSetting.include_amplifier_noise = True
NoiseSetting.assume_perfect_hydrodynamic_focusing = True

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
    optical_power=200 * units.milliwatt,          # Optical power
    RIN=-140
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

# %%
# Step 4: Define ScattererCollection and Population
# -------------------------------------------------
# The scatterer represents particles in the flow. The concentration of particles in the flow cell is
# given by:
#
# .. math::
#     \text{Concentration} = \frac{\text{Number of Particles}}{\text{Volume of Flow}}

from FlowCyPy import Fluidics, ScattererCollection
from FlowCyPy.instances import Exosome, Sphere, distribution

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

custom_population = Sphere(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

# Add an Exosome population
scatterer_collection.add_population(custom_population)


custom_population = Sphere(
    name='Pop 1',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=200 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

# Add an Exosome population
scatterer_collection.add_population(custom_population)

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

fluidics.plot(run_time=3.5 * units.millisecond)

# %%
# Generate a DataFrame of events, which contains information about the particles in the flow cell.
# The DataFrame includes properties like diameter, refractive index, and scattering angles.
event_dataframe = fluidics.generate_event_dataframe(run_time=3.5 * units.millisecond)


# %%
# Plot the distribution of particle diameters in the DataFrame.
event_dataframe.plot(x='Diameter', bins='auto')


# %%
# Step 5: Define Detectors
# ------------------------
# Detectors measure light intensity. Parameters like responsivity define the conversion of optical
# power to electronic signals, and saturation level represents the maximum signal they can handle.

from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier

digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

detector_2 = Detector(
    name='det 2',
    phi_angle=30 * units.degree,
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz,
    voltage_noise_density=.1 * units.nanovolt / units.sqrt_hertz,
    current_noise_density=.2 * units.femtoampere / units.sqrt_hertz
)

from FlowCyPy import OptoElectronics

opto_electronics = OptoElectronics(
    detectors=[detector_0, detector_1, detector_2],
    digitizer=digitizer,
    source=source,
    amplifier=amplifier
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
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    background_power=0.001 * units.milliwatt
)

cytometer.opto_electronics = opto_electronics

processing_steps = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=2 * units.megahertz, order=4, gain=2)
]

# Run the flow cytometry simulation
acquisition, event_dataframe = cytometer.get_acquisition(
    run_time=.5 * units.millisecond,
    processing_steps=processing_steps
)

acquisition.normalize_units(time_units='max', signal_units='max')

_ = acquisition.scatterer.plot(
    x='side',
    y='forward',
    z='RefractiveIndex'
)

# %%
# Visualize the scatter signals from both detectors
acquisition.plot()

# %%
# Step 7: Analyze Detected Signals
# --------------------------------
# The Peak algorithm detects peaks in signals by analyzing local maxima within a defined
# window size and threshold.
from FlowCyPy.triggering_system import DynamicWindow

trigger = DynamicWindow(
    dataframe=acquisition,
    trigger_detector_name='forward',
    max_triggers=-1,
    pre_buffer=20,
    post_buffer=20,
    digitizer=digitizer
)

analog_triggered = trigger.run(
    threshold=10 * units.microvolt
)

analog_triggered.plot()

# %%
# Getting and plotting the extracted peaks.
from FlowCyPy import peak_locator
peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=False)

digital_signal = analog_triggered.digitalize(digitizer=digitizer)

peaks = peak_algorithm.run(digital_signal)

peaks.plot(
    x=('side', 'Height'),
    y=('forward', 'Height')
)

# %%
# Step 8: Classifying the collected dataset
from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=2)

data = classifier.run(
    dataframe=peaks.unstack('Detector'),
    features=['Height'],
    detectors=['side', 'forward']
)

_ = data.plot(
    x=('side', 'Height'),
    y=('forward', 'Height')
)