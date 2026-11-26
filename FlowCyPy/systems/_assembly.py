"""Common acquisition settings for the instrument factories."""

from dataclasses import dataclass
from TypedUnit import Angle, FlowRate, Length, Power, Voltage
from FlowCyPy.digital_processing import DigitalProcessing, discriminator, peak_locator
from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    SampleFlowRate,
    ScattererCollection,
    SheathFlowRate,
)
from FlowCyPy.opto_electronics import (
    Amplifier,
    Detector,
    Digitizer,
    OptoElectronics,
    source,
)
from FlowCyPy.units import ureg


def assemble(
    *,
    sample_volume_flow: SampleFlowRate | FlowRate,
    sheath_volume_flow: SheathFlowRate | FlowRate,
    opto_electronics: OptoElectronics,
    digital_processing: DigitalProcessing,
    background_power: Power,
) -> FlowCytometer:
    """Attach the acquisition chain to a fresh sample in the reference flow cell."""
    cell = FlowCell(
        sample_volume_flow=sample_volume_flow.value
        if isinstance(sample_volume_flow, SampleFlowRate)
        else sample_volume_flow,
        sheath_volume_flow=sheath_volume_flow.value
        if isinstance(sheath_volume_flow, SheathFlowRate)
        else sheath_volume_flow,
        width=177 * ureg.micrometer,
        height=433 * ureg.micrometer,
    )
    return FlowCytometer(
        fluidics=Fluidics(flow_cell=cell, scatterer_collection=ScattererCollection()),
        opto_electronics=opto_electronics,
        digital_processing=digital_processing,
        background_power=background_power,
    )


@dataclass(frozen=True, kw_only=True)
class ScatterChannel:
    """Define the collection geometry of one scatter channel.

    Parameters
    ----------
    name : str
        Channel label used in acquisition results and trigger selection.
    numerical_aperture, cache_numerical_aperture : float
        Outer collection aperture and central obscuration aperture.
    sampling : int
        Number of samples used for angular integration.
    phi_angle, gamma_angle : Angle
        Angular offsets of the detector in the scattering calculation.
    """

    name: str
    numerical_aperture: float
    sampling: int
    phi_angle: Angle
    cache_numerical_aperture: float = 0.0
    gamma_angle: Angle = 0 * ureg.degree

    def build(self) -> Detector:
        """Construct a detector with this geometry and FlowCyPy's default electrical response."""
        return Detector(
            name=self.name,
            numerical_aperture=self.numerical_aperture,
            cache_numerical_aperture=self.cache_numerical_aperture,
            sampling=self.sampling,
            phi_angle=self.phi_angle,
            gamma_angle=self.gamma_angle,
        )


@dataclass(frozen=True, kw_only=True)
class ScatterSystem:
    """Single-laser scattering model using RosettaX geometry and reference electronics.

    Parameters
    ----------
    wavelength : Length
        Laser wavelength for all configured channels.
    channels : tuple of ScatterChannel
        Collection geometry for each detector. The first channel triggers acquisition.
    """

    wavelength: Length
    channels: tuple[ScatterChannel, ...]

    def __post_init__(self) -> None:
        """Require at least one collection channel for triggering."""
        if not self.channels:
            raise ValueError(
                "A scattering system requires at least one detector channel."
            )

    def __call__(
        self,
        *,
        optical_power: Power = 20 * ureg.milliwatt,
        sample_volume_flow: SampleFlowRate | FlowRate = SampleFlowRate.MEDIUM,
        sheath_volume_flow: SheathFlowRate | FlowRate = SheathFlowRate.DEFAULT,
        background_power: Power = 0 * ureg.watt,
        threshold: str | Voltage = "4sigma",
    ) -> FlowCytometer:
        """Create an editable scattering instrument with an empty sample.

        Parameters
        ----------
        optical_power, background_power : Power
            Incident laser power and constant optical background per detector.
        sample_volume_flow, sheath_volume_flow : FlowRate or flow-rate preset
            Sample and sheath volumetric flow rates.
        threshold : str or voltage quantity
            Trigger expression or absolute detector voltage.

        Returns
        -------
        FlowCytometer
            Independent fluidics, optics and processing components.
        """
        optics = OptoElectronics(
            detectors=[channel.build() for channel in self.channels],
            source=source.Gaussian(
                wavelength=self.wavelength,
                optical_power=optical_power,
                waist_y=65 * ureg.micrometer,
                waist_z=10 * ureg.micrometer,
            ),
            amplifier=Amplifier(
                gain=10 * ureg.volt / ureg.ampere, bandwidth=2 * ureg.megahertz
            ),
            digitizer=Digitizer(
                sampling_rate=10 * ureg.megahertz, bit_depth=14, use_auto_range=True
            ),
        )
        processing = DigitalProcessing(
            discriminator=discriminator.DynamicWindow(
                trigger_channel=self.channels[0].name,
                threshold=threshold,
                pre_buffer=20,
                post_buffer=20,
            ),
            peak_locator=peak_locator.GlobalPeakLocator(),
        )
        return assemble(
            sample_volume_flow=sample_volume_flow,
            sheath_volume_flow=sheath_volume_flow,
            opto_electronics=optics,
            digital_processing=processing,
            background_power=background_power,
        )
