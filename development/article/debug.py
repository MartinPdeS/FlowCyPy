from TypedUnit import ureg
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    populations,
    SampleFlowRate,
    SheathFlowRate,
)
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    Amplifier,
    source,
    Digitizer,
)
from FlowCyPy.signal_processing import (
    SignalProcessing,
    circuits,
    peak_locator,
    discriminator,
)
from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import distributions

flow_cell = FlowCell(
    sample_volume_flow=SampleFlowRate.MEDIUM.value,
    sheath_volume_flow=SheathFlowRate.MEDIUM.value,
    width=400 * ureg.micrometer,
    height=150 * ureg.micrometer,
)

scatterer_collection = ScattererCollection()

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

digitizer = Digitizer(
    sampling_rate=10 * ureg.megahertz,
    bit_depth=16,
    use_auto_range=True,
    output_signed_codes=True,
    # min_voltage=10 * ureg.microvolt,
    # max_voltage=50 * ureg.microvolt
)

source = source.Gaussian(
    waist_z=10e-6 * ureg.meter,  # Beam waist along flow direction (z-axis)
    waist_y=60e-6 * ureg.meter,
    wavelength=405 * ureg.nanometer,
    optical_power=200 * ureg.milliwatt,
    bandwidth=10 * ureg.megahertz,
    # rin=-110 * ureg.dB_per_Hz,
)

detectors = [
    Detector(
        name="SSC",
        phi_angle=90 * ureg.degree,
        numerical_aperture=1.1,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
    Detector(
        name="FSC",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.3,
        cache_numerical_aperture=0.1,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
]

amplifier = Amplifier(
    gain=1 * ureg.volt / ureg.ampere,
    bandwidth=2 * ureg.megahertz,
    voltage_noise_density=0.05 * ureg.nanovolt / ureg.sqrt_hertz * 2,
    # current_noise_density=0.05 * ureg.femtoampere / ureg.sqrt_hertz,
)

opto_electronics = OptoElectronics(
    detectors=detectors,
    source=source,
    amplifier=amplifier,
    digitizer=digitizer,
)


analog_processing = [
    circuits.BesselLowPass(cutoff_frequency=1.4 * ureg.megahertz, order=4, gain=2),
    circuits.BaselineRestorationServo(time_constant=3 * ureg.microsecond),
    # circuits.BaselineRestorator(window_size=2 * ureg.microsecond),
]

triggering = discriminator.FixedWindow(
    trigger_channel="SSC",
    threshold="2sigma",
    # threshold=2000 * ureg.microvolt,
    pre_buffer=10,
    post_buffer=10,
    max_triggers=-1,
)

peak_algo = peak_locator.GlobalPeakLocator(
    compute_width=False,
    compute_area=True,
    debug_mode=True,
    allow_negative_area=True,
    support=peak_locator.PulseSupport(channel="SSC", threshold=0.5),
)

signal_processing = SignalProcessing(
    analog_processing=analog_processing,
    discriminator=triggering,
    peak_algorithm=peak_algo,
)

cytometer = FlowCytometer(
    fluidics=fluidics,
    background_power=0.01 * ureg.milliwatt,
)

run_record = cytometer.run(
    run_time=0.9 * ureg.millisecond,
    signal_processing=signal_processing,
    opto_electronics=opto_electronics,
)

print("Done")

run_record.peaks.unstack("Detector")["Area", "SSC"].hist(bins=200)

import pandas as pd

df = pd.DataFrame(run_record.peaks.unstack("Detector"))
df.plot.scatter(x=("Area", "SSC"), y=("Area", "FSC"))
import matplotlib.pyplot as plt

plt.show()
