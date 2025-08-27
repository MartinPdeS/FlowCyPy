"""
Limit of detection
==================
"""

import numpy as np
from FlowCyPy import units
from FlowCyPy import SimulationSettings
from FlowCyPy.population import Sphere
from FlowCyPy import distribution
from FlowCyPy import peak_locator
from FlowCyPy.triggering_system import DynamicWindow
from FlowCyPy import circuits
from FlowCyPy.cytometer import FacsCanto

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True

SimulationSettings.sorted_population = True
SimulationSettings.evenly_spaced_events = True
np.random.seed(3)

flow_cytometer = FacsCanto(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    background_power=0 * units.milliwatt,
    optical_power=200 * units.milliwatt,
    saturation_level=0.1 * units.millivolt
)

for size in [150, 130, 110, 90]:

    population = Sphere(
        name=f'{size} nanometer',
        particle_count=20 * units.particle,
        diameter=distribution.Delta(position=size * units.nanometer),
        refractive_index=distribution.Delta(position=1.39 * units.RIU)
    )

    flow_cytometer.fluidics.scatterer_collection.add_population(population)

# Run the flow cytometry simulation
processing_steps = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=1 * units.megahertz, order=4, gain=2)
]

analog_acquisition, _ = flow_cytometer.get_acquisition(
    run_time=2.0 * units.millisecond,
    processing_steps=processing_steps
)

# %%
# Run triggering system
analog_acquisition.normalize_units(signal_units='max', time_units='max')
analog_acquisition.plot()

trigger = DynamicWindow(
    dataframe=analog_acquisition,
    trigger_detector_name='forward',
    max_triggers=-1,
    pre_buffer=64,
    post_buffer=64,
    digitizer=flow_cytometer.opto_electronics.digitizer
)

analog_trigger = trigger.run(
    # threshold=0.4 * units.millivolt,
    threshold='3sigma'
)

# %%
# Visualize the analog trigger signals
analog_trigger.plot()

digital_trigger = analog_trigger.digitalize(digitizer=flow_cytometer.opto_electronics.digitizer)


# %%
# Visualize the digital acquisition signals
digital_trigger.plot()

peak_algorithm = peak_locator.GlobalPeakLocator()

peaks = peak_algorithm.run(digital_trigger)

# %%
# Visualize the detected peaks
peaks.plot(
    x=('side', 'Height'),
    y=('forward', 'Height')
)
