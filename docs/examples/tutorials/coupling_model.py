"""
Flow Cytometry Workflow: Single Population Example
==================================================

This tutorial demonstrates a basic flow cytometry simulation using the FlowCyPy library.

The example covers the configuration of:
- A fluidic channel with hydrodynamic focusing
- A synthetic particle population (Exosome + HDL)
- A laser source and dual-detector optical system
- Scattering intensity calculation per detector

The resulting data are visualized using event-based plots.

Workflow Steps:
---------------
1. Define laser source and flow cell geometry
2. Add synthetic particle populations
3. Model optical scattering with two detectors
4. Visualize population and scattering response
"""

# %%
# Step 0: Imports and Setup
# --------------------------

from TypedUnit import ureg

from FlowCyPy import OptoElectronics
from FlowCyPy.instances.detector import PMT
from FlowCyPy.instances.population import Exosome
from FlowCyPy.fluidics import FlowCell, Fluidics, ScattererCollection
from FlowCyPy.opto_electronics import TransimpedanceAmplifier, source
from FlowCyPy.signal_processing import Digitizer

# %%
# Step 1: Define Optical Source
# -----------------------------
laser = source.GaussianBeam(
    numerical_aperture=0.3 * ureg.AU,
    wavelength=750 * ureg.nanometer,
    optical_power=20 * ureg.milliwatt,
)

# %%
# Step 2: Configure Flow Cell and Fluidics
# ----------------------------------------
flow_cell = FlowCell(
    sample_volume_flow=0.02 * ureg.microliter / ureg.second,
    sheath_volume_flow=0.1 * ureg.microliter / ureg.second,
    width=20 * ureg.micrometer,
    height=10 * ureg.micrometer,
)

scatterer_collection = ScattererCollection()

# Add Exosome and HDL populations
scatterer_collection.add_population(
    Exosome(particle_count=5e10 * ureg.particle / ureg.milliliter),
)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

# %%
# Step 3: Generate Particle Event DataFrame
# -----------------------------------------
event_frame = fluidics.generate_event_frame(run_time=3.5 * ureg.millisecond)

# Plot the diameter distribution of the particles
event_frame.plot(x="Diameter", bins="auto")

# %%
# Step 4: Define Detectors and Amplifier
# --------------------------------------
detector_forward = PMT(
    name="forward", phi_angle=0 * ureg.degree, numerical_aperture=0.3 * ureg.AU
)

detector_side = PMT(
    name="side", phi_angle=90 * ureg.degree, numerical_aperture=0.3 * ureg.AU
)

amplifier = TransimpedanceAmplifier(
    gain=100 * ureg.volt / ureg.ampere, bandwidth=10 * ureg.megahertz
)

# %%
# Step 5: Configure Digitizer and Opto-Electronics
# ------------------------------------------------
digitizer = Digitizer(
    bit_depth="14bit", saturation_levels="auto", sampling_rate=60 * ureg.megahertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_forward, detector_side], source=laser, amplifier=amplifier
)

# %%
# Step 6: Model Scattering Signals
# --------------------------------
opto_electronics.add_model_to_event_frame(
    event_frame=event_frame, compute_cross_section=True
)

# %%
# Step 7: Visualize Scattering Intensity
# --------------------------------------
event_frame.plot(x="side", y="Csca")  # Color-coded by scattering cross-section
