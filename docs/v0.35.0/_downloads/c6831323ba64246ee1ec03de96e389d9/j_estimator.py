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
from TypedUnit import ureg

from FlowCyPy import FlowCytometer, SimulationSettings
from FlowCyPy.calibration import JEstimator
from FlowCyPy.fluidics import FlowCell, Fluidics, ScattererCollection
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    TransimpedanceAmplifier,
    source,
)
from FlowCyPy.signal_processing import Digitizer, SignalProcessing

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

scatterer_collection = ScattererCollection()

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

source = source.GaussianBeam(
    numerical_aperture=0.2 * ureg.AU,
    wavelength=450 * ureg.nanometer,
    optical_power=0 * ureg.watt,
)

digitizer = Digitizer(
    bit_depth="16bit",
    saturation_levels=(0 * ureg.volt, 2 * ureg.volt),
    sampling_rate=60 * ureg.megahertz,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=60 * ureg.megahertz,
)

detector_0 = Detector(
    name="default",
    phi_angle=0 * ureg.degree,  # Forward scatter
    numerical_aperture=0.2 * ureg.AU,
    cache_numerical_aperture=0.0 * ureg.AU,
    responsivity=1 * ureg.ampere / ureg.watt,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0], source=source, amplifier=amplifier
)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=[],
)

flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=source.optical_power * 0.001,
)

# %%
# Run J Estimation Simulation
# ---------------------------

j_estimator = JEstimator(debug_mode=False)

j_estimator.add_batch(
    illumination_powers=np.linspace(10, 380, 25) * ureg.milliwatt,
    bead_diameter=400 * ureg.nanometer,
    flow_cytometer=flow_cytometer,
    concentration=2.5e7 * ureg.particle / ureg.milliliter,
)

# %%
# Plot estimation and diagnostics
# -------------------------------

j_estimator.plot()


# %%
# Plot relevant statistics
# ------------------------
j_estimator.plot_statistics()
