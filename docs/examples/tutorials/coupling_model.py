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
from FlowCyPy import ScattererCollection, FlowCell
from FlowCyPy._population_instances import Exosome, HDL
from FlowCyPy import GaussianBeam, OptoElectronics, SignalDigitizer, TransimpedanceAmplifier
from FlowCyPy.detector import PMT
from FlowCyPy import Fluidics


source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,
    wavelength=200 * units.nanometer,
    optical_power=20 * units.milliwatt
)

flow_cell = FlowCell(
    sample_volume_flow=0.02 * units.microliter / units.second,
    sheath_volume_flow=0.1 * units.microliter / units.second,
    width=20 * units.micrometer,
    height=10 * units.micrometer,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

# Add an Exosome and HDL population
scatterer_collection.add_population(
    Exosome(particle_count=5e9 * units.particle / units.milliliter),
    HDL(particle_count=5e9 * units.particle / units.milliliter)
)

scatterer_collection.dilute(factor=0.1)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)


event_dataframe = fluidics.generate_event_dataframe(run_time=3.5 * units.millisecond)  # Visualize the particle population

event_dataframe.plot(x='Diameter', bins='auto')

digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = PMT(name='forward', phi_angle=0 * units.degree, numerical_aperture=0.3 * units.AU)

detector_1 = PMT(name='side', phi_angle=90 * units.degree, numerical_aperture=0.3 * units.AU)

amplifier = TransimpedanceAmplifier(
    gain=100 * units.volt / units.ampere,
    bandwidth = 10 * units.megahertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_0, detector_1],
    source=source,
    amplifier=amplifier
)

event_dataframe = opto_electronics.model_event(
    event_dataframe=event_dataframe,
    compute_cross_section=True
)

event_dataframe.plot(
    x='side',
    y='forward',
    z='Csca'
)
