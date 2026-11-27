import math
from functools import partial
import numpy as np
from TypedUnit import Power, Time, ureg, validate_units
from FlowCyPy.digital_processing import DigitalProcessing
from FlowCyPy.event_collection import EventCollection
from FlowCyPy.fluidics import Fluidics, populations
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.opto_electronics.system import _next_noise_seed
from FlowCyPy.run_record import RunRecord
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame


class FlowCytometer:
    """
    High level orchestrator for the flow cytometry simulation pipeline.

    Parameters
    ----------
    fluidics : Fluidics
        Fluidic subsystem, including flow cell and population definitions.
    background_power : pint.Quantity, optional
        Constant optical background added to every detector channel.
    opto_electronics : OptoElectronics, optional
        Default optical and electronic components for acquisitions.
    digital_processing : DigitalProcessing, optional
        Default processing applied by run().
    """

    @validate_units
    def __init__(
        self,
        fluidics: Fluidics,
        background_power: Power | None = 0 * ureg.milliwatt,
        *,
        opto_electronics: OptoElectronics | None = None,
        digital_processing: DigitalProcessing | None = None,
    ):
        self.opto_electronics = opto_electronics
        self.digital_processing = digital_processing
        self.fluidics = fluidics
        self.background_power = 0 * ureg.watt if background_power is None else background_power
        if opto_electronics is not None:
            self._validate_background_power()

    def _validate_background_power(self) -> None:
        """Require a finite, non-negative optical background for configured instruments."""
        try:
            watts = float(self.background_power.to("watt").magnitude)
        except (AttributeError, TypeError, ValueError) as error:
            raise TypeError("background_power must be a scalar power quantity.") from error
        if not math.isfinite(watts) or watts < 0:
            raise ValueError("background_power must be finite and non-negative.")

    def _add_explicit_model_signals(
        self,
        event_collection: EventCollection,
        signal_dict: dict,
        opto_electronics: OptoElectronics,
    ) -> dict:
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

        Returns
        -------
        dict
            Separate optical traces for wavelength-dependent shot noise or
            delayed emission. Keys identify channel, wavelength in nm and,
            for delayed emission, lifetime in seconds.
        """
        sample_times = signal_dict["Time"]
        spectral_traces = {}
        if sample_times.size == 0:
            return spectral_traces

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
            generate_pulse = partial(
                opto_electronics.source.generate_pulses,
                velocities=velocities[event_indices],
                pulse_centers=pulse_centers,
                time_array=sample_times,
                base_level=0 * ureg.watt,
            )
            for detector in opto_electronics.detectors:
                name = detector.name
                components = events.metadata.get("FluorescencePower", {}).get(name)
                needs_spectral_trace = components is not None and (
                    opto_electronics.source.include_shot_noise
                    or opto_electronics.source._has_multiple_lasers
                    or any(len(dye) == 3 for dye in components[1])
                )
                if not needs_spectral_trace:
                    amplitude = events.get_quantity(name)
                    signal_dict[name] += generate_pulse(pulse_amplitudes=amplitude[event_indices])
                    continue

                scatter, dyes = components
                signal_dict[name] += generate_pulse(pulse_amplitudes=scatter[event_indices])
                for dye_amplitude, spectral_weights, *delay in dyes:
                    pulse = generate_pulse(pulse_amplitudes=dye_amplitude[event_indices])
                    for wavelength, weight in spectral_weights.items():
                        key = (name, wavelength, *delay)
                        if key in spectral_traces:
                            spectral_traces[key] += pulse * weight
                        else:
                            spectral_traces[key] = pulse * weight
        return spectral_traces

    def _add_gamma_model_signals(
        self,
        event_collection: EventCollection,
        signal_dict: dict,
        opto_electronics: OptoElectronics,
        *,
        spectral_traces: dict,
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

            for detector in opto_electronics.detectors:
                reference_mean_amplitude = events.get_quantity(detector.name).mean()
                if reference_mean_amplitude > 0 * ureg.watt:
                    break
            else:
                # A population invisible to every channel still has an occupancy trace.
                reference_mean_amplitude = 1 * ureg.watt

            reference_power_trace = opto_electronics.source.get_gamma_trace(
                time_array=signal_dict["Time"],
                shape=expected_number_of_particles,
                scale=reference_mean_amplitude,
                mean_velocity=events.metadata["VelocityMean"],
                seed=_next_noise_seed(generator=random_generator),
            )

            particle_trace = reference_power_trace / reference_mean_amplitude

            events.metadata["ParticleTrace"] = particle_trace
            events.metadata["TimeTrace"] = signal_dict["Time"]

            for detector in opto_electronics.detectors:
                mean_amplitude = events.get_quantity(detector.name).mean()
                if opto_electronics.source._has_multiple_lasers:
                    for index, laser in enumerate(opto_electronics.source.lasers):
                        nm = laser.wavelength.m_as("nm")
                        line_mean = events.get_quantity(f"{detector.name}[{nm:g} nm]").mean()
                        key = (detector.name, nm, 0.0, index)
                        spectral_traces[key] = spectral_traces.get(key, 0 * ureg.watt) + particle_trace * line_mean
                else:
                    signal_dict[detector.name] += particle_trace * mean_amplitude

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

        spectral_traces = self._add_explicit_model_signals(
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
            spectral_traces=spectral_traces,
        )

        return opto_electronics.convert_optical_power_to_voltage(
            power_signal_dict, random_generator=noise_rng, emission=spectral_traces
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
        opto_electronics: OptoElectronics | None = None,
        random_state: int | np.random.Generator | None = None,
    ) -> RunRecord:
        """
        Run the acquisition pipeline up to the analog stage.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics, optional
            Override the optics configured on this instrument for this acquisition.

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
        if self.opto_electronics is not None:
            self._validate_background_power()
            sample = self.fluidics.scatterer_collection.populations
            if not sample:
                raise ValueError("Add at least one population before acquisition.")
            names = [population.name for population in sample]
            if any(not name or not name.strip() for name in names):
                raise ValueError("Each population must have a non-empty name.")
            if len(set(names)) != len(names):
                raise ValueError("Population names must be unique.")
        if opto_electronics is None:
            opto_electronics = self.opto_electronics
        if opto_electronics is None:
            raise ValueError(
                "Set opto_electronics on the instrument or pass it to acquire or run."
            )
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
        opto_electronics: OptoElectronics | None = None,
        digital_processing: DigitalProcessing | None = None,
        random_state: int | np.random.Generator | None = None,
    ) -> RunRecord:
        """
        Run the full simulation pipeline from event generation to peak extraction.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        opto_electronics : OptoElectronics, optional
            Override the optics configured on this instrument for this acquisition.
        digital_processing : DigitalProcessing, optional
            Override the configured processing for this run. If neither is supplied,
            use the default DigitalProcessing settings.

        random_state : int or numpy.random.Generator, optional
            A non-negative integer repeats the events and noisy signals with the
            same build and OpenMP worker count. A generator advances each run.

        Returns
        -------
        RunRecord
            Full run record containing all available stages.
        """
        if digital_processing is None:
            digital_processing = self.digital_processing
        if digital_processing is None:
            digital_processing = DigitalProcessing()

        acquired_run_record = self.acquire(
            run_time=run_time,
            opto_electronics=opto_electronics,
            random_state=random_state,
        )

        return acquired_run_record.process(digital_processing=digital_processing)
