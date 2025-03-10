"""
Workflow
========

This tutorial demonstrates how to simulate a flow cytometry experiment using the FlowCyPy library.
The simulation involves configuring a flow setup, defining a single population of particles, and
analyzing scattering signals from two detectors to produce a 2D density plot of scattering intensities.

Overview:
---------
1. Configure the flow cell and particle population.
2. Define the laser source and detector parameters.
3. Simulate the flow cytometry experiment.
4. Analyze the generated signals and visualize results.

"""

# %%
# Step 0: Import Necessary Libraries
# -----------------------------------
# Here, we import the necessary libraries and units for the simulation. The units module helps us
# define physical quantities like meters, seconds, and watts in a concise and consistent manner.

from FlowCyPy import units
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import CircularFlowCell
from FlowCyPy import ScattererCollection
from FlowCyPy.population import CoreShell, Sphere
from FlowCyPy import distribution
from FlowCyPy.detector import PMT
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import FlowCytometer

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,           # Numerical aperture
    wavelength=200 * units.nanometer,           # Wavelength
    optical_power=200 * units.milliwatt          # Optical power
)


flow_cell = CircularFlowCell(
    volume_flow=0.3 * units.microliter / units.second,  # Flow volume
    radius=10 * units.micrometer,       # Cross-sectional area
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

population_0 = CoreShell(
    name=f'coreshell',
    particle_count=20 * units.particle,
    core_diameter=distribution.Delta(position=100 * units.nanometer),
    core_refractive_index=distribution.Normal(mean=1.39 * units.RIU, std_dev=0.02 * units.RIU),
    shell_thickness=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=30),
    shell_refractive_index=distribution.Normal(mean=1.43 * units.RIU, std_dev=0.02 * units.RIU),
)

population_1 = Sphere(
    name=f'sphere',
    particle_count=20 * units.particle,
    diameter=distribution.Delta(position=100 * units.nanometer),
    refractive_index=distribution.Normal(mean=1.39 * units.RIU, std_dev=0.02 * units.RIU),
)

# Add an Exosome and HDL population
scatterer_collection.add_population(
    population_0, population_1
    # Exosome(particle_count=5e9 * units.particle / units.milliliter),
    # HDL(particle_count=5e9 * units.particle / units.milliliter)
)

scatterer_collection.dilute(factor=1)

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=10 * units.megahertz,
)

detector_0 = PMT(name='forward', cache_numerical_aperture=0.0 * units.AU, phi_angle=0 * units.degree, numerical_aperture=0.3 * units.AU)

detector_1 = PMT(name='side', phi_angle=90 * units.degree, numerical_aperture=0.3 * units.AU)

cytometer = FlowCytometer(
    source=source,
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell,
    background_power=0.001 * units.milliwatt
)

# Run the flow cytometry simulation
cytometer.prepare_acquisition(run_time=1 * units.millisecond)

cytometer.scatterer_dataframe.plot(
    x='ShellThickness',
    y='CoreRefractiveIndex'
)

cytometer.scatterer_dataframe.plot(
    x='side',
    y='forward',
    # log_scale=True
#     z='RefractiveIndex'
)
