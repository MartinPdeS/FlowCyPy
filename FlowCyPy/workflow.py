import math
from typing import List
import numpy as np
from TypedUnit import (
    Length,
    Power,
    FlowRate,
    Frequency,
    Resistance,
    Time,
)
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from FlowCyPy.units import ureg
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
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
    circuits,
    Digitizer,
)

from FlowCyPy.digital_processing import (
    DigitalProcessing,
    classifier,
    peak_locator,
    discriminator,
)
from FlowCyPy.digital_processing.discriminator import BaseDiscriminator

config_dict = ConfigDict(arbitrary_types_allowed=True, extra="forbid", kw_only=True)


@dataclass(config=config_dict, kw_only=True)
class Workflow:
    """High-level convenience builder for a complete flow cytometry pipeline.

    The workflow groups fluidics, opto-electronics, and digital processing
    configuration into one object so a simulation can be initialized and run
    with a compact, user-facing API.
    """
    # Source configuration. Wavelength and optical power are properties of
    # the source itself and intentionally are not duplicated here.
    source: object

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
        """Normalize optional list-like fields after dataclass construction.

        The workflow accepts ``None`` for list-valued configuration fields so
        callers can omit them. This hook converts those ``None`` values to empty
        lists to simplify downstream initialization logic.
        """
        if self.analog_processing is None:
            self.analog_processing = []
        if self.detectors is None:
            self.detectors = []
        if self.population_list is None:
            self.population_list = []

    def _validate_configuration(self) -> None:
        """Validate configuration before constructing simulation components."""
        if not self.population_list:
            raise ValueError("Workflow requires at least one population.")
        if not self.detectors:
            raise ValueError("Workflow requires at least one detector.")

        self._validate_positive_quantity(
            self.sample_volume_flow, "microliter / second", "sample_volume_flow"
        )
        self._validate_positive_quantity(
            self.sheath_volume_flow, "microliter / second", "sheath_volume_flow"
        )
        self._validate_positive_quantity(self.width, "meter", "width")
        self._validate_positive_quantity(self.height, "meter", "height")
        self._validate_positive_quantity(self.sampling_rate, "hertz", "sampling_rate")
        self._validate_positive_quantity(self.bandwidth, "hertz", "bandwidth")
        self._validate_positive_quantity(self.gain, "volt / ampere", "gain")
        self._validate_positive_quantity(
            self.background_power, "watt", "background_power", allow_zero=True
        )

        if not isinstance(self.bit_depth, int) or isinstance(self.bit_depth, bool):
            raise TypeError("bit_depth must be an integer.")
        if self.bit_depth < 0:
            raise ValueError("bit_depth must be non-negative.")
        if not math.isfinite(self.dilution_factor) or self.dilution_factor <= 0:
            raise ValueError("dilution_factor must be finite and greater than zero.")

        sampling_rate = self.sampling_rate.to("hertz").magnitude
        bandwidth = self.bandwidth.to("hertz").magnitude
        if bandwidth > sampling_rate / 2:
            raise ValueError("bandwidth must not exceed the Nyquist frequency.")

        self._validate_named_objects(self.detectors, "detector")
        self._validate_named_objects(self.population_list, "population")

        if self.source is None:
            raise ValueError("Workflow requires a source.")
        for attribute in ("wavelength", "optical_power"):
            if not hasattr(self.source, attribute):
                raise TypeError(f"source must provide a '{attribute}' property.")
        self._validate_positive_quantity(
            self.source.wavelength, "meter", "source.wavelength"
        )
        self._validate_positive_quantity(
            self.source.optical_power, "watt", "source.optical_power", allow_zero=True
        )

    @staticmethod
    def _validate_positive_quantity(value, unit: str, name: str, *, allow_zero=False):
        """Validate that a scalar quantity is finite and physically positive."""
        try:
            magnitude = float(value.to(unit).magnitude)
        except (AttributeError, TypeError, ValueError) as error:
            message = f"{name} must be a quantity compatible with {unit}."
            raise TypeError(message) from error

        if not math.isfinite(magnitude):
            raise ValueError(f"{name} must be finite.")
        if magnitude < 0 or (magnitude == 0 and not allow_zero):
            qualifier = "non-negative" if allow_zero else "strictly positive"
            raise ValueError(f"{name} must be {qualifier}.")

    @staticmethod
    def _validate_named_objects(objects, object_type: str) -> None:
        """Require non-empty, unique names for channel-like objects."""
        names = []
        for item in objects:
            name = getattr(item, "name", None)
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"Each {object_type} must have a non-empty name.")
            names.append(name)

        if len(names) != len(set(names)):
            raise ValueError(f"{object_type.capitalize()} names must be unique.")

    def _get_fluidics(self) -> Fluidics:
        """
        Get the fluidics components for the workflow.

        Returns
        -------
        Fluidics
        """
        from FlowCyPy.fluidics import ScattererCollection

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

        digitizer = Digitizer(
            bit_depth=self.bit_depth,
            sampling_rate=self.sampling_rate,
            use_auto_range=self.use_auto_range,
        )

        return OptoElectronics(
            analog_processing=self.analog_processing,
            digitizer=digitizer,
            detectors=self.detectors,
            source=self.source,
            amplifier=amplifier,
        )

    def _get_digital_processing(self) -> DigitalProcessing:
        """
        Get the signal processing components for the workflow.

        Returns
        -------
        DigitalProcessing
        """
        return DigitalProcessing(
            peak_algorithm=self.peak_locator,
            discriminator=self.discriminator,
        )

    def initialize(self) -> None:
        """
        Build and attach the configured simulation components.

        This method materializes the fluidics, opto-electronics, digital
        processing, and flow cytometer objects from the dataclass parameters.
        It must be called before :meth:`run`.
        """

        self._validate_configuration()

        self.fluidics = self._get_fluidics()
        self.opto_electronics = self._get_opto_electronics()
        self.digital_processing = self._get_digital_processing()

        self.cytometer = FlowCytometer(
            fluidics=self.fluidics,
            background_power=self.background_power,
        )

    def run(
        self,
        run_time: Time,
        random_state: int | np.random.Generator | None = None,
    ):
        """Execute one simulated acquisition.

        Parameters
        ----------
        run_time : Time
            Duration of the acquisition to simulate.

        Returns
        -------
        RunRecord
            Result object containing the event collection, recorded signals,
            and downstream processing outputs for the run.

        Notes
        -----
        :meth:`initialize` must be called first so the workflow components are
        available.
        """
        if not hasattr(self, "cytometer"):
            raise RuntimeError("Workflow must be initialized before calling run().")

        return self.cytometer.run(
            run_time=run_time,
            opto_electronics=self.opto_electronics,
            digital_processing=self.digital_processing,
            random_state=random_state,
        )
