"""Instrument configurations for BD Biosciences."""

from TypedUnit import FlowRate, Power, Voltage
from FlowCyPy import opto_electronics, digital_processing
from FlowCyPy.detectors.photomultipliers import pmt
from FlowCyPy.fluidics import SampleFlowRate, SheathFlowRate
from FlowCyPy.systems._assembly import ScatterChannel, ScatterSystem, assemble
from FlowCyPy.units import ureg
from FlowCyPy.flow_cytometer import FlowCytometer


def facs_canto(
    *,
    sample_volume_flow: SampleFlowRate | FlowRate = SampleFlowRate.MEDIUM,
    sheath_volume_flow: SheathFlowRate | FlowRate = SheathFlowRate.DEFAULT,
    optical_power: Power = 20 * ureg.milliwatt,
    background_power: Power = 0 * ureg.watt,
    threshold: str | Voltage = "4sigma",
    include_shot_noise: bool = True,
    include_rin_noise: bool = True,
) -> FlowCytometer:
    """Build the original FlowCyPy FACSCanto simulation with editable components.

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
        include_shot_noise=include_shot_noise,
        include_rin_noise=include_rin_noise,
    )

    amplifier = opto_electronics.Amplifier(
        gain=10 * ureg.volt / ureg.ampere,
        bandwidth=2 * ureg.megahertz,
    )

    digitizer = opto_electronics.Digitizer(
        bit_depth=14,
        use_auto_range=True,
        sampling_rate=10 * ureg.megahertz,
    )

    detector_0 = pmt(
        name="forward",
        phi_angle=0 * ureg.degree,
        numerical_aperture=1.2 * ureg.AU,
        dark_current=0 * ureg.picoampere,
    )

    detector_1 = pmt(
        name="side",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.3 * ureg.AU,
        cache_numerical_aperture=0.1 * ureg.AU,
        dark_current=0 * ureg.picoampere,
    )

    analog_processing = [
        opto_electronics.circuits.BaselineRestorationServo(
            time_constant=50 * ureg.microsecond
        ),
        opto_electronics.circuits.BesselLowPass(
            cutoff_frequency=2 * ureg.megahertz, order=4, gain=2
        ),
    ]

    optics = opto_electronics.OptoElectronics(
        detectors=[detector_0, detector_1],
        source=source,
        digitizer=digitizer,
        analog_processing=analog_processing,
        amplifier=amplifier,
    )

    triggering = digital_processing.discriminator.DynamicWindow(
        trigger_channel="forward",
        threshold=threshold,
        pre_buffer=20,
        post_buffer=20,
        max_triggers=-1,
    )

    peak_algo = digital_processing.peak_locator.GlobalPeakLocator(compute_width=False)

    processing = digital_processing.DigitalProcessing(
        discriminator=triggering,
        peak_locator=peak_algo,
    )
    return assemble(
        sample_volume_flow=sample_volume_flow,
        sheath_volume_flow=sheath_volume_flow,
        opto_electronics=optics,
        digital_processing=processing,
        background_power=background_power,
    )


facs_calibur = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_canto_i = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_canto_ii = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=800,
            phi_angle=90.0 * ureg.degree,
        ),
        ScatterChannel(
            name="FSC",
            numerical_aperture=0.18,
            sampling=600,
            phi_angle=0.0 * ureg.degree,
            cache_numerical_aperture=0.1,
        ),
    ),
)


facs_lyric = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=800,
            phi_angle=90.0 * ureg.degree,
        ),
        ScatterChannel(
            name="FSC",
            numerical_aperture=0.18,
            sampling=600,
            phi_angle=0.0 * ureg.degree,
            cache_numerical_aperture=0.1,
        ),
    ),
)


facsymphony_a1 = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=800,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


lsr_fortessa = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


lsr_ii = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_aria = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_aria_ii = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_celesta = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_melody = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facs_verse = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)


facsymphony = ScatterSystem(
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


lsr = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(
        ScatterChannel(
            name="SSC",
            numerical_aperture=1.2,
            sampling=900,
            phi_angle=90.0 * ureg.degree,
        ),
    ),
)
