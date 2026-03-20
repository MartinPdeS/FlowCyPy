#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "triggering_system.h"
#include <signal_processing/trigger/interface.cpp>

namespace py = pybind11;

namespace {

/**
 * @brief Return true if the Python object is a NaN float.
 *
 * This is used for optional lower thresholds in the DoubleThreshold wrapper.
 */
bool is_nan_python_float(const py::object &object) {
    return py::isinstance<py::float_>(object) && std::isnan(object.cast<double>());
}

/**
 * @brief Assign a Python threshold object to a trigger instance.
 *
 * Supported Python inputs are:
 * - str, interpreted as symbolic threshold such as "3sigma"
 * - Pint quantity convertible to volt
 */
template <typename TriggerType>
void assign_threshold_from_python(TriggerType &self, const py::object &threshold) {
    if (py::isinstance<py::str>(threshold)) {
        self.set_threshold(threshold.cast<std::string>());
        return;
    }

    self.set_threshold(
        threshold.attr("to")("volt").attr("magnitude").cast<double>()
    );
}

/**
 * @brief Assign a Python lower threshold object to a DoubleThreshold instance.
 *
 * Supported Python inputs are:
 * - None, clears the lower threshold
 * - NaN float, also clears the lower threshold
 * - str, interpreted as symbolic threshold such as "2sigma"
 * - Pint quantity convertible to volt
 */
void assign_lower_threshold_from_python(
    DoubleThreshold &self,
    const py::object &lower_threshold
) {
    if (lower_threshold.is_none() || is_nan_python_float(lower_threshold)) {
        self.clear_lower_threshold();
        return;
    }

    if (py::isinstance<py::str>(lower_threshold)) {
        self.set_lower_threshold(lower_threshold.cast<std::string>());
        return;
    }

    self.set_lower_threshold(
        lower_threshold.attr("to")("volt").attr("magnitude").cast<double>()
    );
}

} // namespace

