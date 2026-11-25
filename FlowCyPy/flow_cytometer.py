import math
import numpy as np
from TypedUnit import Power, Time, ureg, validate_units
from FlowCyPy.digital_processing import DigitalProcessing
from FlowCyPy.fluidics import Fluidics, populations
from FlowCyPy.fluidics.event_collection import EventCollection
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.opto_electronics.system import _next_noise_seed
from FlowCyPy.run_record import RunRecord
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame


class FlowCytometer:
    """
    High level orchestrator for the flow cytometry simulation pipeline.

    This class keeps only the persistent fluidic definition and the constant
    optical background level. All other configuration objects are passed
    explicitly to the methods that use them.

    This design keeps the workflow fully visible to the caller and avoids any
    ambiguity about which opto electronic or signal processing configuration is
    active for a given computation.

    Parameters
    ----------
    fluidics : Fluidics
        Fluidic subsystem, including flow cell and population definitions.
    background_power : pint.Quantity, optional
        Constant optical background added to every detector channel.
    """

    @validate_units
    def __init__(
        self,
        fluidics: Fluidics,
        background_power: Power | None = 0 * ureg.milliwatt,
    ):
        self.fluidics = fluidics
        self.background_power = background_power

    def _add_explicit_model_signals(
        self,
        event_collection: EventCollection,
        signal_dict: dict,
        opto_electronics: OptoElectronics,
    ) -> None:
        """
        Add explicit model detector signals to the optical power dictionary.

        Parameters
        ----------
        event_collection : EventCollection
            Population event blocks.
        signal_dict : dict
            Uniform sample times under "Time" and one optical power array per
            detector, all of shape (n_samples,). Detector powers are incremented
            in place.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        """
        sample_times = signal_dict["Time"]
        if sample_times.size == 0:
            return

        if sample_times.size == 1:
            acquisition_window = sample_times[0]
        else:
            sample_interval = sample_times[1] - sample_times[0]
            acquisition_window = sample_times[-1] - sample_times[0] + sample_interval

        for events in event_collection:
            if events.empty or not isinstance(
                events.sampling_method, populations.ExplicitModel
            ):
                continue

            event_times = events.get_quantity("Time")
            velocities = events.get_quantity("Velocity")
            support_margin = 4 * opto_electronics.source.get_particle_width(velocities)

            # A pulse within four widths of an edge also contributes on the
            # opposite side of the periodic acquisition window.
            late_events = np.flatnonzero(
                event_times >= acquisition_window - support_margin
            )
            early_events = np.flatnonzero(event_times < support_margin)
            pulse_centers = np.concatenate(
                (
                    event_times[late_events] - acquisition_window,
                    event_times,
                    event_times[early_events] + acquisition_window,
                )
            )
            event_indices = np.concatenate(
                (late_events, np.arange(event_times.size), early_events)
            )
            pulse_velocities = velocities[event_indices]

            for detector in opto_electronics.detectors:
                amplitudes = events.get_quantity(detector.name)
                signal_dict[detector.name] += opto_electronics.source.generate_pulses(
                    velocities=pulse_velocities,
                    pulse_centers=pulse_centers,
                    pulse_amplitudes=amplitudes[event_indices],
                    time_array=sample_times,
                    base_level=0 * ureg.watt,
                )

    def _add_gamma_model_signals(
        self,
        event_collection: EventCollection,
        signal_dict: dict,
        opto_electronics: OptoElectronics,
        *,
        random_generator: np.random.Generator | None = None,
    ) -> None:
        """
        Add gamma model detector signals to the optical power dictionary.

        Parameters
        ----------
        event_collection : EventCollection
            Population event blocks.
        signal_dict : dict
            Optical power signal dictionary updated in place.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        random_generator : numpy.random.Generator, optional
            Random stream for analog signal generation.
        """
        for events in event_collection:
            if not isinstance(events.sampling_method, populations.GammaModel):
                continue

            if events.empty:
                continue

            expected_number_of_particles = events.metadata["ExpectedNumberOfParticles"]

            if expected_number_of_particles == 0:
                continue

            if len(opto_electronics.detectors) == 0:
                raise ValueError("opto_electronics must contain at least one detector.")

            reference_detector = opto_electronics.detectors[0]

            reference_mean_amplitude = events.get_quantity(
                reference_detector.name
            ).mean()

            reference_power_trace = opto_electronics.source.get_gamma_trace(
                time_array=signal_dict["Time"],
                shape=expected_number_of_particles,
                scale=reference_mean_amplitude,
                mean_velocity=events.metadata["VelocityMean"],
                seed=_next_noise_seed(generator=random_generator),
            )

            if reference_mean_amplitude == 0 * ureg.watt:
                raise ValueError(
                    "Gamma Model reference mean amplitude is zero, cannot normalize."
                )

            particle_trace = reference_power_trace / reference_mean_amplitude

            events.metadata["ParticleTrace"] = particle_trace
            events.metadata["TimeTrace"] = signal_dict["Time"]

            for detector in opto_electronics.detectors:
                mean_amplitude = events.get_quantity(detector.name).mean()
                detector_power_trace = particle_trace * mean_amplitude
                signal_dict[detector.name] += detector_power_trace

    def compute_analog(
        self,
        run_time: Time,
        event_collection: EventCollection,
        opto_electronics: OptoElectronics,
        *,
        random_generator: np.random.Generator | None = None,
    ) -> dict:
        """
        Compute the full analog detector waveforms from an event collection.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        event_collection : EventCollection
            Population event blocks with optical coupling already evaluated.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        random_generator : numpy.random.Generator, optional
            Random stream for analog signal generation.

        Returns
        -------
        dict
            Analog voltage signal dictionary.
        """
        self._validate_run_time(run_time)
        power_signal_dict = opto_electronics.initialize_optical_signal_dict(
            run_time=run_time,
            background_power=self.background_power,
        )

        self._add_explicit_model_signals(
            event_collection=event_collection,
            signal_dict=power_signal_dict,
            opto_electronics=opto_electronics,
        )

        gamma_rng, noise_rng = (
            random_generator.spawn(2) if random_generator is not None else (None, None)
        )
        self._add_gamma_model_signals(
            event_collection=event_collection,
            signal_dict=power_signal_dict,
            opto_electronics=opto_electronics,
            random_generator=gamma_rng,
        )

        return opto_electronics.convert_optical_power_to_voltage(
            power_signal_dict, random_generator=noise_rng
        )

    def process_analog(
        self,
        run_time: Time,
        event_collection: EventCollection,
        analog_dict: dict,
        digital_processing: DigitalProcessing,
        opto_electronics: OptoElectronics,
    ) -> RunRecord:
        """
        Process an existing analog acquisition through the downstream signal
        processing chain.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        event_collection : EventCollection
            Event collection associated with the analog signals.
        analog_dict : dict
            Analog voltage signal dictionary.
        digital_processing : DigitalProcessing
            Signal processing configuration.
        opto_electronics : OptoElectronics
            Opto electronic configuration associated with the analog signal.

        Returns
        -------
        RunRecord
            Run record containing the analog acquisition and all downstream
            results that could be computed.
        """
        acquisition = RunRecord(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
        )
        processed = opto_electronics.apply_analog_processing(analog_dict=analog_dict)
        return acquisition._process_filtered(
            analog=AcquisitionDataFrame._construct_from_signal_dict(processed),
            digital_processing=digital_processing,
        )

    def acquire(
        self,
        run_time: Time,
        opto_electronics: OptoElectronics,
        random_state: int | np.random.Generator | None = None,
    ) -> RunRecord:
        """
        Run the acquisition pipeline up to the analog stage.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.

        random_state : int or numpy.random.Generator, optional
            A non-negative integer repeats the events and noisy signals with the
            same build and OpenMP worker count. A generator advances each run.

        Returns
        -------
        RunRecord
            Run record containing the event collection, analog voltage
            waveforms, and the opto electronic configuration used to produce
            them.
        """
        self._validate_run_time(run_time)
        self._validate_opto_electronics(opto_electronics)
        if isinstance(random_state, np.random.Generator):
            random_state = int(random_state.integers(0, np.iinfo(np.uint32).max))
        event_collection = self.fluidics.generate_event_collection(
            run_time=run_time,
            sampling_rate=opto_electronics.digitizer.sampling_rate,
            random_state=random_state,
        )

        opto_electronics.add_coupling_to_dataframe(
            event_collection=event_collection,
            compute_cross_section=False,
        )

        processed_analog_dict = self.compute_analog(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
            random_generator=(
                np.random.default_rng(random_state) if random_state is not None else None
            ),
        )

        run_record = RunRecord(
            run_time=run_time,
            event_collection=event_collection,
            opto_electronics=opto_electronics,
        )

        run_record.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(
            signal_dict=processed_analog_dict,
        )

        return run_record

    @staticmethod
    def _validate_run_time(run_time: Time) -> None:
        """Reject empty, negative, non-finite, or unitless run durations."""
        try:
            seconds = float(run_time.to("second").magnitude)
        except (AttributeError, TypeError, ValueError) as error:
            raise TypeError("run_time must be a time quantity.") from error

        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("run_time must be finite and strictly positive.")

    @staticmethod
    def _validate_opto_electronics(opto_electronics: OptoElectronics) -> None:
        """Validate detector channels before starting an acquisition."""
        detectors = getattr(opto_electronics, "detectors", None)
        if not detectors:
            raise ValueError("opto_electronics must contain at least one detector.")

        names = [getattr(detector, "name", None) for detector in detectors]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Each detector must have a non-empty name.")
        if len(names) != len(set(names)):
            raise ValueError("Detector names must be unique.")

    def run(
        self,
        run_time: Time,
        opto_electronics: OptoElectronics,
        digital_processing: DigitalProcessing | None = None,
        random_state: int | np.random.Generator | None = None,
    ) -> RunRecord:
        """
        Run the full simulation pipeline from event generation to peak extraction.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics
            Opto electronic configuration.
        digital_processing : DigitalProcessing, optional
            Signal processing configuration. If None, no digital processing is applied.

        random_state : int or numpy.random.Generator, optional
            A non-negative integer repeats the events and noisy signals with the
            same build and OpenMP worker count. A generator advances each run.

        Returns
        -------
        RunRecord
            Full run record containing all available stages.
        """
        if digital_processing is None:
            digital_processing = DigitalProcessing()

        acquired_run_record = self.acquire(
            run_time=run_time,
            opto_electronics=opto_electronics,
            random_state=random_state,
        )

        return acquired_run_record.process(digital_processing=digital_processing)
