"""
J Estimator Validation — Fixed Bead Size, Variable Illumination
=================================================================

This example demonstrates how to estimate the `J` parameter, which quantifies
how the relative noise (robust coefficient of variation) scales with the
signal strength under varying illumination power. We simulate a flow cytometry
system with fixed bead diameter and varying illumination.

"""

# %%
# Setup and configuration
# -----------------------

import numpy as np
from FlowCyPy.fluidics import Fluidics, FlowCell, ScattererCollection
from FlowCyPy.opto_electronics import OptoElectronics, source, TransimpedanceAmplifier, Detector
from FlowCyPy.signal_processing import SignalProcessing, Digitizer
from FlowCyPy import FlowCytometer, SimulationSettings, units

from FlowCyPy.calibration import JEstimator

# %%
# Configure simulation-level noise assumptions

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_dark_current_noise = False
SimulationSettings.include_source_noise = False
SimulationSettings.include_amplifier_noise = False
SimulationSettings.assume_perfect_hydrodynamic_focusing = True
SimulationSettings.assume_amplifier_bandwidth_is_infinite = True
SimulationSettings.assume_perfect_digitizer = True
SimulationSettings.evenly_spaced_events = True


np.random.seed(3)  # Reproducibility

# %%
# Construct simulation components
# -------------------------------

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=400 * units.micrometer,
    height=400 * units.micrometer,

)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

source = source.GaussianBeam(
    numerical_aperture=0.2 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=0 * units.watt
)

digitizer = Digitizer(
    bit_depth='16bit',
    saturation_levels=(0 * units.volt, 2 * units.volt),
    sampling_rate=60 * units.megahertz,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=60 * units.megahertz,
)

detector_0 = Detector(
    name='default',
    phi_angle=0 * units.degree,  # Forward scatter
    numerical_aperture=0.2 * units.AU,
    cache_numerical_aperture=0.0 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0],
    source=source,
    amplifier=amplifier
)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=[],
)

flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=source.optical_power * 0.001
)

# %%
# Run J Estimation Simulation
# ---------------------------

j_estimator = JEstimator(debug_mode=False)

j_estimator.add_batch(
    illumination_powers=np.linspace(10, 380, 25) * units.milliwatt,
    bead_diameter=400 * units.nanometer,
    flow_cytometer=flow_cytometer,
    particle_count=50 * units.particle
)

# %%
# Plot estimation and diagnostics
# -------------------------------

j_estimator.plot()


# %%
# Plot relevant statistics
# ------------------------
j_estimator.plot_statistics()
