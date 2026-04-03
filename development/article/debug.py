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
    circuits,
)
from FlowCyPy.digital_processing import DigitalProcessing, peak_locator, discriminator
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
        responsivity=1 * ureg.ampere / ureg.watt / 2,
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
    voltage_noise_density=0.05 * ureg.nanovolt / ureg.sqrt_hertz,
    # current_noise_density=0.05 * ureg.femtoampere / ureg.sqrt_hertz,
)

digitizer = Digitizer(
    sampling_rate=10 * ureg.megahertz,
    bit_depth=12,
    use_auto_range=True,
    output_signed_codes=True,
    # min_voltage=10 * ureg.microvolt,
    # max_voltage=50 * ureg.microvolt
)


analog_processing = [
    circuits.BesselLowPass(cutoff_frequency=4 * ureg.megahertz, order=4, gain=2),
    circuits.BaselineRestorationServo(time_constant=3 * ureg.microsecond),
    # circuits.BaselineRestorator(window_size=2 * ureg.microsecond),
]

opto_electronics = OptoElectronics(
    analog_processing=analog_processing,
    detectors=detectors,
    digitizer=digitizer,
    source=source,
    amplifier=amplifier,
)

cytometer = FlowCytometer(
    fluidics=fluidics,
    background_power=0.01 * ureg.milliwatt,
)

print("done")

run_record = cytometer.acquire(
    run_time=30 * ureg.millisecond, opto_electronics=opto_electronics
)

triggering = discriminator.DynamicWindow(
    trigger_channel="SSC",
    # threshold="2sigma",
    threshold=200 * ureg.nanovolt,
    pre_buffer=20,
    post_buffer=20,
    max_triggers=-1,
)

peak_algo = peak_locator.GlobalPeakLocator(
    compute_width=False,
    compute_area=True,
    allow_negative_area=True,
    support=peak_locator.PulseSupport(channel="SSC"),
    # support=peak_locator.FullWindowSupport(),
    # debug_mode=True
)

digital_processing = DigitalProcessing(
    discriminator=triggering,
    peak_algorithm=peak_algo,
)

run_record = cytometer.process_run(
    run_record=run_record,
    digital_processing=digital_processing,
)

run_record.peaks.plot(y=("SSC", "Area"), x=("FSC", "Area"))
