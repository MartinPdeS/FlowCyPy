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
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.noises import NoiseSetting
from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, Sphere, distribution
from FlowCyPy import FlowCytometer, circuits


NoiseSetting.include_noises = True
NoiseSetting.assume_perfect_hydrodynamic_focusing = True

source = GaussianBeam(
    numerical_aperture=0.1 * units.AU,           # Numerical aperture
    wavelength=450 * units.nanometer,           # Wavelength
    optical_power=200 * units.milliwatt,          # Optical power
    RIN=-140
)

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=100 * units.micrometer,
    height=100 * units.micrometer,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

spread_factor = 1

population_0 = Sphere(
    name='Population: 100nm',
    particle_count=100 * units.particle,
    # diameter=150 * units.nanometer,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=30 * spread_factor),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.02 * units.RIU)
)

population_1 = Sphere(
    name='Population: 50nm',
    particle_count=100 * units.particle,
    # diameter=50 * units.nanometer,
    diameter=distribution.RosinRammler(characteristic_property=50 * units.nanometer, spread=30 * spread_factor),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.02 * units.RIU)
)

population_2 = Sphere(
    name='Population: 150nm',
    particle_count=100 * units.particle,
    # diameter=100 * units.nanometer,
    diameter=distribution.RosinRammler(characteristic_property=100 * units.nanometer, spread=30 * spread_factor),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.02 * units.RIU)
)

scatterer_collection.add_population(population_0, population_1, population_2)

scatterer_collection.dilute(factor=2)

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=0.7 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=0.7 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)


amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz,
    voltage_noise_density=.01 * units.nanovolt / units.sqrt_hertz,
    current_noise_density=.02 * units.femtoampere / units.sqrt_hertz
)

cytometer = FlowCytometer(
    source=source,
    transimpedance_amplifier=amplifier,
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell,
    background_power=0.000 * units.milliwatt
)

processing_steps = [
    circuits.BaselineRestorator(window_size=100 * units.microsecond),
    circuits.BesselLowPass(cutoff=1 * units.megahertz, order=4, gain=2)
]

cytometer.prepare_acquisition(run_time=2 * units.millisecond)

acquisition = cytometer.get_acquisition(processing_steps=processing_steps)

acquisition.scatterer.plot(x='Diameter', y='RefractiveIndex')
acquisition.scatterer.plot(x='forward', y='side')

acquisition.analog.plot()

# window size and threshold.
triggered_acquisition = acquisition.run_triggering(
    threshold=0.1 * units.microvolt,
    trigger_detector_name='forward',
    max_triggers=-1,
    pre_buffer=20,
    post_buffer=20
)

triggered_acquisition.analog.plot()


# %%
# Getting and plotting the extracted peaks.
from FlowCyPy import peak_locator
peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=False)


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