PYBIND11_MODULE(triggering_system, module) {
    module.doc() = R"pbdoc(
        Signal Triggering and Segmentation System.

        Provides an efficient framework for threshold-based and dynamic
        window triggering of signals, with support for debouncing,
        pre/post buffering, and segment extraction.
    )pbdoc";

    register_trigger(module);

    py::class_<BaseTrigger>(module, "BaseTrigger")
        .def_readonly(
            "trigger",
            &BaseTrigger::trigger,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                The underlying trigger system used for detection and segmentation.

                This object manages the signal data, time stamps, and segment extraction.
            )pbdoc"
        )
        .def_readwrite(
            "trigger_channel",
            &BaseTrigger::trigger_channel,
            R"pbdoc(
                Name of the trigger detection channel used.

                This is set during initialization and determines which signal
                is used for trigger detection.
            )pbdoc"
        )
        .def_readwrite(
            "pre_buffer",
            &BaseTrigger::pre_buffer,
            R"pbdoc(
                Number of samples to include before each detected trigger.
            )pbdoc"
        )
        .def_readwrite(
            "post_buffer",
            &BaseTrigger::post_buffer,
            R"pbdoc(
                Number of samples to include after each detected trigger.
            )pbdoc"
        )
        .def_readwrite(
            "max_triggers",
            &BaseTrigger::max_triggers,
            R"pbdoc(
                Maximum number of triggers to record.

                If set to -1, there is no limit on the number of triggers.
            )pbdoc"
        )
        .def(
            "add_time",
            [](BaseTrigger &self, const py::object &time_array) {
                const std::vector<double> time_vector = time_array.attr("to")("second").attr("magnitude").cast<std::vector<double>>();

                self.add_time(time_vector);
            },
            py::arg("time_array"),
            R"pbdoc(
                Add a global time axis for the signals.

                Parameters
                ----------
                time_array : array-like quantity
                    One dimensional array of time values convertible to seconds.
            )pbdoc"
        )
        .def(
            "add_channel",
            [](BaseTrigger &self, const std::string &channel, const py::object &signal_array) {
                const std::vector<double> signal_vector = signal_array
                    .attr("to")("volt")
                    .attr("magnitude")
                    .cast<std::vector<double>>();

                self.add_signal(channel, signal_vector);
            },
            py::arg("channel") = "default",
            py::arg("signal_array"),
            R"pbdoc(
                Add a signal trace to be analyzed for triggers.

                Parameters
                ----------
                channel : str
                    Name of the signal channel.
                signal_array : array-like quantity
                    One dimensional array of signal values convertible to volts.
            )pbdoc"
        )
        .def(
            "run_with_dataframe",
            [](BaseTrigger &self, const py::object &dataframe) {
                const std::vector<double> time_vector = dataframe["Time"]
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
                    const std::vector<double> signal_vector = dataframe[channel]
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
                Run trigger detection using a DataFrame. The DataFrame must contain a "Time" column and one or more signal columns.

                Parameters
                ----------
                dataframe : pandas.DataFrame
                    DataFrame containing time and signal columns.

                Returns
                -------
                TriggerDataFrame
                    A DataFrame containing the trigger windows with segment IDs, times, and signals.
            )pbdoc"

        )
        .def(
            "_assemble_dataframe",
            [](BaseTrigger &self, const py::object &dataframe) {
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
                    py::object detector_name = py::reinterpret_borrow<py::object>(detector_name_handle);

                    data[detector_name] = pint_pandas.attr("PintArray")(
                        py::cast(
                            self.trigger.get_segmented_signal(
                                detector_name.cast<std::string>()
                            )
                        ),
                        signal_units
                    );
                }

                py::object tidy = pandas.attr("DataFrame")(data).attr("set_index")("SegmentID");

                py::object trigger_dataframe_class = dataframe.attr("__class__");
                tidy = trigger_dataframe_class(tidy);

                tidy.attr("normalize_units")(
                    py::arg("signal_units") = "max",
                    py::arg("time_units") = "max"
                );

                return tidy;
            },
            py::arg("dataframe"),
            R"pbdoc(
                Assemble a tidy trigger dataframe from the segmented C++ backend results.

                This method collects the segmented time axis, segment identifiers, and
                segmented signal values for all detectors present in the input dataframe,
                then builds a pandas based output dataframe with Pint units preserved.

                Parameters
                ----------
                dataframe : TriggerDataFrame
                    Input dataframe used to recover detector names and signal units.

                Returns
                -------
                TriggerDataFrame
                    A tidy dataframe indexed by segment identifier and containing the
                    segmented time axis and detector signals.
            )pbdoc"
        )
        ;

    py::class_<FixedWindow, BaseTrigger>(module, "FixedWindow")
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

                    assign_threshold_from_python(instance, threshold);

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

                Parameters
                ----------
                trigger_channel : str
                    Name of the detection channel to apply.
                threshold : float or str
                    Trigger threshold in volts or a symbolic threshold such as "3sigma".
                pre_buffer : int, optional
                    Samples to buffer before each detected event. Default = 0.
                post_buffer : int, optional
                    Samples to buffer after each detected event. Default = 0.
                max_triggers : int, optional
                    Maximum number of triggers to record. Use -1 for no limit.
            )pbdoc"
        )
        .def(
            "run",
            &FixedWindow::run,
            R"pbdoc(
                Execute fixed window trigger detection using the stored threshold.
            )pbdoc"
        )
        .def(
            "set_threshold",
            [](FixedWindow &self, const py::object &threshold) {
                assign_threshold_from_python(self, threshold);
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
                py::object quantity = pint.attr("Quantity")(self.resolved_threshold, "volt");
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
                Add a horizontal line to the provided Axes representing the resolved threshold.
            )pbdoc"
        )
        ;

    py::class_<DynamicWindow, BaseTrigger>(module, "DynamicWindow")
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

                    assign_threshold_from_python(instance, threshold);

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

                Parameters
                ----------
                trigger_channel : str
                    Name of the detection channel to apply.
                threshold : float or str
                    Trigger threshold in volts or a symbolic threshold such as "3sigma".
                pre_buffer : int, optional
                    Samples to buffer before each detected event. Default = 0.
                post_buffer : int, optional
                    Samples to buffer after each detected event. Default = 0.
                max_triggers : int, optional
                    Maximum number of triggers to record. Use -1 for no limit.
            )pbdoc"
        )
        .def(
            "rum",
            &DynamicWindow::run,
            R"pbdoc(
                Execute dynamic window trigger detection using the stored threshold.
            )pbdoc"
        )
        .def(
            "set_threshold",
            [](DynamicWindow &self, const py::object &threshold) {
                assign_threshold_from_python(self, threshold);
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
                py::object quantity = pint.attr("Quantity")(self.resolved_threshold, "volt");
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
                Add a horizontal line to the provided Axes representing the resolved threshold.
            )pbdoc"
        )
        ;

    py::class_<DoubleThreshold, BaseTrigger>(module, "DoubleThreshold")
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

                    assign_threshold_from_python(instance, threshold);
                    assign_lower_threshold_from_python(instance, lower_threshold);

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

                Parameters
                ----------
                trigger_channel : str
                    Name of the detection channel to apply.
                threshold : float or str
                    Primary threshold in volts or a symbolic threshold such as "3sigma".
                lower_threshold : float, str, or None, optional
                    Secondary threshold in volts, symbolic form, or None.
                debounce_enabled : bool, optional
                    If true, applies debouncing to avoid rapid successive triggers.
                min_window_duration : int, optional
                    Minimum samples above threshold required for a valid trigger.
                    Use -1 to disable this constraint.
                pre_buffer : int, optional
                    Samples to buffer before each detected event. Default = 0.
                post_buffer : int, optional
                    Samples to buffer after each detected event. Default = 0.
                max_triggers : int, optional
                    Maximum number of triggers to record. Use -1 for no limit.
            )pbdoc"
        )
        .def(
            "rum",
            &DoubleThreshold::run,
            R"pbdoc(
                Execute double threshold trigger detection using the stored parameters.
            )pbdoc"
        )
        .def(
            "set_threshold",
            [](DoubleThreshold &self, const py::object &threshold) {
                assign_threshold_from_python(self, threshold);
            },
            py::arg("threshold"),
            R"pbdoc(
                Update the primary threshold after construction.
            )pbdoc"
        )
        .def(
            "set_lower_threshold",
            [](DoubleThreshold &self, const py::object &lower_threshold) {
                assign_lower_threshold_from_python(self, lower_threshold);
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

                py::object upper_quantity = pint.attr("Quantity")(self.resolved_upper_threshold, "volt");
                py::object upper_converted_quantity = upper_quantity.attr("to")(signal_units);

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
                    py::object lower_quantity = pint.attr("Quantity")(self.resolved_lower_threshold, "volt");
                    py::object lower_converted_quantity = lower_quantity.attr("to")(signal_units);

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
                Add horizontal lines to the provided Axes representing the resolved thresholds.
            )pbdoc"
        )
        ;
}
