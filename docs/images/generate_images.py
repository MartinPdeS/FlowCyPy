import os

import numpy as np
from TypedUnit import ureg

from FlowCyPy import FlowCytometer, SimulationSettings
from FlowCyPy.classifier import KmeansClassifier
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.fluidics import Fluidics, ScattererCollection, distribution, population
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    TransimpedanceAmplifier,
    source,
)
from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    circuits,
    peak_locator,
    triggering_system,
)

current_directory = os.path.dirname(os.path.realpath(__file__))

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_amplifier_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True

np.random.seed(3)

flow_cell = FlowCell(
    sample_volume_flow=80 * ureg.microliter / ureg.minute,
    sheath_volume_flow=1 * ureg.milliliter / ureg.minute,
    width=200 * ureg.micrometer,
    height=100 * ureg.micrometer,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * ureg.RIU)

population_0 = population.Sphere(
    name="Population: 150nm",
    particle_count=5e9 * ureg.particle / ureg.milliliter,
    diameter=distribution.RosinRammler(150 * ureg.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * ureg.RIU, std_dev=0.002 * ureg.RIU),
)

population_1 = population.Sphere(
    name="Population: 200nm",
    particle_count=5e9 * ureg.particle / ureg.milliliter,
    diameter=distribution.RosinRammler(200 * ureg.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * ureg.RIU, std_dev=0.002 * ureg.RIU),
)

scatterer_collection.add_population(population_0, population_1)

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

# figure = fluidics.plot(
#     run_time=0.5 * ureg.millisecond,
#     save_as=f'{current_directory}/example_fluidics.png',
#     show=False
# )

event_df = fluidics.generate_event_dataframe(run_time=0.5 * ureg.millisecond)

event_df.plot(
    x="RefractiveIndex",
    y="Diameter",
    save_as=f"{current_directory}/example_scatterers.png",
    show=False,
)

source = source.GaussianBeam(
    numerical_aperture=0.1 * ureg.AU,
    wavelength=450 * ureg.nanometer,
    optical_power=200 * ureg.milliwatt,
    RIN=-140,
)

detectors = [
    Detector(
        name="forward",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.3 * ureg.AU,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
    Detector(
        name="side",
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.3 * ureg.AU,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
]

amplifier = TransimpedanceAmplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=10 * ureg.megahertz,
    voltage_noise_density=0.1 * ureg.nanovolt / ureg.sqrt_hertz,
    current_noise_density=0.2 * ureg.femtoampere / ureg.sqrt_hertz,
)

opto_electronics = OptoElectronics(
    detectors=detectors, source=source, amplifier=amplifier
)


digitizer = Digitizer(
    bit_depth="14bit", saturation_levels="auto", sampling_rate=60 * ureg.megahertz
)

# analog_processing = [
#     circuits.BaselineRestorator(window_size=10 * ureg.microsecond),
#     circuits.BesselLowPass(cutoff=2 * ureg.megahertz, order=4, gain=2)
# ]

# triggering = triggering_system.DynamicWindow(
#     trigger_detector_name='forward',
#     threshold=10 * ureg.microvolt,
#     pre_buffer=20,
#     post_buffer=20,
#     max_triggers=-1
# )

# peak_algo = peak_locator.GlobalPeakLocator(compute_width=False)

# signal_processing = SignalProcessing(
#     digitizer=digitizer,
#     analog_processing=analog_processing,
#     triggering_system=triggering,
#     peak_algorithm=peak_algo
# )


# cytometer = FlowCytometer(
#     opto_electronics=opto_electronics,
#     fluidics=fluidics,
#     signal_processing=signal_processing,
#     background_power=0.001 * ureg.milliwatt
# )

# results = cytometer.run(run_time=1.8 * ureg.millisecond)
# _ = results.events.plot(x='side', y='forward', z='RefractiveIndex')


# results.analog.normalize_units(signal_units='max')
# _ = results.analog.plot()

# _ = results.triggered_analog.plot()


# classifier = KmeansClassifier(number_of_cluster=2)

# classified = classifier.run(
#     dataframe=results.peaks.unstack('Detector'),
#     features=['Height'],
#     detectors=['side', 'forward']
# )

# _ = classified.plot(
#     x=('side', 'Height'),
#     y=('forward', 'Height')
# )
