#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "peak_locator.h"

namespace py = pybind11;


PYBIND11_MODULE(peak_locator, module) {
    module.doc() = R"pbdoc(
        Fast C++ peak detection utilities for segmented 1D signals.

        This module exposes two peak locator strategies.

        1. SlidingWindowPeakLocator
           The signal is divided into windows and one local maximum is extracted
           from each window. The detected peaks are then sorted by descending
           height.

        2. GlobalPeakLocator
           The strongest sample in the full signal is selected as the peak.

        Width and area semantics are controlled by support objects.

        Available support objects
        -------------------------
        FullWindowSupport()
            Width and area are computed on the full analyzed interval.

        PulseSupport(channel="default", threshold=0.5)
            Width and area are computed on a positive pulse support defined by

                threshold * peak_height

            The `channel` argument controls how the support channel is selected.

            - "default"
                In segmented mode, use the supplied trigger channel.
                In single-array mode, fall back to the current signal.

            - "independent"
                Each channel computes its own support independently.

            - "<detector_name>"
                Reuse the named detector channel as shared support for all
                channels in the same segment.

        Segmented dictionary interface
        ------------------------------
        Locators can process a flat segmented Python dictionary of the form

            {
                "segment_id": [...],
                "Time": <ignored>,
                "forward": array([...]),
                "side": array([...]),
                ...
            }

        The "Time" entry is ignored. Every other entry is interpreted as a
        signal channel and processed independently or with shared support,
        depending on the configured support object.
    )pbdoc";

    py::class_<BaseSupport, std::shared_ptr<BaseSupport>>(
        module,
        "BaseSupport",
        R"pbdoc(
            Abstract base class describing how event support is defined.

            Support objects control the semantics of width and area
            computations. They are passed to peak locator constructors.
        )pbdoc"
    );

    py::class_<FullWindowSupport, BaseSupport, std::shared_ptr<FullWindowSupport>>(
        module,
        "FullWindowSupport",
        R"pbdoc(
            Support object that uses the full analyzed interval.

            In this mode, width is the full segment or window length and area is
            accumulated on the full interval.

            No threshold expansion is used.
        )pbdoc"
    )
        .def(
            py::init<>(),
            R"pbdoc(
                Construct a full-window support object.

                This support mode uses the full interval for width and area
                computations.
            )pbdoc"
        );

    py::class_<PulseSupport, BaseSupport, std::shared_ptr<PulseSupport>>(
        module,
        "PulseSupport",
        R"pbdoc(
            Support object based on a positive pulse support around a peak.

            The support is defined on a support signal by first locating a
            positive peak, then expanding left and right while neighboring
            samples remain above

                threshold * peak_height

            Parameters
            ----------
            channel : str, default="default"
                Support channel selection rule.

                Accepted values are:

                - "default"
                  In segmented mode, use the trigger channel supplied to
                  `run(..., trigger_channel=...)`.

                  In single-array mode, fall back to the current signal.

                - "independent"
                  Each channel computes its own support independently.

                - "<detector_name>"
                  Use the named detector or channel as shared support for all
                  channels in the same segment.

            threshold : float, default=0.5
                Relative threshold in the interval [0, 1].
            )pbdoc"
    )
        .def(
            py::init<const std::string&, double>(),
            py::arg("channel") = "default",
            py::arg("threshold") = 0.5,
            R"pbdoc(
                Construct a pulse-support object.

                Parameters
                ----------
                channel : str, default="default"
                    Support channel selection rule.
                threshold : float, default=0.5
                    Relative threshold used to define the pulse support.
            )pbdoc"
        )
        .def_readonly(
            "channel",
            &PulseSupport::channel,
            R"pbdoc(
                Support channel selector.

                This is one of:
                - "default"
                - "independent"
                - a detector or channel name
            )pbdoc"
        )
        .def_readonly(
            "threshold",
            &PulseSupport::threshold,
            R"pbdoc(
                Relative threshold used during support expansion.
            )pbdoc"
        );

    py::class_<BasePeakLocator, std::shared_ptr<BasePeakLocator>>(
        module,
        "BasePeakLocator",
        R"pbdoc(
            Abstract base class for 1D peak detection.

            Concrete subclasses define how the peak index is selected, while the
            provided support object defines how width and area are computed.
        )pbdoc"
    )
        .def_readonly(
            "max_number_of_peaks",
            &BasePeakLocator::max_number_of_peaks,
            R"pbdoc(
                Maximum number of peaks stored in the fixed-size output buffers.
            )pbdoc"
        )
        .def(
            "get_metrics",
            &BasePeakLocator::get_metrics,
            py::arg("array"),
            R"pbdoc(
                Compute peak metrics for a single 1D signal.

                Parameters
                ----------
                array : array-like of float
                    Input signal values.

                Returns
                -------
                dict
                    Dictionary containing:
                    - "Index": peak indices
                    - "Height": peak heights

                    and, when enabled:
                    - "Width": peak widths
                    - "Area": peak areas
            )pbdoc"
        )
        .def(
            "compute",
            &BasePeakLocator::compute,
            py::arg("array"),
            R"pbdoc(
                Run peak detection on a single 1D signal and update internal
                output buffers.

                Parameters
                ----------
                array : array-like of float
                    Input signal values.
            )pbdoc"
        )
        .def(
            "run",
            [](const BasePeakLocator& self,
               const py::dict& segmented_signal_dictionary,
               const std::string& trigger_channel) -> py::dict {
                if (!segmented_signal_dictionary.contains("segment_id")) {
                    throw std::runtime_error(
                        "Input dictionary must contain a 'segment_id' key."
                    );
                }

                if (!segmented_signal_dictionary.contains("Time")) {
                    throw std::runtime_error(
                        "Input dictionary must contain a 'Time' key."
                    );
                }

                const std::vector<int> segment_ids =
                    py::cast<std::vector<int>>(segmented_signal_dictionary[py::str("segment_id")]);

                FlatSignalDictionary flat_signal_dictionary;

                for (const auto& item : segmented_signal_dictionary) {
                    const std::string key = py::cast<std::string>(item.first);

                    if (key == "segment_id" || key == "Time") {
                        continue;
                    }

                    flat_signal_dictionary[key] =
                        py::cast<std::vector<double>>(item.second);
                }

                if (flat_signal_dictionary.empty()) {
                    throw std::runtime_error(
                        "Input dictionary must contain at least one signal channel in addition to 'segment_id' and 'Time'."
                    );
                }

                const SegmentedMetricDictionary segmented_metrics =
                    self.run_flat_segmented_signals(
                        segment_ids,
                        flat_signal_dictionary,
                        trigger_channel
                    );

                py::dict output_dictionary;

                for (const auto& [segment_id, segment_metric_dictionary] : segmented_metrics) {
                    py::dict segment_output_dictionary;

                    for (const auto& [channel_name, metric_dictionary] : segment_metric_dictionary) {
                        py::dict channel_output_dictionary;

                        for (const auto& [metric_name, metric_values] : metric_dictionary) {
                            channel_output_dictionary[py::str(metric_name)] = py::cast(metric_values);
                        }

                        segment_output_dictionary[py::str(channel_name)] = channel_output_dictionary;
                    }

                    output_dictionary[py::int_(segment_id)] = segment_output_dictionary;
                }

                return output_dictionary;
            },
            py::arg("segmented_signal_dictionary"),
            py::arg("trigger_channel") = "",
            R"pbdoc(
                Compute peak metrics for all channels in a flat segmented dictionary.

                Parameters
                ----------
                segmented_signal_dictionary : dict
                    Flat dictionary structured as

                        {
                            "segment_id": integer_array,
                            "Time": quantity_or_array,
                            "channel_name": array_like,
                            ...
                        }

                    The "segment_id" entry identifies the segment of each sample.
                    The "Time" entry is ignored.
                    Every other key is treated as a 1D signal channel.

                trigger_channel : str, default=""
                    Trigger channel name used when the configured support object
                    is `PulseSupport(channel="default", ...)`.

                Returns
                -------
                dict
                    Nested dictionary structured as

                        {
                            segment_id: {
                                "channel_name": {
                                    "Index": [...],
                                    "Height": [...],
                                    "Width": [...],   # if enabled
                                    "Area": [...],    # if enabled
                                },
                                ...
                            },
                            ...
                        }

                Notes
                -----
                The regrouping and segmented processing are handled in C++.
            )pbdoc"
        );

    py::class_<SlidingWindowPeakLocator, BasePeakLocator, std::shared_ptr<SlidingWindowPeakLocator>>(
        module,
        "SlidingWindowPeakLocator",
        R"pbdoc(
            Sliding window peak detector for 1D signals.

            One local maximum is extracted per window. The resulting peaks are
            sorted by descending height, and the strongest peaks are returned in
            fixed-size output arrays.

            Width and area semantics are controlled by the supplied support
            object.
        )pbdoc"
    )
        .def(
            py::init<int, int, int, int, bool, bool, bool, std::shared_ptr<BaseSupport>, bool>(),
            py::arg("window_size"),
            py::arg("window_step") = -1,
            py::arg("max_number_of_peaks") = 5,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("allow_negative_area") = true,
            py::arg("support") = std::make_shared<FullWindowSupport>(),
            py::arg("debug_mode") = false,
            R"pbdoc(
                Construct a sliding window peak locator.

                Parameters
                ----------
                window_size : int
                    Number of samples in each window.

                window_step : int, default=-1
                    Step between consecutive windows. If set to -1, the step is
                    set equal to `window_size`.

                max_number_of_peaks : int, default=5
                    Maximum number of peaks to report.

                padding_value : int, default=-1
                    Value used to pad unused output entries.

                compute_width : bool, default=False
                    Whether to compute peak widths.

                compute_area : bool, default=False
                    Whether to compute peak areas.

                allow_negative_area : bool, default=True
                    Whether negative samples are allowed during area accumulation.

                support : BaseSupport, default=FullWindowSupport()
                    Support object controlling how width and area are defined.

                debug_mode : bool, default=False
                    Whether to print debug information during peak detection.
            )pbdoc"
        );

    py::class_<GlobalPeakLocator, BasePeakLocator, std::shared_ptr<GlobalPeakLocator>>(
        module,
        "GlobalPeakLocator",
        R"pbdoc(
            Global peak detector for 1D signals.

            This locator identifies a single event over the full signal, then
            measures its amplitude according to configurable polarity, height,
            and baseline conventions.

            Width and area semantics are controlled by the supplied support
            object.
        )pbdoc"
    )
        .def(
            py::init<int, int, bool, bool, bool, std::shared_ptr<BaseSupport>, const std::string&, const std::string&, const std::string&, bool>(),
            py::arg("max_number_of_peaks") = 1,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("allow_negative_area") = true,
            py::arg("support") = std::make_shared<FullWindowSupport>(),
            py::arg("polarity") = "positive",
            py::arg("height_mode") = "raw",
            py::arg("baseline_mode") = "zero",
            py::arg("debug_mode") = false,
            R"pbdoc(
                Construct a global peak locator.

                Parameters
                ----------
                max_number_of_peaks : int, default=1
                    Maximum number of peaks to report. Only one physical peak is
                    detected, so remaining entries are padded.

                padding_value : int, default=-1
                    Value used to pad unused output entries.

                compute_width : bool, default=False
                    Whether to compute width.

                compute_area : bool, default=False
                    Whether to compute area.

                allow_negative_area : bool, default=True
                    Whether negative samples are allowed during area accumulation.

                support : BaseSupport, default=FullWindowSupport()
                    Support object controlling how width and area are defined.

                polarity : {"positive", "negative", "absolute"}, default="positive"
                    Rule used to choose the sample representing the event.

                height_mode : {"raw", "peak_to_baseline", "peak_to_peak"}, default="raw"
                    Rule used to convert the selected event into a reported
                    height.

                baseline_mode : {"zero", "segment_mean", "edge_mean"}, default="zero"
                    Baseline convention used by height modes that depend on a
                    reference level.

                debug_mode : bool, default=False
                    Whether to print debug information during peak detection.
            )pbdoc"
        )
        .def_readonly(
            "polarity",
            &GlobalPeakLocator::polarity,
            R"pbdoc(
                Measurement polarity used to select the event sample.
            )pbdoc"
        )
        .def_readonly(
            "height_mode",
            &GlobalPeakLocator::height_mode,
            R"pbdoc(
                Height measurement mode used for the reported event amplitude.
            )pbdoc"
        )
        .def_readonly(
            "baseline_mode",
            &GlobalPeakLocator::baseline_mode,
            R"pbdoc(
                Baseline convention used by baseline-aware measurement modes.
            )pbdoc"
        );
}
