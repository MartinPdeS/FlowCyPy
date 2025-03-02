import numpy as np
from FlowCyPy import FlowCytometer, FlowCell, Source, Scatterer, distribution
from FlowCyPy.units import meter, micrometer, millisecond, second, degree, particle, milliliter, nanometer, RIU, milliwatt, AU, ohm, megahertz, ampere, kelvin, watt
import cProfile

from pathlib import Path


def run():

    np.random.seed(3)

    source = Source(numerical_aperture=0.1 * AU, wavelength=480 * nanometer, optical_power=100 * milliwatt)

    flow_cell = FlowCell(
        flow_speed=7.56 * meter / second,
        flow_area=(10 * micrometer) ** 2,
        run_time=1 * millisecond
    )

    scatterer = Scatterer(medium_refractive_index=1.33 * RIU)

    scatterer.add_population(
        name='LP',
        concentration=1e10 * particle / milliliter,
        size=distribution.RosinRammler(characteristic_size=20 * nanometer, spread=5),
        refractive_index=distribution.Normal(mean=1.46 * RIU, std_dev=0.0001 * RIU)
    )

    scatterer.initialize(flow_cell=flow_cell)

    cytometer = FlowCytometer(source=source, scatterer=scatterer)

    cytometer.add_detector(
        name='forward',                          # Detector name: Forward scatter
        phi_angle=0 * degree,                    # Detector angle: 0 degrees (forward scatter)
        numerical_aperture=1.2 * AU,             # Detector numerical aperture: 1.2
        responsitivity=1 * ampere / watt,        # Responsitivity: 1 A/W (detector response)
        sampling_freq=10 * megahertz,            # Sampling frequency: 60 MHz
        resistance=10_000 * ohm,                 # Resistance: 1 ohm
        temperature=300 * kelvin,                # Operating temperature: 300 K (room temperature)
    )

    # Add side scatter detector
    cytometer.add_detector(
        name='side',                            # Detector name: Side scatter
        phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
        numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
        responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
        sampling_freq=10 * megahertz,           # Sampling frequency: 60 MHz
        resistance=10_000 * ohm,                # Resistance: 1 ohm
        temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    )

    cytometer.simulate_pulse()


profiler = cProfile.Profile()

profiler.enable()

run()

# Stop profiling
profiler.disable()

# Dump the profile data to a file
profiler.dump_stats(Path(__file__).parent / "output_file.prof")
