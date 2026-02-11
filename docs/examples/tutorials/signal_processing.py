"""
Signal Processing in Flow Cytometry
=====================================

This example demonstrates how to apply signal processing techniques
to flow cytometry data using FlowCyPy. The simulation is set up with a
Gaussian beam, a flow cell, and two detectors. A single population of scatterers
(with delta distributions) is used, and the focus here is on processing the
forward scatter detector signals. Three acquisitions are performed:

- **Raw Signal:** No processing applied.
- **Baseline Restored:** Using a baseline restorator.
- **Bessel LowPass:** Using a Bessel low-pass filter.

The resulting signals are plotted for comparison.
"""

import matplotlib.pyplot as plt
import numpy as np
from TypedUnit import ureg

from FlowCyPy import FlowCytometer, SimulationSettings
from FlowCyPy.fluidics import distributions

# Import necessary components from FlowCyPy
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    population,
)
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    TransimpedanceAmplifier,
    source,
)
from FlowCyPy.signal_processing import Digitizer, SignalProcessing, circuits

# Enable noise settings if desired
SimulationSettings.include_noises = True

# Set random seed for reproducibility
np.random.seed(3)

# Define the optical source: a Gaussian beam.
source = source.GaussianBeam(
    numerical_aperture=0.3 * ureg.AU,  # Numerical aperture of the laser
    wavelength=488 * ureg.nanometer,  # Laser wavelength: 488 nm
    optical_power=100 * ureg.milliwatt,  # Laser optical power: 100 mW
)

# %%
# Define and plot the flow cell.
flow_cell = FlowCell(
    sample_volume_flow=0.02 * ureg.microliter / ureg.second,
    sheath_volume_flow=0.1 * ureg.microliter / ureg.second,
    width=20 * ureg.micrometer,
    height=10 * ureg.micrometer,
)

# Create a scatterer collection with a single population.
# For signal processing, we use delta distributions (i.e., no variability).
population = population.Sphere(
    name="Population",
    concentration=5e9 * ureg.particle / ureg.milliliter,
    diameter=distributions.Delta(value=150 * ureg.nanometer),
    refractive_index=distributions.Delta(value=1.39 * ureg.RIU),
    medium_refractive_index=1.33 * ureg.RIU,
)
scatterer_collection = ScattererCollection(populations=[population])

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

# Define the signal digitizer.
digitizer = Digitizer(
    bit_depth="14bit",
    saturation_levels="auto",
    sampling_rate=60 * ureg.megahertz,  # Sampling rate: 60 MHz
)

# Define two detectors.
detector_0 = Detector(
    name="side",
    phi_angle=90 * ureg.degree,
    numerical_aperture=0.2 * ureg.AU,
    responsivity=1 * ureg.ampere / ureg.watt,
    dark_current=10 * ureg.microampere,
)

detector_1 = Detector(
    name="forward",
    phi_angle=0 * ureg.degree,
    numerical_aperture=0.2 * ureg.AU,
    responsivity=1 * ureg.ampere / ureg.watt,
    dark_current=1 * ureg.microampere,
)

amplifier = TransimpedanceAmplifier(
    gain=100 * ureg.volt / ureg.ampere, bandwidth=10 * ureg.megahertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_0, detector_1], source=source, amplifier=amplifier
)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=[],
)

# Setup the flow cytometer.
flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=2 * ureg.microwatt,
)

# %%
# ---------------------------------------------------------------------------
# Signal Processing: Acquisition with Different Processing Steps
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(12, 6))
run_time = 0.1 * ureg.millisecond

# Acquisition 1: Raw Signal (no processing)
signal_processing.analog_processing = []
results = flow_cytometer.run(run_time=run_time)
ax.plot(
    results.signal.analog["Time"].pint.to("microsecond"),
    results.signal.analog["forward"].pint.to("millivolt"),
    linestyle="-",
    label="Raw Signal",
)

# Acquisition 2: Baseline Restoration
signal_processing.analog_processing = [
    circuits.BaselineRestorator(window_size=1000 * ureg.microsecond)
]
results = flow_cytometer.run(run_time=run_time)
ax.plot(
    results.signal.analog["Time"].pint.to("microsecond"),
    results.signal.analog["forward"].pint.to("millivolt"),
    linestyle="--",
    label="Baseline Restored",
)

# Acquisition 3: Bessel LowPass Filter
signal_processing.analog_processing = [
    circuits.BesselLowPass(cutoff=3 * ureg.megahertz, order=4, gain=2)
]
results = flow_cytometer.run(run_time=run_time)
ax.plot(
    results.signal.analog["Time"].pint.to("microsecond"),
    results.signal.analog["forward"].pint.to("millivolt"),
    linestyle="-.",
    label="Bessel LowPass",
)

# Configure the plot.
ax.set_title("Flow Cytometry Signal Processing")
ax.set_xlabel("Time [microsecond]")
ax.set_ylabel("Signal Amplitude [millivolt]")
ax.legend()
plt.tight_layout()
plt.show()
