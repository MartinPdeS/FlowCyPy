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
from FlowCyPy import units, SimulationSettings
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import ScattererCollection
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy import FlowCytometer, OptoElectronics, Fluidics
from FlowCyPy.calibration import KEstimator
from FlowCyPy.cytometer import FacsCanto


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

np.random.seed(3)  # Reproducibility

# %%
# Construct simulation components
# -------------------------------


flow_cytometer = FacsCanto(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    background_power=0 * units.milliwatt,
    optical_power=200 * units.milliwatt
)

# %%
# Run K Estimation Simulation
# ---------------------------

k_estimator = KEstimator(debug_mode=False)

k_estimator.add_batch(
    bead_diameters=np.linspace(300, 900, 15) * units.nanometer,
    illumination_power=150 * units.milliwatt,
    flow_cytometer=flow_cytometer,
    particle_count=50 * units.particle
)

# %%
# Plot estimation
# ---------------
k_estimator.plot()

# %%
# Plot relevant statistics
# ------------------------
k_estimator.plot_statistics()
