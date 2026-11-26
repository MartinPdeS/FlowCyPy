"""Instrument configurations for Cytek."""

from TypedUnit import FlowRate, Power, Voltage
from FlowCyPy import opto_electronics, digital_processing
from FlowCyPy.fluidics import SampleFlowRate, SheathFlowRate
from FlowCyPy.systems._assembly import ScatterChannel, ScatterSystem, assemble
from FlowCyPy.units import ureg
from FlowCyPy.flow_cytometer import FlowCytometer


def reference(
    *,
    sample_volume_flow: SampleFlowRate | FlowRate = SampleFlowRate.MEDIUM,
    sheath_volume_flow: SheathFlowRate | FlowRate = SheathFlowRate.DEFAULT,
    optical_power: Power = 20 * ureg.milliwatt,
    background_power: Power = 0 * ureg.watt,
    threshold: str | Voltage = "4sigma",
    include_shot_noise: bool = True,
    include_rin_noise: bool = True,
) -> FlowCytometer:
    """Build the original FlowCyPy Cytek simulation with editable components.

    Parameters
    ----------
    sample_volume_flow, sheath_volume_flow : FlowRate or flow-rate preset
        Volumetric flow rates through the reference cell.
    optical_power, background_power : Power
        Laser power and constant background optical power for each channel.
    threshold : str or voltage quantity
        Trigger expression or absolute detector voltage.
    include_shot_noise, include_rin_noise : bool
        Enable the source's shot noise and relative intensity noise settings.

    Returns
    -------
    FlowCytometer
        A fresh acquisition chain and an empty sample collection.
    """
    source = opto_electronics.source.Gaussian(
        waist_y=65 * ureg.micrometer,
        waist_z=10 * ureg.micrometer,
        wavelength=488 * ureg.nanometer,
        optical_power=optical_power,
        bandwidth=10 * ureg.megahertz,
        include_shot_noise=include_shot_noise,
        include_rin_noise=include_rin_noise,
        rin=-250 * ureg.dB_per_Hz,
    )

    amplifier = opto_electronics.Amplifier(
        gain=1 * ureg.volt / ureg.ampere,
        bandwidth=2 * ureg.megahertz,
    )

    digitizer = opto_electronics.Digitizer(
        sampling_rate=10 * ureg.megahertz,
        bit_depth=22,
        use_auto_range=False,
        output_signed_codes=True,
        channel_range_mode="shared",
    )

    # Fixed signed ranges used in FlowCyPy's Cytek bead comparison.
    digitizer.set_channel_voltage_range("FSC", -3 * ureg.microvolt, 3 * ureg.microvolt)
    digitizer.set_channel_voltage_range(
        "SSC", -16 * ureg.microvolt, 16 * ureg.microvolt
    )

    detector_0 = opto_electronics.Detector(
        name="FSC",
        phi_angle=0 * ureg.degree,
        numerical_aperture=1.1,
        bandwidth=10 * ureg.megahertz,
        dark_current=0 * ureg.picoampere,
        current_noise_density=300 * ureg.femtoampere / ureg.sqrt_hertz,
    )

    detector_1 = opto_electronics.Detector(
        name="SSC",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.1,
        cache_numerical_aperture=0.04,
        bandwidth=10 * ureg.megahertz,
        dark_current=0 * ureg.picoampere,
        current_noise_density=20 * ureg.femtoampere / ureg.sqrt_hertz,
    )

    analog_processing = [
        opto_electronics.circuits.BesselLowPass(
            cutoff_frequency=1 * ureg.megahertz, order=4, gain=2
        ),
        opto_electronics.circuits.BaselineRestorationServo(
            time_constant=20 * ureg.microsecond, initialize_with_first_sample=False
        ),
    ]

    optics = opto_electronics.OptoElectronics(
        detectors=[detector_0, detector_1],
        source=source,
        digitizer=digitizer,
        analog_processing=analog_processing,
        amplifier=amplifier,
    )

    discriminator = digital_processing.discriminator.DynamicWindow(
        trigger_channel="SSC",
        threshold=threshold,
        pre_buffer=2,
        post_buffer=2,
        max_triggers=-1,
    )

    peak_algo = digital_processing.peak_locator.GlobalPeakLocator(
        compute_width=False,
        compute_area=True,
        allow_negative_area=True,
        support=digital_processing.peak_locator.FullWindowSupport(),
        polarity="positive",
        height_mode="peak_to_baseline",
        baseline_mode="zero",
    )

    processing = digital_processing.DigitalProcessing(
        discriminator=discriminator,
        peak_locator=peak_algo,
    )
    return assemble(
        sample_volume_flow=sample_volume_flow,
        sheath_volume_flow=sheath_volume_flow,
        opto_electronics=optics,
        digital_processing=processing,
        background_power=background_power,
    )


aurora = ScatterSystem(
    wavelength=405 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
        ScatterChannel(
            name="FSC",
            numerical_aperture=0.16,
            sampling=700,
            phi_angle=0.0 * ureg.degree,
            cache_numerical_aperture=0.08,
        ),
    ),
)


northern_lights = ScatterSystem(
    wavelength=405 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


imagestream_60x = ScatterSystem(
    wavelength=405 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=0.9,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


cellstream_60x = ScatterSystem(
    wavelength=785 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=0.9,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)
