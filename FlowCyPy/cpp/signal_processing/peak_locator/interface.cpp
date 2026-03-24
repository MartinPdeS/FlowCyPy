#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "peak_locator.h"

namespace py = pybind11;


PYBIND11_MODULE(peak_locator, module) {
    module.doc() = R"pbdoc(
        Fast C++ peak detection utilities for segmented 1D signals.

        This module exposes two peak locator strategies:

        1. SlidingWindowPeakLocator
           The signal is divided into windows and one local maximum is extracted
           from each window. The detected peaks are then sorted by descending
           height.

        2. GlobalPeakLocator
           The strongest sample in the full signal is selected as the peak.

        In addition to processing a single 1D signal, locators can process a
        flat segmented Python dictionary of the form

            {
                "segment_id": [...],
                "Time": <ignored>,
                "forward": array([...]),
                "side": array([...]),
                ...
            }

        The "Time" entry is ignored. Every other entry is interpreted as a
        signal channel and processed independently.
    )pbdoc";

    py::class_<BasePeakLocator, std::shared_ptr<BasePeakLocator>>(module, "BasePeakLocator")
        .def_readonly(
            "max_number_of_peaks",
            &BasePeakLocator::max_number_of_peaks,
            R"pbdoc(
                Maximum number of peaks stored in the fixed size output buffers.
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

                    and, when enabled at construction:
                        - "Width": peak widths in samples
                        - "Area": peak areas
            )pbdoc"
        )
        .def(
            "compute",
            &BasePeakLocator::compute,
            py::arg("array"),
            R"pbdoc(
                Run peak detection on a single 1D signal.

                Parameters
                ----------
                array : array-like of float
                    Input signal values.

                Notes
                -----
                This method updates the internal buffers of the locator but does
                not itself return a dictionary. To directly obtain the computed
                metrics, use `get_metrics(...)`.
            )pbdoc"
        )
        .def(
            "run",
            [](const BasePeakLocator& self, const py::dict& segmented_signal_dictionary) -> py::dict {
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
                        flat_signal_dictionary
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
                The regrouping and segmented batch processing are handled in C++.
            )pbdoc"
        );

    py::class_<SlidingWindowPeakLocator, BasePeakLocator, std::shared_ptr<SlidingWindowPeakLocator>>(
        module,
        "SlidingWindowPeakLocator",
        R"pbdoc(
            Sliding window peak detector for 1D signals.

            One local maximum is extracted per window. The resulting peaks are
            sorted by descending height, and the strongest peaks are returned in
            fixed size output arrays.

            Optional metrics:
                - Width: number of contiguous samples above
                  `threshold * peak_height`
                - Area: sum of signal values over the same support
        )pbdoc"
    )
        .def(
            py::init<int, int, int, int, bool, bool, double>(),
            py::arg("window_size"),
            py::arg("window_step") = -1,
            py::arg("max_number_of_peaks") = 5,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("threshold") = 0.5,
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
                threshold : float, default=0.5
                    Fraction of peak height used to define the support of the
                    peak for width and area calculations.
            )pbdoc"
        );

    py::class_<GlobalPeakLocator, BasePeakLocator, std::shared_ptr<GlobalPeakLocator>>(
        module,
        "GlobalPeakLocator",
        R"pbdoc(
            Global peak detector for 1D signals.

            This locator identifies the maximum value over the full signal and
            can optionally compute the width and area of that peak.
        )pbdoc"
    )
        .def(
            py::init<int, int, bool, bool, double>(),
            py::arg("max_number_of_peaks") = 1,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("threshold") = 0.5,
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
                    Whether to compute the width of the detected peak.
                compute_area : bool, default=False
                    Whether to compute the area of the detected peak.
                threshold : float, default=0.5
                    Fraction of peak height used to define the support of the
                    peak for width and area calculations.
            )pbdoc"
        );
}
