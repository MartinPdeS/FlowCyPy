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

from FlowCyPy import FlowCytometer
from FlowCyPy.calibration import JEstimator
from FlowCyPy.fluidics import FlowCell, Fluidics, ScattererCollection
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    Amplifier,
    source,
)
from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    peak_locator,
    discriminator,
)

np.random.seed(3)  # Reproducibility

# %%
# Construct simulation components
# -------------------------------

flow_cell = FlowCell(
    sample_volume_flow=80 * ureg.microliter / ureg.minute,
    sheath_volume_flow=1 * ureg.milliliter / ureg.minute,
    width=400 * ureg.micrometer,
    height=400 * ureg.micrometer,
    event_scheme="linear",
    perfectly_aligned=True,
)

scatterer_collection = ScattererCollection()

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

source = source.FlatTop(
    waist_z=10 * ureg.micrometer,
    waist_y=60 * ureg.micrometer,
    wavelength=450 * ureg.nanometer,
    optical_power=0 * ureg.watt,
    include_shot_noise=False,
    include_rin_noise=False,
)

digitizer = Digitizer(
    bit_depth=16,
    use_auto_range=True,
    sampling_rate=60 * ureg.megahertz,
)

amplifier = Amplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=60 * ureg.megahertz,
    voltage_noise_density=0 * ureg.volt / (ureg.sqrt_hertz),
    current_noise_density=0 * ureg.ampere / (ureg.sqrt_hertz),
)

detector_0 = Detector(
    name="default",
    phi_angle=0 * ureg.degree,  # Forward scatter
    numerical_aperture=0.2,
    cache_numerical_aperture=0.0,
    responsivity=1 * ureg.ampere / ureg.watt,
    dark_current=0 * ureg.ampere,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0], source=source, amplifier=amplifier
)

peak_algorithm = peak_locator.GlobalPeakLocator()

discriminator = discriminator.FixedWindow(
    trigger_channel="default",
    threshold=400 * ureg.nanovolt,
)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=[],
    peak_algorithm=peak_algorithm,
    discriminator=discriminator,
)

flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=source.optical_power * 0.00,
)

# %%
# Run J Estimation Simulation
# ---------------------------
j_estimator = JEstimator(debug_mode=True)

j_estimator.add_batch(
    illumination_powers=np.linspace(10, 380, 25) * ureg.milliwatt,
    bead_diameter=400 * ureg.nanometer,
    flow_cytometer=flow_cytometer,
    concentration=2.5e7 * ureg.particle / ureg.milliliter / 3,
)

# %%
# Plot estimation and diagnostics
# -------------------------------

j_estimator.plot()


# %%
# Plot relevant statistics
# ------------------------
j_estimator.plot_statistics()
