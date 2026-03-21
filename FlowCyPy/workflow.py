from typing import List
from TypedUnit import (
    Length,
    Power,
    FlowRate,
    Dimensionless,
    Frequency,
    Resistance,
    Time,
)
from FlowCyPy import SimulationSettings  # noqa: F401

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from FlowCyPy.units import ureg
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    distributions,
    populations,
)  # noqa: F401

from FlowCyPy.fluidics.populations import GammaModel, ExplicitModel  # noqa: F401

from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy.opto_electronics.source import Gaussian, FlatTop  # noqa: F401
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    Amplifier,
)

from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    circuits,
    classifier,
    peak_locator,
    discriminator,
)
from FlowCyPy.signal_processing.discriminator import BaseDiscriminator

config_dict = ConfigDict(arbitrary_types_allowed=True, extra="forbid", kw_only=True)


@dataclass(config=config_dict, kw_only=True)
class Workflow:
    # Source parameters
    wavelength: Length
    source: object
    optical_power: Power

    # Flowcell parameters
    sample_volume_flow: FlowRate
    sheath_volume_flow: FlowRate
    width: Length
    height: Length

    # Opto-electronic parameters
    detectors: List[Detector] = None
    bit_depth: int
    use_auto_range: bool = True
    sampling_rate: Frequency
    background_power: Power = 0 * ureg.watt

    # Population parameters
    population_list: List[populations.SpherePopulation] = None
    dilution_factor: float = 1

    # signal processing parameters
    gain: Resistance
    bandwidth: Frequency
    analog_processing: List[object] = None
    peak_locator: peak_locator.BasePeakLocator
    discriminator: discriminator.BaseDiscriminator

    def __post_init__(self):
        if self.analog_processing is None:
            self.analog_processing = []
        if self.detectors is None:
            self.detectors = []

    def _get_fluidics(self) -> Fluidics:
        """
        Get the fluidics components for the workflow.

        Returns
        -------
        Fluidics
        """
        scatterer_collection = ScattererCollection(
            populations=self.population_list,
        )

        scatterer_collection.dilute(self.dilution_factor)

        flow_cell = FlowCell(
            sample_volume_flow=self.sample_volume_flow,
            sheath_volume_flow=self.sheath_volume_flow,
            width=self.width,
            height=self.height,
        )

        return Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

    def _get_opto_electronics(self) -> OptoElectronics:
        """
        Get the opto-electronic components for the workflow.

        Returns
        -------
        OptoElectronics
        """
        amplifier = Amplifier(gain=self.gain, bandwidth=self.bandwidth)

        return OptoElectronics(
            detectors=self.detectors,
            source=self.source,
            amplifier=amplifier,
        )

    def _get_signal_processing(self) -> SignalProcessing:
        """
        Get the signal processing components for the workflow.

        Returns
        -------
        SignalProcessing
        """
        digitizer = Digitizer(
            bit_depth=self.bit_depth,
            sampling_rate=self.sampling_rate,
            use_auto_range=self.use_auto_range,
        )

        return SignalProcessing(
            digitizer=digitizer,
            peak_algorithm=self.peak_locator,
            discriminator=self.discriminator,
            analog_processing=self.analog_processing,
        )

    def initialize(self) -> None:
        """
        Initialize the workflow components.
        """

        self.fluidics = self._get_fluidics()
        self.opto_electronics = self._get_opto_electronics()
        self.signal_processing = self._get_signal_processing()

        self.cytometer = FlowCytometer(
            opto_electronics=self.opto_electronics,
            fluidics=self.fluidics,
            signal_processing=self.signal_processing,
            background_power=self.background_power,
        )

    def run(self, run_time: Time):
        return self.cytometer.run(run_time=run_time)
