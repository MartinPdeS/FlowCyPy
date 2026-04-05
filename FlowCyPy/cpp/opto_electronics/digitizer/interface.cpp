#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <cmath>
#include <cstdint>
#include <limits>
#include <map>
#include <string>
#include <utility>
#include <vector>

#include "digitizer.h"
#include <utils/casting.h>
#include <pint/pint.h>

namespace py = pybind11;


namespace {

inline bool is_metadata_channel(const std::string& channel_name) {
    return channel_name == "Time" || channel_name == "segment_id";
}

ChannelRangeMode parse_channel_range_mode(const std::string& value) {
    if (value == "shared") {
        return ChannelRangeMode::shared;
    }

    if (value == "per_channel") {
        return ChannelRangeMode::per_channel;
    }

    throw std::invalid_argument(
        "channel_range_mode must be one of {'shared', 'per_channel'}."
    );
}


std::string channel_range_mode_to_string(const ChannelRangeMode value) {
    if (value == ChannelRangeMode::shared) {
        return "shared";
    }

    return "per_channel";
}


py::object as_voltage_quantity(
    const py::object& unit_registry,
    const std::vector<double>& values
) {
    return py::array_t<double>(values.size(), values.data()) * unit_registry.attr("volt");
}


py::object as_time_quantity(
    const py::object& unit_registry,
    const std::vector<double>& values
) {
    return py::array_t<double>(values.size(), values.data()) * unit_registry.attr("second");
}


py::object as_voltage_quantity(
    const py::object& unit_registry,
    const double value
) {
    return (py::float_(value) * unit_registry.attr("volt")).attr("to_compact")();
}


std::map<std::string, std::vector<double>> cast_py_dict_to_flat_data_map(
    const py::dict& data_dict
) {
    std::map<std::string, std::vector<double>> input_data_map;

    for (const auto& item : data_dict) {
        const std::string channel_name = py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

        const py::object channel_object = py::reinterpret_borrow<py::object>(item.second);

        if (channel_name == "segment_id") {
            input_data_map[channel_name] = Casting::cast_py_to_vector<double>(
                channel_object,
                channel_name
            );
        }
        else if (channel_name == "Time") {
            input_data_map[channel_name] = Casting::cast_py_to_vector<double>(
                channel_object,
                channel_name,
                "second"
            );
        }
        else {
            input_data_map[channel_name] = Casting::cast_py_to_vector<double>(
                channel_object,
                channel_name,
                "volt"
            );
        }
    }

    return input_data_map;
}

std::map<std::string, std::map<std::string, std::vector<double>>> cast_py_dict_to_nested_data_map(
    const py::dict& data_dict
) {
    std::map<std::string, std::map<std::string, std::vector<double>>> nested_data_map;

    for (const auto& segment_item : data_dict) {
        const std::string segment_identifier = py::str(py::reinterpret_borrow<py::object>(segment_item.first));

        const py::dict segment_dict = py::reinterpret_borrow<py::dict>(segment_item.second);

        nested_data_map[segment_identifier] = cast_py_dict_to_flat_data_map(segment_dict);
    }

    return nested_data_map;
}


py::dict build_python_output_dict_from_processed_double_map(
    const py::object& unit_registry,
    const py::dict& input_data_dict,
    const std::map<std::string, std::vector<double>>& processed_data_map
) {
    py::dict output_dict;

    for (const auto& [channel_name, channel_signal] : processed_data_map) {
        if (is_metadata_channel(channel_name)) {
            output_dict[py::str(channel_name)] = input_data_dict[py::str(channel_name)];
            continue;
        }

        output_dict[py::str(channel_name)] = py::array_t<double>(channel_signal.size(), channel_signal.data()) * unit_registry.attr("volt");
    }

    return output_dict;
}


py::dict build_python_output_dict_from_processed_signed_map(
    const py::dict& input_data_dict,
    const std::map<std::string, std::vector<int64_t>>& processed_data_map
) {
    py::dict output_dict;

    if (input_data_dict.contains("Time")) {
        output_dict[py::str("Time")] = input_data_dict[py::str("Time")];
    }

    if (input_data_dict.contains("segment_id")) {
        output_dict[py::str("segment_id")] = input_data_dict[py::str("segment_id")];
    }

    for (const auto& [channel_name, channel_signal] : processed_data_map) {
        if (is_metadata_channel(channel_name)) {
            continue;
        }

        output_dict[py::str(channel_name)] =
            py::array_t<int64_t>(channel_signal.size(), channel_signal.data());
    }

    return output_dict;
}


py::dict build_python_output_dict_from_processed_unsigned_map(
    const py::dict& input_data_dict,
    const std::map<std::string, std::vector<uint64_t>>& processed_data_map
) {
    py::dict output_dict;

    if (input_data_dict.contains("Time")) {
        output_dict[py::str("Time")] = input_data_dict[py::str("Time")];
    }

    if (input_data_dict.contains("segment_id")) {
        output_dict[py::str("segment_id")] = input_data_dict[py::str("segment_id")];
    }

    for (const auto& [channel_name, channel_signal] : processed_data_map) {
        if (is_metadata_channel(channel_name)) {
            continue;
        }

        output_dict[py::str(channel_name)] =
            py::array_t<uint64_t>(channel_signal.size(), channel_signal.data());
    }

    return output_dict;
}


py::object digitize_python_data_dict(
    const Digitizer& self,
    const py::object& unit_registry,
    const py::dict& data_dict
) {

    const std::map<std::string, std::vector<double>> input_data_map =
        cast_py_dict_to_flat_data_map(data_dict);

    if (!self.should_digitize()) {
        const std::map<std::string, std::vector<double>> processed_data_map =
            self.process_flat_acquisition_data(input_data_map);

        return build_python_output_dict_from_processed_double_map(
            unit_registry,
            data_dict,
            processed_data_map
        );
    }

    if (self.output_signed_codes) {
        const std::map<std::string, std::vector<int64_t>> processed_data_map =
            self.get_processed_signed_data_map(input_data_map);

        return build_python_output_dict_from_processed_signed_map(
            data_dict,
            processed_data_map
        );
    }

    const std::map<std::string, std::vector<uint64_t>> processed_data_map =
        self.get_processed_unsigned_data_map(input_data_map);

    return build_python_output_dict_from_processed_unsigned_map(
        data_dict,
        processed_data_map
    );

}

}  // namespace


