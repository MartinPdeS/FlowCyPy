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
import numpy as np
from FlowCyPy import units
from FlowCyPy.opto_electronics import source, TransimpedanceAmplifier
from FlowCyPy.fluidics import Fluidics, FlowCell, ScattererCollection, population
from FlowCyPy.detector import PMT
from FlowCyPy.signal_processing import Digitizer
from FlowCyPy import OptoElectronics

# %%
# Step 1: Define Optical Source
# -----------------------------
laser = source.GaussianBeam(
    numerical_aperture=0.3 * units.AU,
    wavelength=750 * units.nanometer,
    optical_power=20 * units.milliwatt
)

# %%
# Step 2: Configure Flow Cell and Fluidics
# ----------------------------------------
flow_cell = FlowCell(
    sample_volume_flow=0.02 * units.microliter / units.second,
    sheath_volume_flow=0.1 * units.microliter / units.second,
    width=20 * units.micrometer,
    height=10 * units.micrometer
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

# Add Exosome and HDL populations
scatterer_collection.add_population(
    population.Exosome(particle_count=5e10 * units.particle / units.milliliter),
)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

# %%
# Step 3: Generate Particle Event DataFrame
# -----------------------------------------
event_dataframe = fluidics.generate_event_dataframe(run_time=3.5 * units.millisecond)

# Plot the diameter distribution of the particles
event_dataframe.plot(x='Diameter', bins='auto')

# %%
# Step 4: Define Detectors and Amplifier
# --------------------------------------
detector_forward = PMT(
    name='forward',
    phi_angle=0 * units.degree,
    numerical_aperture=0.3 * units.AU
)

detector_side = PMT(
    name='side',
    phi_angle=90 * units.degree,
    numerical_aperture=0.3 * units.AU
)

amplifier = TransimpedanceAmplifier(
    gain=100 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz
)

# %%
# Step 5: Configure Digitizer and Opto-Electronics
# ------------------------------------------------
digitizer = Digitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_forward, detector_side],
    source=laser,
    amplifier=amplifier
)

# %%
# Step 6: Model Scattering Signals
# --------------------------------
event_dataframe = opto_electronics.model_event(
    event_dataframe=event_dataframe,
    compute_cross_section=True
)

# %%
# Step 7: Visualize Scattering Intensity
# --------------------------------------
event_dataframe.plot(
    x='side',
    y='Csca'  # Color-coded by scattering cross-section
)
