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
from TypedUnit import ureg

from FlowCyPy.fluidics import Fluidics, FlowCell, ScattererCollection
from FlowCyPy.opto_electronics import OptoElectronics, source, TransimpedanceAmplifier, Detector
from FlowCyPy.signal_processing import SignalProcessing, Digitizer
from FlowCyPy import FlowCytometer, SimulationSettings
from FlowCyPy.calibration import KEstimator

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
    sample_volume_flow=80 * ureg.microliter / ureg.minute,
    sheath_volume_flow=1 * ureg.milliliter / ureg.minute,
    width=400 * ureg.micrometer,
    height=400 * ureg.micrometer,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * ureg.RIU)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

_source = source.GaussianBeam(
    numerical_aperture=0.2 * ureg.AU,
    wavelength=450 * ureg.nanometer,
    optical_power=150 * ureg.milliwatt  # Fixed illumination power
)

digitizer = Digitizer(
    bit_depth='16bit',
    saturation_levels=(0 * ureg.volt, 2 * ureg.volt),
    sampling_rate=60 * ureg.megahertz,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=60 * ureg.megahertz,
)

detector_0 = Detector(
    name='default',
    phi_angle=0 * ureg.degree,
    numerical_aperture=0.2 * ureg.AU,
    cache_numerical_aperture=0.0 * ureg.AU,
    responsivity=1 * ureg.ampere / ureg.watt,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0],
    source=_source,
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
    background_power=_source.optical_power * 0.001
)


# %%
# Run K Estimation Simulation
# ---------------------------

k_estimator = KEstimator(debug_mode=False)

k_estimator.add_batch(
    bead_diameters=np.linspace(300, 900, 15) * ureg.nanometer,
    illumination_power=_source.optical_power,
    flow_cytometer=flow_cytometer,
    particle_count=50 * ureg.particle
)

# %%
# Plot estimation
# ---------------
k_estimator.plot()

# %%
# Plot relevant statistics
# ------------------------
k_estimator.plot_statistics()
