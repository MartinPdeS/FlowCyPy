"""
K Estimator Validation — Fixed Illumination, Variable Bead Size
=================================================================

This example demonstrates how to estimate the `K` parameter, which characterizes
how the **absolute signal noise** (Robust STD) scales with the **square root of the median signal**
when varying bead size under fixed illumination power.

"""

# %%
# Setup and configuration
# -----------------------

import numpy as np
from FlowCyPy import units, NoiseSetting
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import ScattererCollection
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy import FlowCytometer, OptoElectronics, Fluidics
from FlowCyPy.calibration import KEstimator

# %%
# Configure simulation-level noise assumptions

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_source_noise = False
NoiseSetting.include_amplifier_noise = False
NoiseSetting.assume_perfect_hydrodynamic_focusing = True
NoiseSetting.assume_amplifier_bandwidth_is_infinite = True
NoiseSetting.assume_perfect_digitizer = True

np.random.seed(3)  # Reproducibility

# %%
# Construct simulation components
# -------------------------------

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=400 * units.micrometer,
    height=400 * units.micrometer,
    event_scheme='sequential-uniform'
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

source = GaussianBeam(
    numerical_aperture=0.2 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=150 * units.milliwatt  # Fixed illumination power
)

digitizer = SignalDigitizer(
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
    phi_angle=0 * units.degree,
    numerical_aperture=0.2 * units.AU,
    cache_numerical_aperture=0.0 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0],
    digitizer=digitizer,
    source=source,
    amplifier=amplifier
)

flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    background_power=source.optical_power * 0.001
)

# %%
# Run K Estimation Simulation
# ---------------------------

k_estimator = KEstimator(debug_mode=False)

k_estimator.add_batch(
    bead_diameters=np.linspace(300, 900, 15) * units.nanometer,
    illumination_power=source.optical_power,
    flow_cytometer=flow_cytometer,
    particle_count=50 * units.particle
)

# %%
# Plot estimation and diagnostics
# -------------------------------

k_estimator.plot()
k_estimator.plot_statistics()
