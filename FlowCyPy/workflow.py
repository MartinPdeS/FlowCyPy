from typing import List

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from FlowCyPy import distribution, units
from FlowCyPy.circuits import SignalProcessor
from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy.fluidics import FlowCell, Fluidics, ScattererCollection
from FlowCyPy.opto_electronics import (
    Detector,
    GaussianBeam,
    OptoElectronics,
    TransimpedanceAmplifier,
)
from FlowCyPy.peak_locator.base_class import BasePeakLocator
from FlowCyPy.population import Sphere
from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    circuits,
    peak_locator,
    triggering_system,
)
from FlowCyPy.triggering_system import BaseTrigger

config_dict = ConfigDict(arbitrary_types_allowed=True, extra="forbid", kw_only=True)


@dataclass(config=config_dict, kw_only=True)
class Workflow:
    # Source parameters
    wavelength: units.Quantity
    source_numerical_aperture: units.Quantity
    optical_power: units.Quantity

    # Flowcell parameters
    sample_volume_flow: units.Quantity
    sheath_volume_flow: units.Quantity
    width: units.Quantity
    height: units.Quantity

    # Opto-electronic parameters
    detectors: List[Detector] = None
    bit_depth: str
    saturation_levels: str
    sampling_rate: units.Quantity
    background_power: units.Quantity = 0 * units.watt

    # Population parameters
    populations: List[Sphere]
    medium_refractive_index: units.Quantity

    # signal processing parameters
    gain: units.Quantity
    bandwidth: units.Quantity
    analog_processing: List[SignalProcessor] = None
    peak_locator: BasePeakLocator
    trigger: BaseTrigger

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
            medium_refractive_index=self.medium_refractive_index,
            populations=self.populations,
        )

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
        source = GaussianBeam(
            numerical_aperture=self.source_numerical_aperture,
            wavelength=self.wavelength,
            optical_power=self.optical_power,
        )

        amplifier = TransimpedanceAmplifier(gain=self.gain, bandwidth=self.bandwidth)

        return OptoElectronics(
            detectors=self.detectors,
            source=source,
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
            saturation_levels=self.saturation_levels,
        )

        return SignalProcessing(
            digitizer=digitizer,
            peak_algorithm=self.peak_locator,
            triggering_system=self.trigger,
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

    def run(self, run_time: units.Quantity):
        self.results = self.cytometer.run(run_time=run_time)
