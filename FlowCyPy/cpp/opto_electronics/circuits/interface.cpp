#include <limits>
#include <memory>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <pint/pint.h>
#include "circuits.h"

namespace py = pybind11;


PYBIND11_MODULE(circuits, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"pbdoc(
        Analog signal conditioning circuits for FlowCyPy.

        This module exposes analog processing circuits used in the opto electronic
        acquisition chain of a flow cytometry simulation.
        %
        Each circuit operates on a one dimensional signal and returns a processed
        signal with the same physical units as the input.
        %
        Typical use cases include baseline correction, baseline restoration, and
        analog low pass filtering prior to digitization or downstream digital
        processing.

        All public ``process`` methods expect:

        - ``signal`` to be a Pint quantity backed by a one dimensional NumPy array
        - ``sampling_rate`` to be a Pint quantity compatible with hertz when required
    )pbdoc";

    py::class_<BaseCircuit, std::shared_ptr<BaseCircuit>>(
        module,
        "BaseCircuit",
        R"pbdoc(
            Abstract base class for analog signal conditioning circuits.

            A :class:`BaseCircuit` represents a transformation applied to a
            one dimensional signal in the analog acquisition chain.
            %
            Concrete subclasses implement specific operations such as baseline
            subtraction or low pass filtering.
            %
            The processed output always retains the same physical units as the
            input signal.
        )pbdoc"
    )
        .def(
            "process",
            [](
                const BaseCircuit& circuit,
                const py::object& signal,
                const py::object& sampling_rate
            ) {
                if (!py::hasattr(signal, "units") || !py::hasattr(signal, "magnitude")) {
                    throw std::runtime_error(
                        "signal must be a Pint quantity backed by a one dimensional NumPy array."
                    );
                }

                py::object signal_units = signal.attr("units");
                std::vector<double> input_signal =
                    signal.attr("magnitude").cast<std::vector<double>>();

                double sampling_rate_value = std::numeric_limits<double>::quiet_NaN();

                if (!sampling_rate.is_none()) {
                    sampling_rate_value =
                        sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>();

                    if (sampling_rate_value <= 0.0) {
                        throw std::runtime_error("sampling_rate must be strictly positive.");
                    }
                }

                std::vector<double> output_signal =
                    circuit.process(input_signal, sampling_rate_value);

                py::array_t<double> output_array(output_signal.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(output_signal.size()); ++index) {
                    output_view(index) = output_signal[static_cast<size_t>(index)];
                }

                return output_array * signal_units;
            },
            py::arg("signal"),
            py::arg("sampling_rate") = py::none(),
            R"pbdoc(
                Process a signal with the circuit.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional input signal.
                sampling_rate : pint.Quantity or None, optional
                    Sampling rate in hertz.
                    %
                    Circuits that depend on time scale or frequency response may
                    require this value, while others may ignore it.

                Returns
                -------
                pint.Quantity
                    Processed signal with the same units as the input.

                Notes
                -----
                This method preserves the physical units of the input signal.
                %
                Only the numerical values are transformed by the circuit.
            )pbdoc"
        );


    py::class_<
        SlidingMinimumBaselineCorrection,
        BaseCircuit,
        std::shared_ptr<SlidingMinimumBaselineCorrection>
    >(
        module,
        "SlidingMinimumBaselineCorrection",
        R"pbdoc(
            Sliding minimum baseline correction circuit.

            This circuit estimates the local baseline by tracking the minimum
            signal value within a sliding window and subtracting that baseline
            estimate from the input.
            %
            It is useful for suppressing slowly varying offsets or drifting
            baselines while preserving positive excursions associated with
            particle events.
            %
            A window size of ``-1 * second`` is interpreted as an infinite
            window, meaning that the baseline is estimated from the global
            minimum over the full signal.
        )pbdoc"
    )
        .def(
            py::init(
                [ureg](const py::object& window_size) {
                    const double window_size_second =
                        window_size.attr("to")("second").attr("magnitude").cast<double>();

                    return std::make_shared<SlidingMinimumBaselineCorrection>(
                        window_size_second
                    );
                }
            ),
            py::arg("window_size"),
            R"pbdoc(
                Initialize a sliding minimum baseline correction circuit.

                Parameters
                ----------
                window_size : pint.Quantity
                    Sliding window size in second.
                    %
                    Use ``-1 * second`` to request an infinite window spanning
                    the full signal.

                Notes
                -----
                When a finite window is used, the effective number of samples in
                the window depends on the sampling rate supplied to
                :meth:`process`.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "window_size",
            [ureg](const SlidingMinimumBaselineCorrection& circuit) {
                if (circuit.window_size == -1.0) {
                    return py::cast(-1.0) * ureg.attr("second");
                }

                return py::cast(circuit.window_size) * ureg.attr("second");
            },
            R"pbdoc(
                Sliding window size used for baseline estimation.

                Returns
                -------
                pint.Quantity
                    Window size in second.
                    %
                    A value of ``-1 * second`` indicates an infinite window.
            )pbdoc"
        )
        .def(
            "process",
            [](
                const SlidingMinimumBaselineCorrection& circuit,
                const py::object& signal,
                const py::object& sampling_rate
            ) {
                if (!py::hasattr(signal, "units") || !py::hasattr(signal, "magnitude")) {
                    throw std::runtime_error(
                        "signal must be a Pint quantity backed by a one dimensional NumPy array."
                    );
                }

                py::object signal_units = signal.attr("units");
                std::vector<double> input_signal =
                    signal.attr("magnitude").cast<std::vector<double>>();

                double sampling_rate_value = std::numeric_limits<double>::quiet_NaN();

                if (!sampling_rate.is_none()) {
                    sampling_rate_value =
                        sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>();

                    if (sampling_rate_value <= 0.0) {
                        throw std::runtime_error("sampling_rate must be strictly positive.");
                    }
                }

                std::vector<double> output_signal =
                    circuit.process(input_signal, sampling_rate_value);

                py::array_t<double> output_array(output_signal.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(output_signal.size()); ++index) {
                    output_view(index) = output_signal[static_cast<size_t>(index)];
                }

                return output_array * signal_units;
            },
            py::arg("signal"),
            py::arg("sampling_rate") = py::none(),
            R"pbdoc(
                Apply sliding minimum baseline correction.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional input signal.
                sampling_rate : pint.Quantity or None, optional
                    Sampling rate in hertz.
                    %
                    This is required when ``window_size`` is finite, because the
                    time window must be converted into a number of samples.
                    %
                    It may be omitted when the window is infinite.

                Returns
                -------
                pint.Quantity
                    Baseline corrected signal with the same units as the input.
            )pbdoc"
        )
        .def(
            "__repr__",
            [](const SlidingMinimumBaselineCorrection& circuit) {
                return
                    "SlidingMinimumBaselineCorrection(window_size=" +
                    std::to_string(circuit.window_size) + ")";
            }
        );


    py::class_<
        BaselineRestorationServo,
        BaseCircuit,
        std::shared_ptr<BaselineRestorationServo>
    >(
        module,
        "BaselineRestorationServo",
        R"pbdoc(
            Baseline restoration servo circuit.

            This circuit models a baseline restoration stage that continuously
            estimates the slowly varying baseline of a signal and subtracts it
            so that the output is driven toward a target reference level.
            %
            It is useful for suppressing baseline drift and restoring a stable
            operating point before digitization or event extraction.
            %
            The response speed of the servo is controlled by its time constant.
        )pbdoc"
    )
        .def(
            py::init(
                [ureg](
                    const py::object& time_constant,
                    const double reference_level,
                    const bool initialize_with_first_sample
                ) {
                    const double time_constant_second =
                        time_constant.attr("to")("second").attr("magnitude").cast<double>();

                    return std::make_shared<BaselineRestorationServo>(
                        time_constant_second,
                        reference_level,
                        initialize_with_first_sample
                    );
                }
            ),
            py::arg("time_constant"),
            py::arg("reference_level") = 0.0,
            py::arg("initialize_with_first_sample") = true,
            R"pbdoc(
                Initialize a baseline restoration servo.

                Parameters
                ----------
                time_constant : pint.Quantity
                    Servo time constant in second.
                    %
                    Larger values produce slower baseline tracking, while smaller
                    values produce faster adaptation.
                reference_level : float, optional
                    Output reference level after restoration.
                initialize_with_first_sample : bool, optional
                    If ``True``, initialize the internal baseline state from the
                    first input sample.
                    %
                    If ``False``, the internal state is initialized independently
                    of the first sample.

                Notes
                -----
                This circuit requires a valid sampling rate in order to convert
                the time constant into a discrete time update rule.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "time_constant",
            [ureg](const BaselineRestorationServo& circuit) {
                return py::cast(circuit.time_constant) * ureg.attr("second");
            },
            R"pbdoc(
                Servo time constant.

                Returns
                -------
                pint.Quantity
                    Time constant in second.
            )pbdoc"
        )
        .def_readonly(
            "reference_level",
            &BaselineRestorationServo::reference_level,
            R"pbdoc(
                Target output baseline level.

                After restoration, the signal baseline is driven toward this
                numerical reference value.
            )pbdoc"
        )
        .def_readonly(
            "initialize_with_first_sample",
            &BaselineRestorationServo::initialize_with_first_sample,
            R"pbdoc(
                Whether the internal baseline state is initialized from the first sample.

                When enabled, the circuit starts from the first input value,
                which often reduces initial transients.
            )pbdoc"
        )
        .def(
            "process",
            [](
                const BaselineRestorationServo& circuit,
                const py::object& signal,
                const py::object& sampling_rate
            ) {
                if (!py::hasattr(signal, "units") || !py::hasattr(signal, "magnitude")) {
                    throw std::runtime_error(
                        "signal must be a Pint quantity backed by a one dimensional NumPy array."
                    );
                }

                if (sampling_rate.is_none()) {
                    throw std::runtime_error(
                        "sampling_rate is required for BaselineRestorationServo."
                    );
                }

                py::object signal_units = signal.attr("units");
                std::vector<double> input_signal =
                    signal.attr("magnitude").cast<std::vector<double>>();

                const double sampling_rate_value =
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>();

                if (sampling_rate_value <= 0.0) {
                    throw std::runtime_error("sampling_rate must be strictly positive.");
                }

                std::vector<double> output_signal =
                    circuit.process(input_signal, sampling_rate_value);

                py::array_t<double> output_array(output_signal.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(output_signal.size()); ++index) {
                    output_view(index) = output_signal[static_cast<size_t>(index)];
                }

                return output_array * signal_units;
            },
            py::arg("signal"),
            py::arg("sampling_rate"),
            R"pbdoc(
                Apply baseline restoration servo processing.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional input signal.
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.

                Returns
                -------
                pint.Quantity
                    Baseline restored signal with the same units as the input.

                Notes
                -----
                A valid sampling rate is required because the circuit dynamics are
                defined through the servo time constant.
            )pbdoc"
        )
        .def(
            "__repr__",
            [](const BaselineRestorationServo& circuit) {
                return
                    "BaselineRestorationServo(time_constant=" +
                    std::to_string(circuit.time_constant) +
                    ", reference_level=" + std::to_string(circuit.reference_level) +
                    ", initialize_with_first_sample=" +
                    std::string(circuit.initialize_with_first_sample ? "true" : "false") +
                    ")";
            }
        );


    py::class_<
        ButterworthLowPassFilter,
        BaseCircuit,
        std::shared_ptr<ButterworthLowPassFilter>
    >(
        module,
        "ButterworthLowPass",
        R"pbdoc(
            Butterworth low pass filter.

            This circuit applies a Butterworth low pass response to the input
            signal.
            %
            Butterworth filters provide a maximally flat magnitude response in
            the passband and are useful when smooth low pass attenuation is
            desired without passband ripple.
            %
            The output can optionally be scaled by a multiplicative gain factor.
        )pbdoc"
    )
        .def(
            py::init(
                [ureg](
                    const py::object& cutoff_frequency,
                    const int order,
                    const double gain
                ) {
                    const double cutoff_frequency_hertz =
                        cutoff_frequency.attr("to")("hertz").attr("magnitude").cast<double>();

                    return std::make_shared<ButterworthLowPassFilter>(
                        cutoff_frequency_hertz,
                        order,
                        gain
                    );
                }
            ),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"pbdoc(
                Initialize a Butterworth low pass filter.

                Parameters
                ----------
                cutoff_frequency : pint.Quantity
                    Cutoff frequency in hertz.
                order : int
                    Filter order.
                    %
                    Higher orders produce a steeper roll off.
                gain : float
                    Multiplicative gain applied to the filtered output.

                Notes
                -----
                This circuit requires a valid sampling rate when calling
                :meth:`process`.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "cutoff_frequency",
            [ureg](const ButterworthLowPassFilter& circuit) {
                return py::cast(circuit.cutoff_frequency) * ureg.attr("hertz");
            },
            R"pbdoc(
                Filter cutoff frequency.

                Returns
                -------
                pint.Quantity
                    Cutoff frequency in hertz.
            )pbdoc"
        )
        .def_readonly(
            "order",
            &ButterworthLowPassFilter::order,
            R"pbdoc(
                Filter order.

                Higher orders correspond to a sharper transition between passband
                and stopband.
            )pbdoc"
        )
        .def_readonly(
            "gain",
            &ButterworthLowPassFilter::gain,
            R"pbdoc(
                Multiplicative output gain applied after filtering.
            )pbdoc"
        )
        .def(
            "process",
            [](
                const ButterworthLowPassFilter& circuit,
                const py::object& signal,
                const py::object& sampling_rate
            ) {
                if (!py::hasattr(signal, "units") || !py::hasattr(signal, "magnitude")) {
                    throw std::runtime_error(
                        "signal must be a Pint quantity backed by a one dimensional NumPy array."
                    );
                }

                if (sampling_rate.is_none()) {
                    throw std::runtime_error(
                        "sampling_rate is required for ButterworthLowPass."
                    );
                }

                py::object signal_units = signal.attr("units");
                std::vector<double> input_signal =
                    signal.attr("magnitude").cast<std::vector<double>>();

                const double sampling_rate_value =
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>();

                if (sampling_rate_value <= 0.0) {
                    throw std::runtime_error("sampling_rate must be strictly positive.");
                }

                std::vector<double> output_signal =
                    circuit.process(input_signal, sampling_rate_value);

                py::array_t<double> output_array(output_signal.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(output_signal.size()); ++index) {
                    output_view(index) = output_signal[static_cast<size_t>(index)];
                }

                return output_array * signal_units;
            },
            py::arg("signal"),
            py::arg("sampling_rate"),
            R"pbdoc(
                Apply Butterworth low pass filtering.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional input signal.
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.

                Returns
                -------
                pint.Quantity
                    Filtered signal with the same units as the input.

                Notes
                -----
                The sampling rate is required to map the analog cutoff frequency
                to the discrete time signal.
            )pbdoc"
        )
        .def(
            "__repr__",
            [](const ButterworthLowPassFilter& circuit) {
                return
                    "ButterworthLowPass(cutoff_frequency=" +
                    std::to_string(circuit.cutoff_frequency) +
                    ", order=" + std::to_string(circuit.order) +
                    ", gain=" + std::to_string(circuit.gain) + ")";
            }
        );


    py::class_<
        BesselLowPassFilter,
        BaseCircuit,
        std::shared_ptr<BesselLowPassFilter>
    >(
        module,
        "BesselLowPass",
        R"pbdoc(
            Bessel low pass filter.

            This circuit applies a Bessel low pass response to the input signal.
            %
            Bessel filters are often preferred when preserving waveform shape and
            approximate phase linearity is more important than maximizing roll off
            steepness.
            %
            The output can optionally be scaled by a multiplicative gain factor.
        )pbdoc"
    )
        .def(
            py::init(
                [ureg](
                    const py::object& cutoff_frequency,
                    const int order,
                    const double gain
                ) {
                    const double cutoff_frequency_hertz =
                        cutoff_frequency.attr("to")("hertz").attr("magnitude").cast<double>();

                    return std::make_shared<BesselLowPassFilter>(
                        cutoff_frequency_hertz,
                        order,
                        gain
                    );
                }
            ),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"pbdoc(
                Initialize a Bessel low pass filter.

                Parameters
                ----------
                cutoff_frequency : pint.Quantity
                    Cutoff frequency in hertz.
                order : int
                    Filter order.
                gain : float
                    Multiplicative gain applied to the filtered output.

                Notes
                -----
                This circuit requires a valid sampling rate when calling
                :meth:`process`.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "cutoff_frequency",
            [ureg](const BesselLowPassFilter& circuit) {
                return py::cast(circuit.cutoff_frequency) * ureg.attr("hertz");
            },
            R"pbdoc(
                Filter cutoff frequency.

                Returns
                -------
                pint.Quantity
                    Cutoff frequency in hertz.
            )pbdoc"
        )
        .def_readonly(
            "order",
            &BesselLowPassFilter::order,
            R"pbdoc(
                Filter order.

                Higher orders increase the sharpness of the low pass transition.
            )pbdoc"
        )
        .def_readonly(
            "gain",
            &BesselLowPassFilter::gain,
            R"pbdoc(
                Multiplicative output gain applied after filtering.
            )pbdoc"
        )
        .def(
            "process",
            [](
                const BesselLowPassFilter& circuit,
                const py::object& signal,
                const py::object& sampling_rate
            ) {
                if (!py::hasattr(signal, "units") || !py::hasattr(signal, "magnitude")) {
                    throw std::runtime_error(
                        "signal must be a Pint quantity backed by a one dimensional NumPy array."
                    );
                }

                if (sampling_rate.is_none()) {
                    throw std::runtime_error(
                        "sampling_rate is required for BesselLowPass."
                    );
                }

                py::object signal_units = signal.attr("units");
                std::vector<double> input_signal =
                    signal.attr("magnitude").cast<std::vector<double>>();

                const double sampling_rate_value =
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>();

                if (sampling_rate_value <= 0.0) {
                    throw std::runtime_error("sampling_rate must be strictly positive.");
                }

                std::vector<double> output_signal =
                    circuit.process(input_signal, sampling_rate_value);

                py::array_t<double> output_array(output_signal.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(output_signal.size()); ++index) {
                    output_view(index) = output_signal[static_cast<size_t>(index)];
                }

                return output_array * signal_units;
            },
            py::arg("signal"),
            py::arg("sampling_rate"),
            R"pbdoc(
                Apply Bessel low pass filtering.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional input signal.
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.

                Returns
                -------
                pint.Quantity
                    Filtered signal with the same units as the input.

                Notes
                -----
                This filter is typically used when preserving pulse shape is more
                important than maximizing stopband steepness.
            )pbdoc"
        )
        .def(
            "__repr__",
            [](const BesselLowPassFilter& circuit) {
                return
                    "BesselLowPass(cutoff_frequency=" +
                    std::to_string(circuit.cutoff_frequency) +
                    ", order=" + std::to_string(circuit.order) +
                    ", gain=" + std::to_string(circuit.gain) + ")";
            }
        );
}
