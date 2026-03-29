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
from TypedUnit import ureg

from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import distributions

from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    populations,
)
from FlowCyPy.opto_electronics import (
    Detector,
    Digitizer,
    circuits,
    OptoElectronics,
    Amplifier,
    source,
)

from FlowCyPy.digital_processing import DigitalProcessing

source = source.Gaussian(
    waist_z=10 * ureg.micrometer,
    waist_y=60 * ureg.micrometer,
    wavelength=488 * ureg.nanometer,
    optical_power=100 * ureg.milliwatt,
    bandwidth=10 * ureg.megahertz,
    rin=-100 * ureg.dB_per_Hz,
)

# %%
# Define and plot the flow cell.
flow_cell = FlowCell(
    sample_volume_flow=0.02 * ureg.microliter / ureg.second,
    sheath_volume_flow=0.1 * ureg.microliter / ureg.second,
    width=20 * ureg.micrometer,
    height=10 * ureg.micrometer,
)

# Create a scatterer collection with a single populations.
# For signal processing, we use delta distributions (i.e., no variability).
population = populations.SpherePopulation(
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
    bit_depth=14,
    use_auto_range=True,
    sampling_rate=60 * ureg.megahertz,
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

amplifier = Amplifier(gain=100 * ureg.volt / ureg.ampere, bandwidth=10 * ureg.megahertz)

opto_electronics = OptoElectronics(
    detectors=[detector_0, detector_1],
    source=source,
    amplifier=amplifier,
    digitizer=digitizer,
    analog_processing=[],
)

# Setup the flow cytometer.
flow_cytometer = FlowCytometer(
    fluidics=fluidics,
    background_power=2 * ureg.microwatt,
)

# %%
# ---------------------------------------------------------------------------
# Signal Processing: Acquisition with Different Processing Steps
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(12, 6))
run_time = 0.1 * ureg.millisecond

# Acquisition 1: Raw Signal (no processing)
opto_electronics.analog_processing = []
run_record = flow_cytometer.run(
    run_time=run_time,
    opto_electronics=opto_electronics,
)
ax.plot(
    run_record.signal.analog["Time"].to("microsecond"),
    run_record.signal.analog["forward"].to("millivolt"),
    linestyle="-",
    label="Raw Signal",
)

# Acquisition 2: Baseline Restoration
opto_electronics.analog_processing = [
    circuits.BaselineRestorationServo(time_constant=10 * ureg.microsecond)
]
run_record = flow_cytometer.run(
    run_time=run_time,
    opto_electronics=opto_electronics,
)
ax.plot(
    run_record.signal.analog["Time"].to("microsecond"),
    run_record.signal.analog["forward"].to("millivolt"),
    linestyle="--",
    label="Baseline Restored",
)

# Acquisition 3: Bessel LowPass Filter
opto_electronics.analog_processing = [
    circuits.BesselLowPass(cutoff_frequency=3 * ureg.megahertz, order=4, gain=2)
]
run_record = flow_cytometer.run(
    run_time=run_time,
    opto_electronics=opto_electronics,
)
ax.plot(
    run_record.signal.analog["Time"].to("microsecond"),
    run_record.signal.analog["forward"].to("millivolt"),
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
