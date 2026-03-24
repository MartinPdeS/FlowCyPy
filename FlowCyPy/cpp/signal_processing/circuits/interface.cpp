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
        FlowCyPy C++ circuit interface.

        This module exposes C++ signal processing circuits to Python using pybind11.
        Each circuit processes a one dimensional signal and returns a new processed signal.
    )pbdoc";

    py::class_<BaseCircuit, std::shared_ptr<BaseCircuit>>(module, "BaseCircuit")
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
                Process a signal and return the processed output.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional signal to process.
                sampling_rate : pint.Quantity | None, optional
                    Sampling rate in hertz. Required for circuits that depend on it.

                Returns
                -------
                pint.Quantity
                    Processed signal with the same units as the input.
            )pbdoc"
        );


    py::class_<
        SlidingMinimumBaselineCorrection,
        BaseCircuit,
        std::shared_ptr<SlidingMinimumBaselineCorrection>
    >(
        module,
        "SlidingMinimumBaselineCorrection"
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
                    Sliding window size in second. Use -1 * second for an infinite window.
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
                Window size used for sliding minimum correction.

                Returns
                -------
                pint.Quantity
                    Window size in second. A value of -1 second means infinite window.
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
                Apply sliding minimum baseline correction to a signal.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional signal to process.
                sampling_rate : pint.Quantity | None, optional
                    Sampling rate in hertz. Required unless the window is infinite.

                Returns
                -------
                pint.Quantity
                    Corrected signal with the same units as the input.
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


    py::class_<BaselineRestorationServo, BaseCircuit, std::shared_ptr<BaselineRestorationServo>>(module, "BaselineRestorationServo")
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
                reference_level : float, optional
                    Target baseline level after restoration.
                initialize_with_first_sample : bool, optional
                    If True, initialize the baseline state from the first input sample.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "time_constant",
            [ureg](const BaselineRestorationServo& circuit) {
                return py::cast(circuit.time_constant) * ureg.attr("second");
            },
            R"pbdoc(
                Time constant of the baseline restoration servo.

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
                Output reference level used after baseline subtraction.
            )pbdoc"
        )
        .def_readonly(
            "initialize_with_first_sample",
            &BaselineRestorationServo::initialize_with_first_sample,
            R"pbdoc(
                Whether the internal baseline state is initialized from the first sample.
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
                Apply baseline restoration servo processing to a signal.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional signal to process.
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.

                Returns
                -------
                pint.Quantity
                    Baseline restored signal with the same units as the input.
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


    py::class_<ButterworthLowPassFilter, BaseCircuit, std::shared_ptr<ButterworthLowPassFilter>>(
        module,
        "ButterworthLowPass"
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
                gain : float
                    Output gain factor.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "cutoff_frequency",
            [ureg](const ButterworthLowPassFilter& circuit) {
                return py::cast(circuit.cutoff_frequency) * ureg.attr("hertz");
            },
            R"pbdoc(
                Cutoff frequency of the Butterworth filter.

                Returns
                -------
                pint.Quantity
                    Cutoff frequency in hertz.
            )pbdoc"
        )
        .def_readonly("order", &ButterworthLowPassFilter::order)
        .def_readonly("gain", &ButterworthLowPassFilter::gain)
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
                Apply the Butterworth filter to a signal.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional signal to process.
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.

                Returns
                -------
                pint.Quantity
                    Filtered signal with the same units as the input.
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


    py::class_<BesselLowPassFilter, BaseCircuit, std::shared_ptr<BesselLowPassFilter>>(
        module,
        "BesselLowPass"
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
                    Output gain factor.
            )pbdoc"
        )
        .def(py::init<>())
        .def_property_readonly(
            "cutoff_frequency",
            [ureg](const BesselLowPassFilter& circuit) {
                return py::cast(circuit.cutoff_frequency) * ureg.attr("hertz");
            },
            R"pbdoc(
                Cutoff frequency of the Bessel filter.

                Returns
                -------
                pint.Quantity
                    Cutoff frequency in hertz.
            )pbdoc"
        )
        .def_readonly("order", &BesselLowPassFilter::order)
        .def_readonly("gain", &BesselLowPassFilter::gain)
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
                Apply the Bessel filter to a signal.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional signal to process.
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.

                Returns
                -------
                pint.Quantity
                    Filtered signal with the same units as the input.
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