PYBIND11_MODULE(digitizer, module) {
    py::object unit_registry = get_shared_ureg();

    module.doc() = R"pbdoc(
        FlowCyPy digitizer interface.

        This module exposes a digitizer model that can clip voltage signals,
        infer voltage ranges, quantize detector traces into integer ADC code
        values, and process channel dictionaries using either a shared
        automatically inferred range, a per channel automatically inferred
        range, or explicit per channel overrides.

        Signals are expected to be Pint quantities compatible with volts.
        Time axes are expected to be Pint quantities compatible with seconds.
    )pbdoc";

    py::class_<Digitizer>(
        module,
        "Digitizer",
        R"pbdoc(
            Digitize and clip voltage signals.

            The ``Digitizer`` class models a digitization stage for detector
            voltage signals. It supports optional clipping, optional automatic
            range inference, and quantization to either unsigned or signed
            integer like ADC codes.

            Two settings control range selection:

            ``use_auto_range``
                Select whether ranges are inferred from the data or taken from
                the fixed instance level ``min_voltage`` and ``max_voltage``.

            ``channel_range_mode``
                When ``use_auto_range`` is enabled, controls whether automatic
                range inference is shared across channels or done independently
                for each channel.

            Explicit channel ranges set with
            :meth:`set_channel_voltage_range` always take precedence over the
            automatic or fixed instance level policy.

            Parameters
            ----------
            sampling_rate : pint.Quantity
                Sampling rate in hertz.
            bandwidth : pint.Quantity or None, default=None
                Digitizer bandwidth in hertz. If ``None``, bandwidth remains unset.
            bit_depth : int, default=0
                Number of quantization bits. A value of ``0`` disables digitization.
            min_voltage : pint.Quantity or None, default=None
                Minimum clipping voltage used when a fixed range is required.
            max_voltage : pint.Quantity or None, default=None
                Maximum clipping voltage used when a fixed range is required.
            use_auto_range : bool, default=False
                If ``True``, infer voltage ranges automatically from the signal data.
            output_signed_codes : bool, default=False
                If ``True``, digitized outputs use signed integer like code values.
            debug_mode : bool, default=False
                If ``True``, print debug information during processing.
            channel_range_mode : {"shared", "per_channel"}, default="shared"
                Automatic range scope used when ``use_auto_range`` is enabled.
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
                const bool debug_mode,
                const std::string& channel_range_mode
            ) {
                const double sampling_rate_value = Casting::cast_py_to_scalar<double>(
                    sampling_rate,
                    "sampling_rate",
                    "hertz"
                );

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
                    debug_mode,
                    parse_channel_range_mode(channel_range_mode)
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
            py::arg("channel_range_mode") = "shared",
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
                    Minimum clipping voltage in volts when using a fixed range.
                max_voltage : pint.Quantity or None, default=None
                    Maximum clipping voltage in volts when using a fixed range.
                use_auto_range : bool, default=False
                    If ``True``, infer voltage ranges from the processed signal data.
                output_signed_codes : bool, default=False
                    If ``True``, return signed integer like ADC code values.
                debug_mode : bool, default=False
                    If ``True``, print debug information during processing.
                channel_range_mode : {"shared", "per_channel"}, default="shared"
                    Automatic range scope when ``use_auto_range`` is enabled.
            )pbdoc"
        )

        .def("has_bandwidth", &Digitizer::has_bandwidth,
            R"pbdoc(
                Return whether a bandwidth is defined.

                Returns
                -------
                bool
                    ``True`` if ``bandwidth`` is set, otherwise ``False``.
            )pbdoc"
        )

        .def("has_voltage_range", &Digitizer::has_voltage_range,
            R"pbdoc(
                Return whether the instance level fixed voltage range is defined.

                Returns
                -------
                bool
                    ``True`` if both ``min_voltage`` and ``max_voltage`` are set.
            )pbdoc"
        )

        .def("should_digitize", &Digitizer::should_digitize,
            R"pbdoc(
                Return whether digitization is enabled.

                Returns
                -------
                bool
                    ``True`` if ``bit_depth`` is greater than zero.
            )pbdoc"
        )

        .def("has_signed_output_codes", &Digitizer::has_signed_output_codes,
            R"pbdoc(
                Return whether signed output codes are enabled.

                Returns
                -------
                bool
                    ``True`` if signed integer ADC codes are requested.
            )pbdoc"
        )

        .def("clear_bandwidth", &Digitizer::clear_bandwidth,
            R"pbdoc(
                Clear the configured bandwidth.

                After this call, ``bandwidth`` becomes undefined.
            )pbdoc"
        )

        .def("clear_voltage_range", &Digitizer::clear_voltage_range,
            R"pbdoc(
                Clear the instance level fixed voltage range.

                After this call, both ``min_voltage`` and ``max_voltage`` become undefined.
                Explicit per channel ranges are not modified.
            )pbdoc"
        )

        .def("get_minimum_code", &Digitizer::get_minimum_code,
            R"pbdoc(
                Return the minimum ADC code value.

                Returns
                -------
                int
                    Minimum representable code value for the current digitizer settings.

                Raises
                ------
                RuntimeError
                    If digitization is disabled.
            )pbdoc"
        )

        .def("get_maximum_code", &Digitizer::get_maximum_code,
            R"pbdoc(
                Return the maximum ADC code value.

                Returns
                -------
                int
                    Maximum representable code value for the current digitizer settings.

                Raises
                ------
                RuntimeError
                    If digitization is disabled.
            )pbdoc"
        )

        .def_property(
            "channel_range_mode",
            [](const Digitizer& self) {
                return channel_range_mode_to_string(self.channel_range_mode);
            },
            [](Digitizer& self, const std::string& value) {
                self.channel_range_mode = parse_channel_range_mode(value);
            },
            R"pbdoc(
                Automatic range scope for dictionary based channel processing.

                Allowed values are:

                ``"shared"``
                    Infer one shared range across all detector channels without
                    explicit channel overrides.

                ``"per_channel"``
                    Infer one independent range for each detector channel without
                    explicit channel overrides.

                Notes
                -----
                This property only affects processing when ``use_auto_range`` is ``True``.
                When ``use_auto_range`` is ``False``, the instance level
                ``min_voltage`` and ``max_voltage`` are used instead.
            )pbdoc"
        )
        .def_property(
            "bandwidth",
            [unit_registry](const Digitizer& self) -> py::object {
                if (std::isnan(self.bandwidth)) {
                    return py::none();
                }

                return (py::float_(self.bandwidth) * unit_registry.attr("hertz")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.bandwidth = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "bandwidth",
                    "hertz"
                );

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
            [unit_registry](const Digitizer& self) -> py::object {
                return (py::float_(self.sampling_rate) * unit_registry.attr("hertz")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.sampling_rate = Casting::cast_py_to_scalar<double>(
                    value,
                    "sampling_rate",
                    "hertz"
                );

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
                if (value > 63) {
                    throw std::invalid_argument(
                        "Digitizer bit_depth must be smaller than or equal to 63."
                    );
                }

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
                Whether voltage ranges are inferred automatically from the data.

                When ``False``, processing uses the fixed instance level
                ``min_voltage`` and ``max_voltage``, unless an explicit channel
                override is present.

                When ``True``, processing infers ranges from the signal data.
                The scope of that inference is controlled by ``channel_range_mode``.
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
            [unit_registry](const Digitizer& self) -> py::object {
                if (std::isnan(self.min_voltage)) {
                    return py::none();
                }

                return (py::float_(self.min_voltage) * unit_registry.attr("volt")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.min_voltage = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "min_voltage",
                    "volt"
                );

                if (
                    !std::isnan(self.min_voltage) &&
                    !std::isnan(self.max_voltage) &&
                    self.max_voltage <= self.min_voltage
                ) {
                    throw std::invalid_argument(
                        "Digitizer requires max_voltage to be greater than min_voltage."
                    );
                }
            },
            R"pbdoc(
                Instance level fixed minimum clipping voltage.

                Returns
                -------
                pint.Quantity or None
                    Minimum clipping voltage in volts, or ``None`` if unset.

                Notes
                -----
                This value is used only when ``use_auto_range`` is ``False``,
                unless an explicit per channel range overrides it.
            )pbdoc"
        )

        .def_property(
            "max_voltage",
            [unit_registry](const Digitizer& self) -> py::object {
                if (std::isnan(self.max_voltage)) {
                    return py::none();
                }

                return (py::float_(self.max_voltage) * unit_registry.attr("volt")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.max_voltage = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "max_voltage",
                    "volt"
                );

                if (
                    !std::isnan(self.min_voltage) &&
                    !std::isnan(self.max_voltage) &&
                    self.max_voltage <= self.min_voltage
                ) {
                    throw std::invalid_argument(
                        "Digitizer requires max_voltage to be greater than min_voltage."
                    );
                }
            },
            R"pbdoc(
                Instance level fixed maximum clipping voltage.

                Returns
                -------
                pint.Quantity or None
                    Maximum clipping voltage in volts, or ``None`` if unset.

                Notes
                -----
                This value is used only when ``use_auto_range`` is ``False``,
                unless an explicit per channel range overrides it.
            )pbdoc"
        )
        .def(
            "set_channel_voltage_range",
            [](Digitizer& self,
               const std::string& channel_name,
               const py::object& minimum_voltage,
               const py::object& maximum_voltage) {
                self.set_channel_voltage_range(
                    channel_name,
                    Casting::cast_py_to_scalar<double>(minimum_voltage, "minimum_voltage", "volt"),
                    Casting::cast_py_to_scalar<double>(maximum_voltage, "maximum_voltage", "volt")
                );
            },
            py::arg("channel_name"),
            py::arg("minimum_voltage"),
            py::arg("maximum_voltage"),
            R"pbdoc(
                Set an explicit voltage range for one detector channel.

                Parameters
                ----------
                channel_name : str
                    Name of the detector channel.
                minimum_voltage : pint.Quantity
                    Minimum voltage bound. Must be compatible with volts.
                maximum_voltage : pint.Quantity
                    Maximum voltage bound. Must be compatible with volts.

                Notes
                -----
                Explicit channel ranges always take precedence over the global
                processing policy.

                Examples
                --------
                ``digitizer.set_channel_voltage_range("forward", -0.2 * ureg.volt, 1.5 * ureg.volt)``
            )pbdoc"
        )
        .def(
            "clear_channel_voltage_range",
            &Digitizer::clear_channel_voltage_range,
            py::arg("channel_name"),
            R"pbdoc(
                Clear the explicit voltage range for one detector channel.

                Parameters
                ----------
                channel_name : str
                    Name of the detector channel.
            )pbdoc"
        )
        .def(
            "clear_all_channel_voltage_ranges",
            &Digitizer::clear_all_channel_voltage_ranges,
            R"pbdoc(
                Clear all explicit per channel voltage ranges.
            )pbdoc"
        )
        .def(
            "has_channel_voltage_range",
            &Digitizer::has_channel_voltage_range,
            py::arg("channel_name"),
            R"pbdoc(
                Return whether a channel has an explicit voltage range.

                Parameters
                ----------
                channel_name : str
                    Name of the detector channel.

                Returns
                -------
                bool
                    ``True`` if the channel has an explicit range override.
            )pbdoc"
        )

        .def(
            "get_channel_voltage_range",
            [unit_registry](const Digitizer& self, const std::string& channel_name) {
                const auto [minimum_voltage, maximum_voltage] =
                    self.get_channel_voltage_range(channel_name);

                return py::make_tuple(
                    as_voltage_quantity(unit_registry, minimum_voltage),
                    as_voltage_quantity(unit_registry, maximum_voltage)
                );
            },
            py::arg("channel_name"),
            R"pbdoc(
                Return the explicit voltage range of a channel.

                Parameters
                ----------
                channel_name : str
                    Name of the detector channel.

                Returns
                -------
                tuple[pint.Quantity, pint.Quantity]
                    Minimum and maximum voltage bounds in volts.

                Raises
                ------
                RuntimeError
                    If the channel has no explicit range override.
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
                Infer and store the instance level voltage range from one signal.

                The minimum and maximum finite values of the input signal are used
                to update ``min_voltage`` and ``max_voltage``.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.
            )pbdoc"
        )

        .def(
            "get_min_max",
            [unit_registry](const Digitizer& self, const py::object& signal) {
                const auto [minimum_value, maximum_value] = self.get_min_max(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );

                return py::make_tuple(
                    as_voltage_quantity(unit_registry, minimum_value),
                    as_voltage_quantity(unit_registry, maximum_value)
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Return the minimum and maximum finite values of a signal.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.

                Returns
                -------
                tuple[pint.Quantity, pint.Quantity]
                    Minimum and maximum finite values in volts.
            )pbdoc"
        )

        .def(
            "clip_signal",
            [unit_registry](const Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector =
                    Casting::cast_py_to_vector<double>(signal, "volt");

                self.clip_signal(signal_vector);

                return as_voltage_quantity(unit_registry, signal_vector);
            },
            py::arg("signal"),
            R"pbdoc(
                Clip a signal to the instance level fixed voltage range.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.

                Returns
                -------
                pint.Quantity
                    Clipped voltage signal.

                Notes
                -----
                This method uses only the instance level ``min_voltage`` and
                ``max_voltage``.
            )pbdoc"
        )

        .def(
            "process_signal",
            [unit_registry](Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector =
                    Casting::cast_py_to_vector<double>(signal, "volt");

                self.process_signal(signal_vector);

                if (!self.should_digitize()) {
                    return as_voltage_quantity(unit_registry, signal_vector);
                }

                if (self.output_signed_codes) {
                    const std::vector<int64_t> output_signal =
                        self.convert_signal_to_signed_codes(signal_vector);

                    return py::array_t<int64_t>(output_signal.size(), output_signal.data());
                }

                const std::vector<uint64_t> output_signal =
                    self.convert_signal_to_unsigned_codes(signal_vector);

                return py::array_t<uint64_t>(output_signal.size(), output_signal.data());
            },
            py::arg("signal"),
            R"pbdoc(
                Process one signal.

                Processing order:

                1. choose a fixed or automatically inferred range
                2. clip using that range
                3. digitize

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.

                Returns
                -------
                pint.Quantity or numpy.ndarray
                    If digitization is disabled, returns a voltage quantity.
                    Otherwise returns an integer code array.
            )pbdoc"
        )
        .def(
            "capture_signal",
            [](Digitizer& self, const py::object& signal) {
                self.capture_signal(
                    Casting::cast_py_to_vector<double>(signal, "signal", "volt")
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Update internal range information using the persistent ``use_auto_range`` setting.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.
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
                Update internal range information with an explicit auto range override.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.
                use_auto_range : bool
                    If ``True``, infer and store the signal min and max as the
                    instance level voltage range.
            )pbdoc"
        )
        .def(
            "digitize_signal",
            [](const Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector =
                    Casting::cast_py_to_vector<double>(signal, "volt");

                self.digitize_signal(signal_vector);

                if (!self.should_digitize()) {
                    return py::array_t<double>(signal_vector.size(), signal_vector.data());
                }

                if (self.output_signed_codes) {
                    const std::vector<int64_t> output_signal =
                        self.convert_signal_to_signed_codes(signal_vector);

                    return py::array_t<int64_t>(output_signal.size(), output_signal.data());
                }

                const std::vector<uint64_t> output_signal =
                    self.convert_signal_to_unsigned_codes(signal_vector);

                return py::array_t<uint64_t>(output_signal.size(), output_signal.data());
            },
            py::arg("signal"),
            R"pbdoc(
                Digitize one voltage signal using the instance level fixed voltage range.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional voltage signal.

                Returns
                -------
                numpy.ndarray
                    Integer ADC code array if digitization is enabled.
                    If digitization is disabled, the returned array contains the
                    unchanged floating point samples.

                Notes
                -----
                This method does not perform automatic range inference.
            )pbdoc"
        )
        .def(
            "digitize_data_dict",
            [unit_registry](const Digitizer& self, const py::dict& data_dict) -> py::object {
                const std::map<std::string, std::vector<double>> input_data_map = cast_py_dict_to_flat_data_map(data_dict);

                if (!self.should_digitize()) {
                    const std::map<std::string, std::vector<double>> processed_data_map = self.process_flat_acquisition_data(input_data_map);

                    return build_python_output_dict_from_processed_double_map(
                        unit_registry,
                        data_dict,
                        processed_data_map
                    );
                }

                if (self.output_signed_codes) {
                    const std::map<std::string, std::vector<int64_t>> processed_data_map = self.get_processed_signed_data_map(input_data_map);

                    return build_python_output_dict_from_processed_signed_map(
                        data_dict,
                        processed_data_map
                    );
                }

                const std::map<std::string, std::vector<uint64_t>> processed_data_map = self.get_processed_unsigned_data_map(input_data_map);

                return build_python_output_dict_from_processed_unsigned_map(
                    data_dict,
                    processed_data_map
                );
            },
            py::arg("data_dict"),
            R"pbdoc(
                Process acquisition data stored in a dictionary.

                Supported input formats
                -----------------------
                Flat acquisition dictionary:
                    {
                        "Time": time_quantity,
                        "DetectorA": voltage_quantity,
                        ...
                    }

                Flat acquisition dictionaries may also contain metadata fields
                such as ``"segment_id"``. Metadata fields are copied through
                unchanged and are never used for voltage range inference.

                Range resolution order
                ----------------------
                For each detector channel, the applied range is chosen in this order:

                1. explicit channel range set with :meth:`set_channel_voltage_range`
                2. if ``use_auto_range`` is ``True``:
                   a. shared inferred range when ``channel_range_mode == "shared"``
                   b. per channel inferred range when ``channel_range_mode == "per_channel"``
                3. if ``use_auto_range`` is ``False``:
                   instance level ``min_voltage`` and ``max_voltage``

                Parameters
                ----------
                data_dict : dict
                    Acquisition data dictionary using Pint quantities.

                Returns
                -------
                dict
                    Dictionary with processed detector channels.
                    Metadata fields such as ``Time`` and ``segment_id`` are copied unchanged.
                    If digitization is disabled, detector channels are returned
                    as voltage quantities.
                    If digitization is enabled, detector channels are returned
                    as integer ADC code arrays.
            )pbdoc"
        )
        .def(
            "get_time_series",
            [unit_registry](const Digitizer& self, const py::object& run_time) -> py::object {
                const std::vector<double> time_series = self.get_time_series(
                    Casting::cast_py_to_scalar<double>(
                        run_time,
                        "run_time",
                        "second"
                    )
                );

                return as_time_quantity(unit_registry, time_series);
            },
            py::arg("run_time"),
            R"pbdoc(
                Return the sampling time axis for a given acquisition duration.

                Parameters
                ----------
                run_time : pint.Quantity
                    Acquisition duration in seconds.

                Returns
                -------
                pint.Quantity
                    Sampling time axis in seconds.
            )pbdoc"
        )
        .def(
            "__repr__",
            [](const Digitizer& self) {
                return self.repr();
            }
        );
}
