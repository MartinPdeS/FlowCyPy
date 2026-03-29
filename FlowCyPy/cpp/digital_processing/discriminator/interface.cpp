#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "discriminator.h"
#include <pint/pint.h>

namespace py = pybind11;

PYBIND11_MODULE(discriminator, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"pbdoc(
        Signal Discrimination System.

        Provides an efficient framework for threshold based and dynamic
        window discrimination of signals, with support for debouncing,
        pre/post buffering, and segment extraction.
    )pbdoc";

    py::class_<Threshold>(module, "Threshold")
        .def(py::init<>())
        .def(py::init<double>(), py::arg("numeric_value"))
        .def(py::init<const std::string &>(), py::arg("symbolic_value"))
        .def(
            py::init<double, const std::string &>(),
            py::arg("numeric_value"),
            py::arg("symbolic_value")
        )
        .def(
            "set_numeric",
            &Threshold::set_numeric,
            py::arg("value"),
            R"pbdoc(
                Set or replace the numeric threshold value.
            )pbdoc"
        )
        .def(
            "set_symbolic",
            &Threshold::set_symbolic,
            py::arg("value"),
            R"pbdoc(
                Set or replace the symbolic threshold expression.
            )pbdoc"
        )
        .def(
            "clear_numeric",
            &Threshold::clear_numeric,
            R"pbdoc(
                Remove the numeric threshold value.
            )pbdoc"
        )
        .def(
            "clear_symbolic",
            &Threshold::clear_symbolic,
            R"pbdoc(
                Remove the symbolic threshold expression.
            )pbdoc"
        )
        .def(
            "clear",
            &Threshold::clear,
            R"pbdoc(
                Remove both numeric and symbolic threshold values.
            )pbdoc"
        )
        .def_property_readonly(
            "has_numeric",
            &Threshold::has_numeric,
            R"pbdoc(
                Return True if a numeric value is available.
            )pbdoc"
        )
        .def_property_readonly(
            "has_symbolic",
            &Threshold::has_symbolic,
            R"pbdoc(
                Return True if a symbolic value is available.
            )pbdoc"
        )
        .def_property_readonly(
            "is_defined",
            &Threshold::is_defined,
            R"pbdoc(
                Return True if the threshold contains at least one value.
            )pbdoc"
        )
        .def_property_readonly(
            "numeric",
            [ureg](const Threshold &self) -> py::object {
                if (!self.has_numeric()) {
                    return py::none();
                }

                return py::cast(self.get_numeric()) * ureg.attr("volt");
            },
            R"pbdoc(
                Numeric threshold value as a Pint quantity in volts, or None.
            )pbdoc"
        )
        .def_property_readonly(
            "symbolic",
            [](const Threshold &self) -> py::object {
                if (!self.has_symbolic()) {
                    return py::none();
                }

                return py::cast(self.get_symbolic());
            },
            R"pbdoc(
                Symbolic threshold expression, or None.
            )pbdoc"
        )
        .def(
            "__repr__",
            [ureg](const Threshold &self) {
                std::string output = "Threshold(";
                bool has_previous = false;

                if (self.has_numeric()) {
                    py::object quantity = py::cast(self.get_numeric()) * ureg.attr("volt");
                    py::object compact_quantity = quantity.attr("to_compact")();
                    output += "numeric=" + py::str(compact_quantity).cast<std::string>();
                    has_previous = true;
                }

                if (self.has_symbolic()) {
                    if (has_previous) {
                        output += ", ";
                    }
                    output += "symbolic='" + self.get_symbolic() + "'";
                }

                output += ")";
                return output;
            }
        );








    py::class_<Trigger>(module, "Trigger")
        .def(py::init<>())
        .def_readonly(
            "global_time",
            &Trigger::global_time,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Global time vector used for all signal operations.

                This aligns one to one with samples in added signals.
            )pbdoc"
        )
        .def(
            "get_segmented_signal",
            &Trigger::get_segmented_signal,
            py::arg("detector_name"),
            R"pbdoc(
                Retrieve the segmented signal values for a specific detector.

                Parameters
                ----------
                detector_name : str
                    Name of the signal detector to retrieve.

                Returns
                -------
                numpy.ndarray
                    One dimensional array of segmented signal values.
            )pbdoc"
        )
        .def_readonly(
            "segmented_time",
            &Trigger::time_out,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Time samples corresponding to the segmented output.

                This is flattened across all detected segments.
            )pbdoc"
        )
        .def_readonly(
            "segment_ids",
            &Trigger::segment_ids_out,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Segment identifier associated with each segmented sample.

                This is flattened across all detected segments.
            )pbdoc"
        );

    py::class_<BaseDiscriminator>(module, "BaseDiscriminator")
        .def_readonly(
            "trigger",
            &BaseDiscriminator::trigger,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Underlying trigger container holding raw and segmented signal data.
            )pbdoc"
        )
        .def_readwrite(
            "trigger_channel",
            &BaseDiscriminator::trigger_channel,
            R"pbdoc(
                Name of the signal channel used for trigger detection.
            )pbdoc"
        )
        .def_readwrite(
            "pre_buffer",
            &BaseDiscriminator::pre_buffer,
            R"pbdoc(
                Number of samples included before the detected trigger position.
            )pbdoc"
        )
        .def_readwrite(
            "post_buffer",
            &BaseDiscriminator::post_buffer,
            R"pbdoc(
                Number of samples included after the detected trigger position.
            )pbdoc"
        )
        .def_readwrite(
            "max_triggers",
            &BaseDiscriminator::max_triggers,
            R"pbdoc(
                Maximum number of triggers to accept.

                A value of -1 disables the limit.
            )pbdoc"
        )
        .def(
            "run_with_dict",
            [ureg](BaseDiscriminator &self, const py::dict &data_dict) {
                if (!data_dict.contains("Time")) {
                    throw std::runtime_error("Input dictionary must contain a 'Time' key.");
                }

                const std::vector<double> time_vector =
                    py::reinterpret_borrow<py::object>(data_dict["Time"])
                        .attr("to")("second")
                        .attr("magnitude")
                        .cast<std::vector<double>>();

                self.add_time(time_vector);

                std::vector<std::string> channel_names;
                channel_names.reserve(data_dict.size() > 0 ? data_dict.size() - 1 : 0);

                for (const auto &item : data_dict) {
                    const std::string key =
                        py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

                    if (key == "Time") {
                        continue;
                    }

                    const std::vector<double> signal_vector =
                        py::reinterpret_borrow<py::object>(item.second)
                            .attr("to")("volt")
                            .attr("magnitude")
                            .cast<std::vector<double>>();

                    self.add_signal(key, signal_vector);
                    channel_names.push_back(key);
                }

                if (channel_names.empty()) {
                    throw std::runtime_error(
                        "Input dictionary must contain at least one signal channel in addition to 'Time'."
                    );
                }

                self.run();

                py::module_ numpy = py::module_::import("numpy");

                const std::vector<int> &segment_ids = self.trigger.segment_ids_out;
                const std::vector<double> &segmented_time = self.trigger.time_out;

                if (segment_ids.size() != segmented_time.size()) {
                    throw std::runtime_error(
                        "Segmented output is inconsistent: segment_ids_out and time_out do not have the same length."
                    );
                }

                py::dict final_output;

                final_output["segment_id"] = numpy.attr("array")(segment_ids);
                final_output["Time"] = numpy.attr("array")(segmented_time) * ureg.attr("second");

                for (const std::string &channel_name : channel_names) {
                    const std::vector<double> &segmented_signal =
                        self.trigger.get_segmented_signal(channel_name);

                    if (segmented_signal.size() != segment_ids.size()) {
                        throw std::runtime_error(
                            "Segmented signal size mismatch for channel '" + channel_name + "'."
                        );
                    }

                    final_output[py::str(channel_name)] =
                        numpy.attr("array")(segmented_signal) * ureg.attr("volt");
                }

                return final_output;
            },
            py::arg("data_dict"),
            R"pbdoc(
                Run trigger detection from a dictionary.

                Expected input format
                ---------------------
                {
                    "Time": quantity_array_convertible_to_seconds,
                    "ChannelA": quantity_array_convertible_to_volts,
                    "ChannelB": quantity_array_convertible_to_volts,
                }

                Returns
                -------
                dict
                    Flat dictionary where each entry corresponds to one segmented sample.

                    The output contains:
                    - "segment_id": integer array identifying the segment of each sample
                    - "Time": time array with units of seconds
                    - one array per signal channel with units of volts

                    Example
                    -------
                    {
                        "segment_id": [...],
                        "Time": [...]*second,
                        "ChannelA": [...]*volt,
                        "ChannelB": [...]*volt,
                    }
            )pbdoc"
        )
        ;

    py::class_<FixedWindow, BaseDiscriminator>(module, "FixedWindow")
        .def(
            py::init(
                [](
                    const std::string &trigger_channel,
                    const py::object &threshold,
                    size_t pre_buffer,
                    size_t post_buffer,
                    int max_triggers
                ) {
                    FixedWindow instance(
                        trigger_channel,
                        pre_buffer,
                        post_buffer,
                        max_triggers
                    );

                    if (py::isinstance<py::str>(threshold)) {
                        instance.set_threshold(threshold.cast<std::string>());
                    } else {
                        instance.set_threshold(
                            threshold.attr("to")("volt").attr("magnitude").cast<double>()
                        );
                    }

                    return instance;
                }
            ),
            py::arg("trigger_channel"),
            py::arg("threshold"),
            py::arg("pre_buffer") = 0,
            py::arg("post_buffer") = 0,
            py::arg("max_triggers") = -1,
            R"pbdoc(
                Initialize a FixedWindow trigger detector.
            )pbdoc"
        )
        .def(
            "run",
            &FixedWindow::run,
            R"pbdoc(
                Execute fixed window trigger detection.
            )pbdoc"
        )
        .def_property(
            "threshold",
            [](FixedWindow &self) -> Threshold & {
                return self.threshold;
            },
            [](FixedWindow &self, const py::object &threshold_object) {
                if (py::isinstance<Threshold>(threshold_object)) {
                    self.threshold = threshold_object.cast<Threshold>();
                } else if (py::isinstance<py::str>(threshold_object)) {
                    self.set_threshold(threshold_object.cast<std::string>());
                } else {
                    self.set_threshold(
                        threshold_object.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Threshold object storing the symbolic expression and resolved numeric value.
            )pbdoc"
        )
        .def(
            "_add_to_ax",
            [](FixedWindow &self, py::object ax, py::object signal_units) {
                if (std::isnan(self.resolved_threshold)) {
                    throw std::runtime_error(
                        "Threshold has not been resolved. Run the trigger first."
                    );
                }

                py::module_ pint = py::module_::import("pint");
                py::object quantity =
                    pint.attr("Quantity")(self.resolved_threshold, "volt");
                py::object converted_quantity = quantity.attr("to")(signal_units);

                ax.attr("axhline")(
                    converted_quantity.attr("magnitude"),
                    py::arg("color") = "red",
                    py::arg("linestyle") = "--",
                    py::arg("linewidth") = 1,
                    py::arg("label") = py::str("Threshold: {:.2f}").format(
                        quantity.attr("to_compact")()
                    )
                );

                ax.attr("legend")();
            },
            py::arg("ax"),
            py::arg("signal_units"),
            R"pbdoc(
                Add the resolved threshold to a matplotlib Axes.
            )pbdoc"
        );

    py::class_<DynamicWindow, BaseDiscriminator>(module, "DynamicWindow")
        .def(
            py::init(
                [](
                    const std::string &trigger_channel,
                    const py::object &threshold,
                    size_t pre_buffer,
                    size_t post_buffer,
                    int max_triggers
                ) {
                    DynamicWindow instance(
                        trigger_channel,
                        pre_buffer,
                        post_buffer,
                        max_triggers
                    );

                    if (py::isinstance<py::str>(threshold)) {
                        instance.set_threshold(threshold.cast<std::string>());
                    } else {
                        instance.set_threshold(
                            threshold.attr("to")("volt").attr("magnitude").cast<double>()
                        );
                    }

                    return instance;
                }
            ),
            py::arg("trigger_channel"),
            py::arg("threshold"),
            py::arg("pre_buffer") = 0,
            py::arg("post_buffer") = 0,
            py::arg("max_triggers") = -1,
            R"pbdoc(
                Initialize a DynamicWindow trigger detector.
            )pbdoc"
        )
        .def(
            "run",
            &DynamicWindow::run,
            R"pbdoc(
                Execute dynamic window trigger detection.
            )pbdoc"
        )
        .def_property(
            "threshold",
            [](DynamicWindow &self) -> Threshold & {
                return self.threshold;
            },
            [](DynamicWindow &self, const py::object &threshold_object) {
                if (py::isinstance<Threshold>(threshold_object)) {
                    self.threshold = threshold_object.cast<Threshold>();
                } else if (py::isinstance<py::str>(threshold_object)) {
                    self.set_threshold(threshold_object.cast<std::string>());
                } else {
                    self.set_threshold(
                        threshold_object.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Threshold object storing the symbolic expression and resolved numeric value.
            )pbdoc"
        )
        .def(
            "_add_to_ax",
            [ureg](DynamicWindow &self, py::object ax, py::object signal_units) {
                if (std::isnan(self.resolved_threshold)) {
                    throw std::runtime_error(
                        "Threshold has not been resolved. Run the trigger first."
                    );
                }

                py::object quantity = py::cast(self.resolved_threshold) * ureg.attr("volt");

                py::object converted_quantity = quantity.attr("to")(signal_units);

                ax.attr("axhline")(
                    converted_quantity.attr("magnitude"),
                    py::arg("color") = "red",
                    py::arg("linestyle") = "--",
                    py::arg("linewidth") = 1,
                    py::arg("label") = py::str("Threshold: {:.2f}").format(quantity.attr("to_compact")())
                );

                ax.attr("legend")();
            },
            py::arg("ax"),
            py::arg("signal_units"),
            R"pbdoc(
                Add the resolved threshold to a matplotlib Axes.
            )pbdoc"
        );

    py::class_<DoubleThreshold, BaseDiscriminator>(module, "DoubleThreshold")
        .def(
            py::init(
                [](
                    const std::string &trigger_channel,
                    const py::object &threshold,
                    const py::object &lower_threshold,
                    const bool debounce_enabled,
                    const int min_window_duration,
                    size_t pre_buffer,
                    size_t post_buffer,
                    int max_triggers
                ) {
                    DoubleThreshold instance(
                        trigger_channel,
                        pre_buffer,
                        post_buffer,
                        max_triggers
                    );

                    if (py::isinstance<py::str>(threshold)) {
                        instance.set_threshold(threshold.cast<std::string>());
                    } else {
                        instance.set_threshold(
                            threshold.attr("to")("volt").attr("magnitude").cast<double>()
                        );
                    }

                    if (
                        lower_threshold.is_none() ||
                        (
                            py::isinstance<py::float_>(lower_threshold) &&
                            std::isnan(lower_threshold.cast<double>())
                        )
                    ) {
                        instance.clear_lower_threshold();
                    } else if (py::isinstance<py::str>(lower_threshold)) {
                        instance.set_lower_threshold(lower_threshold.cast<std::string>());
                    } else {
                        instance.set_lower_threshold(
                            lower_threshold.attr("to")("volt").attr("magnitude").cast<double>()
                        );
                    }

                    instance.set_debounce_enabled(debounce_enabled);
                    instance.set_min_window_duration(min_window_duration);

                    return instance;
                }
            ),
            py::arg("trigger_channel"),
            py::arg("threshold"),
            py::arg("lower_threshold") = py::none(),
            py::arg("debounce_enabled") = true,
            py::arg("min_window_duration") = -1,
            py::arg("pre_buffer") = 0,
            py::arg("post_buffer") = 0,
            py::arg("max_triggers") = -1,
            R"pbdoc(
                Initialize a DoubleThreshold trigger detector.
            )pbdoc"
        )
        .def(
            "run",
            &DoubleThreshold::run,
            R"pbdoc(
                Execute double threshold trigger detection.
            )pbdoc"
        )
        .def_property(
            "threshold",
            [](DoubleThreshold &self) -> Threshold & {
                return self.threshold;
            },
            [](DoubleThreshold &self, const py::object &threshold_object) {
                if (py::isinstance<Threshold>(threshold_object)) {
                    self.threshold = threshold_object.cast<Threshold>();
                } else if (py::isinstance<py::str>(threshold_object)) {
                    self.set_threshold(threshold_object.cast<std::string>());
                } else {
                    self.set_threshold(
                        threshold_object.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Threshold object storing the symbolic expression and resolved numeric value.
            )pbdoc"
        )
        .def_property(
            "lower_threshold",
            [](DoubleThreshold &self) -> Threshold & {
                return self.lower_threshold;
            },
            [](DoubleThreshold &self, const py::object &threshold_object) {
                if (py::isinstance<Threshold>(threshold_object)) {
                    self.lower_threshold = threshold_object.cast<Threshold>();
                } else if (py::isinstance<py::str>(threshold_object)) {
                    self.set_lower_threshold(threshold_object.cast<std::string>());
                } else {
                    self.set_lower_threshold(
                        threshold_object.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Threshold object storing the symbolic expression and resolved numeric value.
            )pbdoc"
        )
        .def(
            "set_debounce_enabled",
            &DoubleThreshold::set_debounce_enabled,
            py::arg("debounce_enabled"),
            R"pbdoc(
                Update debounce behavior after construction.
            )pbdoc"
        )
        .def(
            "set_min_window_duration",
            &DoubleThreshold::set_min_window_duration,
            py::arg("min_window_duration"),
            R"pbdoc(
                Update minimum window duration after construction.
            )pbdoc"
        )
        .def(
            "_add_to_ax",
            [](DoubleThreshold &self, py::object ax, py::object signal_units) {
                if (std::isnan(self.resolved_upper_threshold)) {
                    throw std::runtime_error(
                        "Thresholds have not been resolved. Run the trigger first."
                    );
                }

                py::module_ pint = py::module_::import("pint");

                py::object upper_quantity =
                    pint.attr("Quantity")(self.resolved_upper_threshold, "volt");
                py::object upper_converted_quantity =
                    upper_quantity.attr("to")(signal_units);

                ax.attr("axhline")(
                    upper_converted_quantity.attr("magnitude"),
                    py::arg("color") = "blue",
                    py::arg("linestyle") = "--",
                    py::arg("linewidth") = 1,
                    py::arg("label") = py::str("Upper Threshold: {:.2f}").format(upper_quantity.attr("to_compact")())
                );

                if (!std::isnan(self.resolved_lower_threshold)) {
                    py::object lower_quantity =
                        pint.attr("Quantity")(self.resolved_lower_threshold, "volt");
                    py::object lower_converted_quantity =
                        lower_quantity.attr("to")(signal_units);

                    ax.attr("axhline")(
                        lower_converted_quantity.attr("magnitude"),
                        py::arg("color") = "red",
                        py::arg("linestyle") = "--",
                        py::arg("linewidth") = 1,
                        py::arg("label") = py::str("Lower Threshold: {:.2f}").format(lower_quantity.attr("to_compact")())
                    );
                }

                ax.attr("legend")();
            },
            py::arg("ax"),
            py::arg("signal_units"),
            R"pbdoc(
                Add the resolved thresholds to a matplotlib Axes.
            )pbdoc"
        );
}
