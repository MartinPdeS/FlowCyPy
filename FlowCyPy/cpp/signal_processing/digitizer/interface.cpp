#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <cmath>
#include <string>
#include <vector>
#include <limits>
#include <cstdint>
#include <map>

#include "digitizer.h"
#include <utils/casting.h>
#include <pint/pint.h>

namespace py = pybind11;


PYBIND11_MODULE(digitizer, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"pbdoc(
        FlowCyPy digitizer interface.

        This module exposes a digitizer model that can clip voltage signals,
        infer voltage ranges, quantize to integer code values, and optionally
        use signed output codes.

        Signals are expected to be Pint quantities compatible with volts.
    )pbdoc";

    py::class_<Digitizer>(
        module,
        "Digitizer",
        R"pbdoc(
            Digitize and clip voltage signals.

            The ``Digitizer`` class models a digitization stage for voltage signals.
            It can optionally clip the signal to a voltage range and quantize it
            according to a specified bit depth.

            Input signals may contain negative voltages. The voltage range used for
            clipping and quantization is defined by ``min_voltage`` and ``max_voltage``.

            The output code format depends on ``output_signed_codes``:

            * if ``False``, codes lie in ``[0, 2**bit_depth - 1]``
            * if ``True``, codes lie in ``[-2**(bit_depth - 1), 2**(bit_depth - 1) - 1]``

            A bit depth of ``0`` disables digitization. In that case, the signal remains
            continuous and only optional clipping is applied.

            The bandwidth is optional. If ``bandwidth`` is not provided, it remains unset
            and is not considered in any computation.

            Automatic range inference can be enabled persistently by setting
            ``use_auto_range=True`` at construction, or temporarily per call with
            the corresponding method argument.

            Parameters
            ----------
            sampling_rate : pint.Quantity
                Sampling rate of the digitizer. Must be compatible with hertz.
            bandwidth : pint.Quantity or None, default=None
                Digitizer bandwidth. Must be compatible with hertz. If ``None``,
                bandwidth remains unset.
            bit_depth : int, default=0
                Number of quantization bits. A value of ``0`` disables digitization.
            min_voltage : pint.Quantity or None, default=None
                Minimum clipping voltage. Must be compatible with volts.
            max_voltage : pint.Quantity or None, default=None
                Maximum clipping voltage. Must be compatible with volts.
            use_auto_range : bool, default=False
                If ``True``, :meth:`process_signal` and :meth:`capture_signal`
                will infer ``min_voltage`` and ``max_voltage`` from the input signal
                when their overload without explicit override is used.
            output_signed_codes : bool, default=False
                If ``True``, digitized outputs use signed integer like code values.
        )pbdoc"
    )
        .def(
            py::init([](
                const py::object& sampling_rate,
                const py::object& bandwidth,
                const size_t bit_depth,
                const py::object& min_voltage,
                const py::object& max_voltage,
                const bool use_auto_range,
                const bool output_signed_codes,
                const bool debug_mode
            ) {
                const double sampling_rate_value = Casting::cast_py_to_scalar<double>( sampling_rate, "sampling_rate", "hertz");

                const double bandwidth_value = bandwidth.is_none()
                    ? std::numeric_limits<double>::quiet_NaN()
                    : Casting::cast_py_to_scalar<double>(bandwidth, "bandwidth", "hertz");

                return Digitizer(
                    bandwidth_value,
                    sampling_rate_value,
                    bit_depth,
                    Casting::cast_py_to_optional_scalar<double>(min_voltage, "min_voltage", "volt"),
                    Casting::cast_py_to_optional_scalar<double>(max_voltage, "max_voltage", "volt"),
                    use_auto_range,
                    output_signed_codes,
                    debug_mode
                );
            }),
            py::arg("sampling_rate"),
            py::arg("bandwidth") = py::none(),
            py::arg("bit_depth") = 0,
            py::arg("min_voltage") = py::none(),
            py::arg("max_voltage") = py::none(),
            py::arg("use_auto_range") = false,
            py::arg("output_signed_codes") = false,
            py::arg("debug_mode") = false,

            R"pbdoc(
                Initialize a digitizer.

                Parameters
                ----------
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.
                bandwidth : pint.Quantity or None, default=None
                    Digitizer bandwidth in hertz. If ``None``, bandwidth remains unset.
                bit_depth : int, default=0
                    Number of quantization bits. A value of ``0`` disables digitization.
                min_voltage : pint.Quantity or None, default=None
                    Minimum clipping voltage.
                max_voltage : pint.Quantity or None, default=None
                    Maximum clipping voltage.
                use_auto_range : bool, default=False
                    Persistent automatic range inference mode.
                output_signed_codes : bool, default=False
                    If ``True``, return signed integer like ADC code values.
                debug_mode : bool, default=False
                    If ``True``, print debug information during processing.
            )pbdoc"
        )

        .def("has_bandwidth", &Digitizer::has_bandwidth)
        .def("has_voltage_range", &Digitizer::has_voltage_range)
        .def("should_digitize", &Digitizer::should_digitize)
        .def("has_signed_output_codes", &Digitizer::has_signed_output_codes)
        .def("clear_bandwidth", &Digitizer::clear_bandwidth)
        .def("clear_voltage_range", &Digitizer::clear_voltage_range)
        .def("get_minimum_code", &Digitizer::get_minimum_code)
        .def("get_maximum_code", &Digitizer::get_maximum_code)

        .def_property(
            "bandwidth",
            [ureg](const Digitizer& self) -> py::object {
                if (std::isnan(self.bandwidth)) {
                    return py::none();
                }

                return (py::float_(self.bandwidth) * ureg.attr("hertz")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.bandwidth = Casting::cast_py_to_optional_scalar<double>(value, "bandwidth", "hertz");

                if (!std::isnan(self.bandwidth) && self.bandwidth <= 0.0) {
                    throw std::invalid_argument(
                        "Digitizer bandwidth must be strictly positive when provided."
                    );
                }
            },
            R"pbdoc(
                Bandwidth of the digitizer.

                Returns
                -------
                pint.Quantity or None
                    Bandwidth in hertz, or ``None`` if unset.
            )pbdoc"
        )

        .def_property(
            "sampling_rate",
            [ureg](const Digitizer& self) -> py::object {
                return (py::float_(self.sampling_rate) * ureg.attr("hertz")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.sampling_rate = Casting::cast_py_to_scalar<double>(value, "sampling_rate", "hertz");

                if (std::isnan(self.sampling_rate) || self.sampling_rate <= 0.0) {
                    throw std::invalid_argument(
                        "Digitizer sampling_rate must be strictly positive."
                    );
                }
            },
            R"pbdoc(
                Sampling rate of the digitizer.

                Returns
                -------
                pint.Quantity
                    Sampling rate in hertz.
            )pbdoc"
        )

        .def_property(
            "bit_depth",
            [](const Digitizer& self) {
                return self.bit_depth;
            },
            [](Digitizer& self, const size_t value) {
                if (value > 63)
                    throw std::invalid_argument("Digitizer bit_depth must be smaller than or equal to 63.");

                self.bit_depth = value;
            },
            R"pbdoc(
                Number of quantization bits.

                A value of ``0`` disables digitization.
            )pbdoc"
        )
        .def_readwrite(
            "use_auto_range",
            &Digitizer::use_auto_range,
            R"pbdoc(
                Persistent automatic range inference mode.
            )pbdoc"
        )
        .def_readwrite(
            "output_signed_codes",
            &Digitizer::output_signed_codes,
            R"pbdoc(
                Whether digitized outputs use signed integer like code values.
            )pbdoc"
        )
        .def_property(
            "min_voltage",
            [ureg](const Digitizer& self) -> py::object {
                if (std::isnan(self.min_voltage)) {
                    return py::none();
                }

                return (py::float_(self.min_voltage) * ureg.attr("volt")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.min_voltage = Casting::cast_py_to_optional_scalar<double>(value, "min_voltage", "volt");

                if (!std::isnan(self.min_voltage) && !std::isnan(self.max_voltage) && self.max_voltage <= self.min_voltage)
                    throw std::invalid_argument("Digitizer requires max_voltage to be greater than min_voltage.");

            },
            R"pbdoc(
                Minimum clipping voltage.

                Returns
                -------
                pint.Quantity or None
                    Minimum clipping voltage in volts, or ``None`` if unset.
            )pbdoc"
        )

        .def_property(
            "max_voltage",
            [ureg](const Digitizer& self) -> py::object {
                if (std::isnan(self.max_voltage))
                    return py::none();

                return (py::float_(self.max_voltage) * ureg.attr("volt")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.max_voltage = Casting::cast_py_to_optional_scalar<double>(value, "max_voltage", "volt");

                if (!std::isnan(self.min_voltage) && !std::isnan(self.max_voltage) && self.max_voltage <= self.min_voltage)
                    throw std::invalid_argument("Digitizer requires max_voltage to be greater than min_voltage.");
            },
            R"pbdoc(
                Maximum clipping voltage.

                Returns
                -------
                pint.Quantity or None
                    Maximum clipping voltage in volts, or ``None`` if unset.
            )pbdoc"
        )

        .def(
            "set_auto_range",
            [](Digitizer& self, const py::object& signal) {
                self.set_auto_range(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Infer the voltage range from a signal.

                The minimum and maximum finite values of the input signal are used
                to update ``min_voltage`` and ``max_voltage``.
            )pbdoc"
        )

        .def(
            "get_min_max",
            [ureg](const Digitizer& self, const py::object& signal) {
                const auto [minimum_value, maximum_value] = self.get_min_max(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );

                return py::make_tuple(
                    (py::float_(minimum_value) * ureg.attr("volt")).attr("to_compact")(),
                    (py::float_(maximum_value) * ureg.attr("volt")).attr("to_compact")()
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Return the minimum and maximum finite values of a signal.
            )pbdoc"
        )

        .def(
            "clip_signal",
            [ureg](const Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector =
                    Casting::cast_py_to_vector<double>(signal, "volt");

                self.clip_signal(signal_vector);

                return py::array_t<double>(
                    signal_vector.size(),
                    signal_vector.data()
                ) * ureg.attr("volt");
            },
            py::arg("signal"),
            R"pbdoc(
                Clip a signal to the configured voltage range.

                Returns
                -------
                pint.Quantity
                    Clipped signal in volts.
            )pbdoc"
        )

        .def(
            "digitize_signal",
            [](const Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector = Casting::cast_py_to_vector<double>(signal, "volt");

                self.digitize_signal(signal_vector);

                if (!self.should_digitize()) {
                    return signal.attr("magnitude");
                }

                if (self.output_signed_codes) {
                    py::array_t<int64_t> output_array(signal_vector.size());
                    auto output_view = output_array.mutable_unchecked<1>();

                    for (ssize_t index = 0; index < static_cast<ssize_t>(signal_vector.size()); ++index) {
                        const double sample = signal_vector[static_cast<size_t>(index)];

                        if (std::isnan(sample)) {
                            throw std::runtime_error(
                                "Digitized integer output cannot represent NaN values."
                            );
                        }

                        output_view(index) = static_cast<int64_t>(std::llround(sample));
                    }

                    return output_array;
                }

                py::array_t<uint64_t> output_array(signal_vector.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(signal_vector.size()); ++index) {
                    const double sample = signal_vector[static_cast<size_t>(index)];

                    if (std::isnan(sample)) {
                        throw std::runtime_error(
                            "Digitized integer output cannot represent NaN values."
                        );
                    }

                    const int64_t code_value = static_cast<int64_t>(std::llround(sample));

                    if (code_value < 0) {
                        throw std::runtime_error(
                            "Unsigned digitizer output encountered a negative code."
                        );
                    }

                    output_view(index) = static_cast<uint64_t>(code_value);
                }

                return output_array;
            },
            py::arg("signal"),
            R"pbdoc(
                Quantize a signal according to the configured bit depth and voltage range.

                Returns
                -------
                numpy.ndarray or pint.Quantity
                    Integer ADC codes when digitization is enabled.
                    Otherwise the original signal is returned unchanged.
            )pbdoc"
        )

        .def(
            "process_signal",
            [ureg](Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector = Casting::cast_py_to_vector<double>(signal, "volt");

                self.process_signal(signal_vector);

                if (!self.should_digitize()) {
                    return py::array_t<double>(signal_vector.size(), signal_vector.data()) * ureg.attr("volt");
                }

                if (self.output_signed_codes) {
                    py::array_t<int64_t> output_array(signal_vector.size());
                    auto output_view = output_array.mutable_unchecked<1>();

                    for (ssize_t index = 0; index < static_cast<ssize_t>(signal_vector.size()); ++index) {
                        const double sample = signal_vector[static_cast<size_t>(index)];

                        if (std::isnan(sample)) {
                            throw std::runtime_error("Processed integer output cannot represent NaN values.");
                        }

                        output_view(index) = static_cast<int64_t>(std::llround(sample));
                    }

                    return output_array;
                }

                py::array_t<uint64_t> output_array(signal_vector.size());
                auto output_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(signal_vector.size()); ++index) {
                    const double sample = signal_vector[static_cast<size_t>(index)];

                    if (std::isnan(sample)) {
                        throw std::runtime_error("Processed integer output cannot represent NaN values.");
                    }

                    const int64_t code_value = static_cast<int64_t>(std::llround(sample));

                    if (code_value < 0) {
                        throw std::runtime_error("Unsigned digitizer output encountered a negative code.");
                    }

                    output_view(index) = static_cast<uint64_t>(code_value);
                }

                return output_array;
            },
            py::arg("signal"),
            R"pbdoc(
                Process a signal using the persistent ``use_auto_range`` setting.

                Processing order:

                1. optional automatic range inference
                2. clipping
                3. digitization
            )pbdoc"
        )
        .def(
            "capture_signal",
            [](Digitizer& self, const py::object& signal) {
                self.capture_signal(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Update internal range information using the persistent ``use_auto_range`` setting.
            )pbdoc"
        )

        .def(
            "capture_signal",
            [](Digitizer& self, const py::object& signal, const bool use_auto_range) {
                self.capture_signal(
                    Casting::cast_py_to_vector<double>(signal, "volt"),
                    use_auto_range
                );
            },
            py::arg("signal"),
            py::arg("use_auto_range"),
            R"pbdoc(
                Update internal range information with an explicit automatic range inference override.
            )pbdoc"
        )

        .def(
            "digitize_data_dict",
            [ureg](const Digitizer& self, const py::dict& data_dict) -> py::object {
                const bool is_nested_trigger_dict =
                    !data_dict.empty() &&
                    !data_dict.contains("Time");

                if (!is_nested_trigger_dict) {
                    std::map<std::string, std::vector<double>> input_data_map;

                    for (const auto& item : data_dict) {
                        const std::string key =
                            py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

                        if (key == "Time") {
                            input_data_map[key] = Casting::cast_py_to_vector<double>(
                                py::reinterpret_borrow<py::object>(item.second),
                                "second"
                            );
                        }
                        else {
                            input_data_map[key] = Casting::cast_py_to_vector<double>(
                                py::reinterpret_borrow<py::object>(item.second),
                                "volt"
                            );
                        }
                    }

                    const std::map<std::string, std::vector<double>> processed_data_map =
                        self.get_processed_data_map(input_data_map);

                    py::dict output_dict;

                    for (const auto& [channel_name, channel_signal] : processed_data_map) {
                        if (channel_name == "Time") {
                            output_dict[py::str(channel_name)] = data_dict[py::str(channel_name)];
                            continue;
                        }

                        if (!self.should_digitize()) {
                            output_dict[py::str(channel_name)] =
                                py::array_t<double>(
                                    channel_signal.size(),
                                    channel_signal.data()
                                ) * ureg.attr("volt");
                            continue;
                        }

                        if (self.output_signed_codes) {
                            py::array_t<int64_t> output_array(channel_signal.size());
                            auto output_view = output_array.mutable_unchecked<1>();

                            for (ssize_t index = 0; index < static_cast<ssize_t>(channel_signal.size()); ++index) {
                                const double sample = channel_signal[static_cast<size_t>(index)];

                                if (std::isnan(sample)) {
                                    throw std::runtime_error(
                                        "Digitized integer output cannot represent NaN values."
                                    );
                                }

                                output_view(index) = static_cast<int64_t>(std::llround(sample));
                            }

                            output_dict[py::str(channel_name)] = output_array;
                            continue;
                        }

                        py::array_t<uint64_t> output_array(channel_signal.size());
                        auto output_view = output_array.mutable_unchecked<1>();

                        for (ssize_t index = 0; index < static_cast<ssize_t>(channel_signal.size()); ++index) {
                            const double sample = channel_signal[static_cast<size_t>(index)];

                            if (std::isnan(sample)) {
                                throw std::runtime_error(
                                    "Digitized integer output cannot represent NaN values."
                                );
                            }

                            const int64_t code_value = static_cast<int64_t>(std::llround(sample));

                            if (code_value < 0) {
                                throw std::runtime_error(
                                    "Unsigned digitizer output encountered a negative code."
                                );
                            }

                            output_view(index) = static_cast<uint64_t>(code_value);
                        }

                        output_dict[py::str(channel_name)] = output_array;
                    }

                    return output_dict;
                }

                py::dict output_segment_dict;

                for (const auto& segment_item : data_dict) {
                    py::object segment_id =
                        py::reinterpret_borrow<py::object>(segment_item.first);
                    py::dict segment_dict =
                        py::reinterpret_borrow<py::dict>(segment_item.second);

                    if (!segment_dict.contains("Time")) {
                        throw std::runtime_error(
                            "Each triggered segment dictionary must contain a 'Time' key."
                        );
                    }

                    std::map<std::string, std::vector<double>> input_data_map;

                    for (const auto& channel_item : segment_dict) {
                        const std::string key =
                            py::reinterpret_borrow<py::object>(channel_item.first).cast<std::string>();

                        if (key == "Time") {
                            input_data_map[key] = Casting::cast_py_to_vector<double>(
                                py::reinterpret_borrow<py::object>(channel_item.second),
                                "second"
                            );
                        }
                        else {
                            input_data_map[key] = Casting::cast_py_to_vector<double>(
                                py::reinterpret_borrow<py::object>(channel_item.second),
                                "volt"
                            );
                        }
                    }

                    const std::map<std::string, std::vector<double>> processed_data_map =
                        self.get_processed_data_map(input_data_map);

                    py::dict output_channel_dict;

                    for (const auto& [channel_name, channel_signal] : processed_data_map) {
                        if (channel_name == "Time") {
                            output_channel_dict[py::str(channel_name)] =
                                segment_dict[py::str(channel_name)];
                            continue;
                        }

                        if (!self.should_digitize()) {
                            output_channel_dict[py::str(channel_name)] =
                                py::array_t<double>(
                                    channel_signal.size(),
                                    channel_signal.data()
                                ) * ureg.attr("volt");
                            continue;
                        }

                        if (self.output_signed_codes) {
                            py::array_t<int64_t> output_array(channel_signal.size());
                            auto output_view = output_array.mutable_unchecked<1>();

                            for (ssize_t index = 0; index < static_cast<ssize_t>(channel_signal.size()); ++index) {
                                const double sample = channel_signal[static_cast<size_t>(index)];

                                if (std::isnan(sample)) {
                                    throw std::runtime_error(
                                        "Digitized integer output cannot represent NaN values."
                                    );
                                }

                                output_view(index) = static_cast<int64_t>(std::llround(sample));
                            }

                            output_channel_dict[py::str(channel_name)] = output_array;
                            continue;
                        }

                        py::array_t<uint64_t> output_array(channel_signal.size());
                        auto output_view = output_array.mutable_unchecked<1>();

                        for (ssize_t index = 0; index < static_cast<ssize_t>(channel_signal.size()); ++index) {
                            const double sample = channel_signal[static_cast<size_t>(index)];

                            if (std::isnan(sample)) {
                                throw std::runtime_error(
                                    "Digitized integer output cannot represent NaN values."
                                );
                            }

                            const int64_t code_value = static_cast<int64_t>(std::llround(sample));

                            if (code_value < 0) {
                                throw std::runtime_error(
                                    "Unsigned digitizer output encountered a negative code."
                                );
                            }

                            output_view(index) = static_cast<uint64_t>(code_value);
                        }

                        output_channel_dict[py::str(channel_name)] = output_array;
                    }

                    output_segment_dict[segment_id] = output_channel_dict;
                }

                return output_segment_dict;
            },
            py::arg("data_dict"),
            R"pbdoc(
                Digitize acquisition data stored in a dictionary.

                Supported input formats
                -----------------------
                Flat acquisition dictionary:
                    {
                        "Time": time_quantity,
                        "DetectorA": voltage_quantity,
                        ...
                    }

                Nested triggered dictionary:
                    {
                        0: {
                            "Time": time_quantity,
                            "DetectorA": voltage_quantity,
                            ...
                        },
                        1: {
                            "Time": time_quantity,
                            "DetectorA": voltage_quantity,
                            ...
                        },
                        ...
                    }

                The ``Time`` entry is always copied unchanged. All detector channels are
                processed in C++. If digitization is disabled, processed detector channels
                are returned as volt quantities. If digitization is enabled, detector
                channels are returned as integer ADC codes.
            )pbdoc"
        )

        .def(
            "get_time_series",
            [ureg](const Digitizer& self, const py::object& run_time) -> py::object {
                const std::vector<double> time_series = self.get_time_series(
                    Casting::cast_py_to_scalar<double>(
                        run_time,
                        "run_time",
                        "second"
                    )
                );

                return py::array_t<double>(
                    time_series.size(),
                    time_series.data()
                ) * ureg.attr("second");
            },
            py::arg("run_time"),
            R"pbdoc(
                Return the sampling time axis for a given acquisition duration.
            )pbdoc"
        )

        .def(
            "__repr__",
            [](const Digitizer& self) {
                return
                    "Digitizer("
                    "bandwidth=" + (
                        std::isnan(self.bandwidth) ? std::string("None") : std::to_string(self.bandwidth)
                    ) +
                    ", sampling_rate=" + std::to_string(self.sampling_rate) +
                    ", bit_depth=" + std::to_string(self.bit_depth) +
                    ", min_voltage=" + (
                        std::isnan(self.min_voltage) ? std::string("None") : std::to_string(self.min_voltage)
                    ) +
                    ", max_voltage=" + (
                        std::isnan(self.max_voltage) ? std::string("None") : std::to_string(self.max_voltage)
                    ) +
                    ", use_auto_range=" + std::string(self.use_auto_range ? "True" : "False") +
                    ", output_signed_codes=" + std::string(self.output_signed_codes ? "True" : "False") +
                    ")";
            }
        );
}
