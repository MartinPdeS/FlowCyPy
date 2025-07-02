"""
Limit of detection
==================
"""

import numpy as np
from FlowCyPy import units
from FlowCyPy import NoiseSetting
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import ScattererCollection
from FlowCyPy.population import Sphere
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy import OptoElectronics, Fluidics
from FlowCyPy import FlowCytometer, circuits

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_source_noise = False
NoiseSetting.include_dark_current_noise = False
NoiseSetting.assume_perfect_hydrodynamic_focusing = True

np.random.seed(3)


bead_diameter = 200 * units.nanometer
illumination_power = 120 * units.milliwatt

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=600 * units.micrometer,
    height=600 * units.micrometer,
    event_scheme='sequential-uniform'
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

particle_count = 5 * units.particle

population_0 = Sphere(
    name='population',
    particle_count=particle_count,
    diameter=bead_diameter,
    refractive_index=1.47 * units.RIU
)

scatterer_collection.add_population(population_0)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

source = GaussianBeam(
    numerical_aperture=0.1 * units.AU,           # Numerical aperture
    wavelength=450 * units.nanometer,           # Wavelength
    optical_power=illumination_power,          # Optical power
)

digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=10 * units.megahertz,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=60 * units.megahertz,
)

detector_0 = Detector(
    name='default',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=0.2 * units.AU,
    cache_numerical_aperture=0. * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0],
    digitizer=digitizer,
    source=source,
    amplifier=amplifier
)

cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
)


analog, event_df = cytometer.get_acquisition(
    run_time=1.3 * units.millisecond,
    compute_cross_section=True
)

figure = analog.plot()
