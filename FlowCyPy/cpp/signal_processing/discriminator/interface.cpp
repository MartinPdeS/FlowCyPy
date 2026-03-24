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
            "add_time",
            [](BaseDiscriminator &self, const py::object &time_array) {
                const std::vector<double> time_vector =
                    time_array
                        .attr("to")("second")
                        .attr("magnitude")
                        .cast<std::vector<double>>();

                self.add_time(time_vector);
            },
            py::arg("time_array"),
            R"pbdoc(
                Add the global time axis.

                Parameters
                ----------
                time_array : array-like quantity
                    One dimensional array convertible to seconds.
            )pbdoc"
        )
        .def(
            "add_channel",
            [](BaseDiscriminator &self,
               const std::string &channel,
               const py::object &signal_array) {
                const std::vector<double> signal_vector =
                    signal_array
                        .attr("to")("volt")
                        .attr("magnitude")
                        .cast<std::vector<double>>();

                self.add_signal(channel, signal_vector);
            },
            py::arg("channel"),
            py::arg("signal_array"),
            R"pbdoc(
                Add a signal channel.

                Parameters
                ----------
                channel : str
                    Name of the signal channel.
                signal_array : array-like quantity
                    One dimensional array convertible to volts.
            )pbdoc"
        )
        .def(
            "run_with_dataframe",
            [](BaseDiscriminator &self, const py::object &dataframe) {
                const std::vector<double> time_vector =
                    dataframe["Time"]
                        .attr("pint")
                        .attr("quantity")
                        .attr("to")("second")
                        .attr("magnitude")
                        .cast<std::vector<double>>();

                self.add_time(time_vector);

                const py::object &channel_list = dataframe.attr("columns");
                for (const auto &channel : channel_list) {
                    if (channel.cast<std::string>() == "Time") {
                        continue;
                    }

                    const std::vector<double> signal_vector =
                        dataframe[channel]
                            .attr("pint")
                            .attr("quantity")
                            .attr("to")("volt")
                            .attr("magnitude")
                            .cast<std::vector<double>>();

                    self.add_signal(channel.cast<std::string>(), signal_vector);
                }

                self.run();

                return py::cast(self).attr("_assemble_dataframe")(dataframe);
            },
            py::arg("dataframe"),
            R"pbdoc(
                Run trigger detection from a dataframe.

                The dataframe must contain a "Time" column and one or more signal columns.

                Parameters
                ----------
                dataframe : pandas.DataFrame
                    Dataframe containing time and signal columns.

                Returns
                -------
                TriggerDataFrame
                    Segmented trigger output assembled as a tidy dataframe.
            )pbdoc"
        )
        .def(
            "run_with_dict",
            [ureg](BaseDiscriminator &self, const py::dict &data_dict) {
                if (!data_dict.contains("Time")) {
                    throw std::runtime_error("Input dictionary must contain a 'Time' key.");
                }

                const std::vector<double> time_vector =
                    py::reinterpret_borrow<py::object>(data_dict["Time"]).attr("to")("second").attr("magnitude").cast<std::vector<double>>();

                self.add_time(time_vector);

                bool found_signal_channel = false;

                for (const auto &item : data_dict) {
                    const std::string key =
                        py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

                    if (key == "Time") {
                        continue;
                    }

                    const std::vector<double> signal_vector = py::reinterpret_borrow<py::object>(item.second).attr("to")("volt").attr("magnitude").cast<std::vector<double>>();

                    self.add_signal(key, signal_vector);
                    found_signal_channel = true;
                }

                if (!found_signal_channel) {
                    throw std::runtime_error("Input dictionary must contain at least one signal channel in addition to 'Time'.");
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

                py::dict grouped_output;

                for (size_t sample_index = 0; sample_index < segment_ids.size(); ++sample_index) {
                    const int segment_id = segment_ids[sample_index];
                    py::int_ py_segment_id(segment_id);

                    if (!grouped_output.contains(py_segment_id)) {
                        py::dict segment_dict;
                        segment_dict["Time"] = py::list();

                        for (const auto &item : data_dict) {
                            const std::string key =
                                py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

                            if (key == "Time") {
                                continue;
                            }

                            segment_dict[py::str(key)] = py::list();
                        }

                        grouped_output[py_segment_id] = segment_dict;
                    }

                    py::dict segment_dict =
                        py::reinterpret_borrow<py::dict>(grouped_output[py_segment_id]);

                    py::list time_list =
                        py::reinterpret_borrow<py::list>(segment_dict["Time"]);
                    time_list.append(segmented_time[sample_index]);

                    for (const auto &item : data_dict) {
                        const std::string key =
                            py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

                        if (key == "Time") {
                            continue;
                        }

                        const std::vector<double> &segmented_signal =
                            self.trigger.get_segmented_signal(key);

                        if (segmented_signal.size() != segment_ids.size()) {
                            throw std::runtime_error(
                                "Segmented signal size mismatch for channel '" + key + "'."
                            );
                        }

                        py::list channel_list =
                            py::reinterpret_borrow<py::list>(segment_dict[py::str(key)]);
                        channel_list.append(segmented_signal[sample_index]);
                    }
                }

                py::dict final_output;

                for (const auto &item : grouped_output) {
                    py::int_ segment_id = py::reinterpret_borrow<py::int_>(item.first);
                    py::dict raw_segment_dict = py::reinterpret_borrow<py::dict>(item.second);

                    py::dict final_segment_dict;

                    final_segment_dict["Time"] = numpy.attr("array")(raw_segment_dict["Time"]) * ureg.attr("second");

                    for (const auto &channel_item : raw_segment_dict) {
                        const std::string key = py::reinterpret_borrow<py::object>(channel_item.first).cast<std::string>();

                        if (key == "Time") {
                            continue;
                        }

                        final_segment_dict[py::str(key)] = (numpy.attr("array")(channel_item.second) * ureg.attr("volt")).attr("to_compact")();
                    }

                    final_output[segment_id] = final_segment_dict;
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
                    Nested dictionary indexed by segment identifier. Each segment
                    contains a "Time" entry and one entry per signal channel.
            )pbdoc"
        )
        .def(
            "_assemble_dataframe",
            [](BaseDiscriminator &self, const py::object &dataframe) {
                py::module_ pandas = py::module_::import("pandas");
                py::module_ pint_pandas = py::module_::import("pint_pandas");

                py::list detector_names = dataframe.attr("detector_names");
                py::object signal_units = dataframe.attr("signal_units");

                py::dict data;
                data["SegmentID"] = py::cast(self.trigger.segment_ids_out);
                data["Time"] = pint_pandas.attr("PintArray")(
                    py::cast(self.trigger.time_out),
                    "second"
                );

                for (const py::handle &detector_name_handle : detector_names) {
                    py::object detector_name =
                        py::reinterpret_borrow<py::object>(detector_name_handle);

                    data[detector_name] = pint_pandas.attr("PintArray")(
                        py::cast(
                            self.trigger.get_segmented_signal(
                                detector_name.cast<std::string>()
                            )
                        ),
                        signal_units
                    );
                }

                py::object tidy =
                    pandas.attr("DataFrame")(data).attr("set_index")("SegmentID");

                py::object trigger_dataframe_class =
                    py::module_::import("FlowCyPy.sub_frames.acquisition")
                        .attr("TriggerDataFrame");

                tidy = trigger_dataframe_class(tidy);

                tidy.attr("normalize_units")(
                    py::arg("signal_units") = "max",
                    py::arg("time_units") = "max"
                );

                return tidy;
            },
            py::arg("dataframe"),
            R"pbdoc(
                Assemble a tidy trigger dataframe from segmented C++ backend results.
            )pbdoc"
        );

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
        .def(
            "set_threshold",
            [](FixedWindow &self, const py::object &threshold) {
                if (py::isinstance<py::str>(threshold)) {
                    self.set_threshold(threshold.cast<std::string>());
                } else {
                    self.set_threshold(
                        threshold.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::arg("threshold"),
            R"pbdoc(
                Update the trigger threshold after construction.
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
        .def(
            "set_threshold",
            [](DynamicWindow &self, const py::object &threshold) {
                if (py::isinstance<py::str>(threshold)) {
                    self.set_threshold(threshold.cast<std::string>());
                } else {
                    self.set_threshold(
                        threshold.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::arg("threshold"),
            R"pbdoc(
                Update the trigger threshold after construction.
            )pbdoc"
        )
        .def(
            "_add_to_ax",
            [](DynamicWindow &self, py::object ax, py::object signal_units) {
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
        .def(
            "set_threshold",
            [](DoubleThreshold &self, const py::object &threshold) {
                if (py::isinstance<py::str>(threshold)) {
                    self.set_threshold(threshold.cast<std::string>());
                } else {
                    self.set_threshold(
                        threshold.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::arg("threshold"),
            R"pbdoc(
                Update the primary threshold after construction.
            )pbdoc"
        )
        .def(
            "set_lower_threshold",
            [](DoubleThreshold &self, const py::object &lower_threshold) {
                if (
                    lower_threshold.is_none() ||
                    (
                        py::isinstance<py::float_>(lower_threshold) &&
                        std::isnan(lower_threshold.cast<double>())
                    )
                ) {
                    self.clear_lower_threshold();
                } else if (py::isinstance<py::str>(lower_threshold)) {
                    self.set_lower_threshold(lower_threshold.cast<std::string>());
                } else {
                    self.set_lower_threshold(
                        lower_threshold.attr("to")("volt").attr("magnitude").cast<double>()
                    );
                }
            },
            py::arg("lower_threshold"),
            R"pbdoc(
                Update the lower threshold after construction.

                Passing None clears the lower threshold.
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
                    py::arg("label") = py::str("Upper Threshold: {:.2f}").format(
                        upper_quantity.attr("to_compact")()
                    )
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
                        py::arg("label") = py::str("Lower Threshold: {:.2f}").format(
                            lower_quantity.attr("to_compact")()
                        )
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
