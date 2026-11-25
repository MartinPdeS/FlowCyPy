import math
from copy import copy
from typing import Self
import numpy as np
from pydantic import ConfigDict, validate_call
from TypedUnit import (
    FlowRate,
    Frequency,
    Length,
    Power,
    Resistance,
    Time,
)

# Convenience exports used by the documented workflow examples.
from FlowCyPy.digital_processing import (
    DigitalProcessing,
    classifier,  # noqa: F401
    discriminator,  # noqa: F401
    peak_locator,  # noqa: F401
)
from FlowCyPy.digital_processing.discriminator import BaseDiscriminator
from FlowCyPy.digital_processing.peak_locator import BasePeakLocator
from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    distributions,  # noqa: F401
    populations,
)
from FlowCyPy.fluidics.populations import ExplicitModel, GammaModel  # noqa: F401
from FlowCyPy.opto_electronics import (
    Amplifier,
    Detector,
    Digitizer,
    OptoElectronics,
    circuits,  # noqa: F401
)
from FlowCyPy.opto_electronics.source import FlatTop, Gaussian  # noqa: F401
from FlowCyPy.run_record import RunRecord
from FlowCyPy.units import ureg

config_dict = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class Workflow:
    """High-level convenience builder for a complete flow cytometry pipeline.

    The workflow groups fluidics, opto-electronics, and digital processing
    configuration into one object so a simulation can be initialized and run
    with a compact, user-facing API. Use the keyword constructor to build from
    settings, or use from_components to keep and edit assembled subsystems.
    """

    @validate_call(config=config_dict)
    def __init__(
        self,
        *,
        source: object,
        sample_volume_flow: FlowRate,
        sheath_volume_flow: FlowRate,
        width: Length,
        height: Length,
        bit_depth: int,
        sampling_rate: Frequency,
        gain: Resistance,
        bandwidth: Frequency,
        detectors: list[Detector] | None = None,
        use_auto_range: bool = True,
        background_power: Power = 0 * ureg.watt,
        population_list: list[populations.SpherePopulation] | None = None,
        dilution_factor: float = 1,
        analog_processing: list[object] | None = None,
        peak_locator: BasePeakLocator | None = None,
        discriminator: BaseDiscriminator | None = None,
    ):
        """Store acquisition settings for initialization on the first run."""
        self.source = source
        self.sample_volume_flow = sample_volume_flow
        self.sheath_volume_flow = sheath_volume_flow
        self.width = width
        self.height = height
        self.bit_depth = bit_depth
        self.sampling_rate = sampling_rate
        self.gain = gain
        self.bandwidth = bandwidth
        self.detectors = detectors if detectors is not None else []
        self.use_auto_range = use_auto_range
        self.background_power = background_power
        self.population_list = population_list if population_list is not None else []
        self.dilution_factor = dilution_factor
        self.analog_processing = (
            analog_processing if analog_processing is not None else []
        )
        self.peak_locator = peak_locator
        self.discriminator = discriminator
        self._uses_components = False

    @classmethod
    @validate_call(config=config_dict)
    def from_components(
        cls,
        *,
        fluidics: Fluidics,
        opto_electronics: OptoElectronics,
        digital_processing: DigitalProcessing,
        background_power: Power = 0 * ureg.watt,
    ) -> Self:
        """Assemble a workflow using the supplied live components.

        Parameters
        ----------
        fluidics : Fluidics
            Flow cell and sample collection. Populations can be added after assembly.
        opto_electronics : OptoElectronics
            Source, detector channels, amplifier, digitizer and analog circuits.
        digital_processing : DigitalProcessing
            Trigger and peak measurement settings.
        background_power : Power, optional
            Constant optical background for each detector, convertible to watts.

        Returns
        -------
        Workflow
            A ready-to-use workflow. Edits to its components apply to the next run.
        """
        workflow = cls.__new__(cls)
        workflow._uses_components = True
        workflow.fluidics = fluidics
        workflow.opto_electronics = opto_electronics
        workflow.digital_processing = digital_processing
        workflow.background_power = background_power
        workflow.initialize()
        return workflow

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

        if self.bandwidth > self.sampling_rate / 2:
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
        scatterer_collection = ScattererCollection(
            populations=[copy(population) for population in self.population_list],
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
            peak_locator=self.peak_locator,
            discriminator=self.discriminator,
        )

    def initialize(self) -> None:
        """
        Build and attach the configured simulation components.

        For a workflow constructed from settings, call this after editing those
        settings to rebuild the subsystems. For a workflow built with
        from_components, this reattaches the existing subsystems.
        """

        if self._uses_components:
            self._validate_positive_quantity(
                self.background_power, "watt", "background_power", allow_zero=True
            )
        else:
            self._validate_configuration()
            self.fluidics = self._get_fluidics()
            self.opto_electronics = self._get_opto_electronics()
            self.digital_processing = self._get_digital_processing()

        self.cytometer = FlowCytometer(
            fluidics=self.fluidics,
            background_power=self.background_power,
        )

    def acquire(
        self,
        *,
        run_time: Time,
        random_state: int | np.random.Generator | None = None,
    ) -> RunRecord:
        """Acquire analog waveforms, initializing the workflow on first use.

        Parameters
        ----------
        run_time : Time
            Duration of the acquisition.
        random_state : int or numpy.random.Generator, optional
            Seed or advancing random stream, as for :meth:`run`.

        Returns
        -------
        RunRecord
            Particle events and analog voltages, ready for repeated processing.
        """
        if not hasattr(self, "cytometer"):
            self.initialize()
        if self._uses_components:
            collection = self.fluidics.scatterer_collection
            if not collection.populations:
                raise ValueError("Workflow requires at least one population.")
            self._validate_named_objects(collection.populations, "population")
            self._validate_positive_quantity(
                self.background_power, "watt", "background_power", allow_zero=True
            )
            self.cytometer.fluidics = self.fluidics
            self.cytometer.background_power = self.background_power
        return self.cytometer.acquire(
            run_time=run_time,
            opto_electronics=self.opto_electronics,
            random_state=random_state,
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

        random_state : int or numpy.random.Generator, optional
            A non-negative integer repeats the events and noisy signals with the
            same build and OpenMP worker count. A generator advances each run.

        Returns
        -------
        RunRecord
            Result object containing the event collection, recorded signals,
            and downstream processing outputs for the run.

        Notes
        -----
        The first run initializes the workflow automatically. Call
        :meth:`initialize` to rebuild it after editing configuration settings.
        """
        acquisition = self.acquire(run_time=run_time, random_state=random_state)
        return acquisition.process(digital_processing=self.digital_processing)
