"""
J-Estimator Calibration Example
===============================

This example demonstrates how to simulate a noise-aware calibration procedure using the `JEstimator` in FlowCyPy.
The goal is to estimate the system's noise factor (J) by simulating flow cytometry experiments at different
illumination powers for a fixed bead size.

Workflow:
---------
1. Define noise model assumptions
2. Build fluidic and optical subsystems
3. Configure the cytometer and estimator
4. Simulate experiments across illumination powers
5. Plot J-estimation results
"""

# %%
# Step 0: Imports and Global Settings
# -----------------------------------
import numpy as np

from FlowCyPy import NoiseSetting, units

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
# Step 1: Define the Flow Cell and Fluidics
# -----------------------------------------
from FlowCyPy import Fluidics, ScattererCollection
from FlowCyPy.flow_cell import FlowCell

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=400 * units.micrometer,
    height=400 * units.micrometer,
    event_scheme="sequential-uniform",
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

# %%
# Step 2: Define the Laser Source
# -------------------------------
from FlowCyPy import GaussianBeam

source = GaussianBeam(
    numerical_aperture=0.2 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=0 * units.watt,  # Overridden during batch simulations
)

# %%
# Step 3: Configure the Detectors and Electronics
# -----------------------------------------------
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy.detector import Detector
from FlowCyPy.digitizer import SignalDigitizer

digitizer = SignalDigitizer(
    bit_depth="16bit",
    saturation_levels=(0 * units.volt, 2 * units.volt),
    sampling_rate=60 * units.megahertz,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere, bandwidth=60 * units.megahertz
)

detector_0 = Detector(
    name="default",
    phi_angle=0 * units.degree,  # Forward scatter
    numerical_aperture=0.2 * units.AU,
    cache_numerical_aperture=0.0 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

# %%
# Step 4: Assemble the Cytometer
# ------------------------------
from FlowCyPy import FlowCytometer, OptoElectronics

opto_electronics = OptoElectronics(
    detectors=[detector_0], digitizer=digitizer, source=source, amplifier=amplifier
)

flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    background_power=source.optical_power * 0.00,
)

# %%
# Step 5: Run the J-Estimator
# ---------------------------
from FlowCyPy.calibration import JEstimator

j_estimator = JEstimator(debug_mode=False)

j_estimator.add_batch(
    illumination_powers=np.linspace(10, 280, 45) * units.milliwatt,
    bead_diameter=400 * units.nanometer,
    flow_cytometer=flow_cytometer,
    particle_count=50 * units.particle,
)

j_estimator.plot()
