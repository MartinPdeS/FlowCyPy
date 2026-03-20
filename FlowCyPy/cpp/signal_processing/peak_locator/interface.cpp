#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "peak_locator.h"

namespace py = pybind11;

PYBIND11_MODULE(peak_locator, module) {
    module.doc() = R"pbdoc(
        Peak locator module for identifying signal peaks.

        This module provides fast C++ implementations for locating peaks in 1D signals
        using overlapping sliding windows or global search strategies.

        If `window_step` is not explicitly set in `SlidingWindowPeakLocator`,
        it defaults to `window_size`, resulting in non-overlapping windows.
    )pbdoc";

    py::class_<BasePeakLocator, std::shared_ptr<BasePeakLocator>>(module, "BasePeakLocator")
        .def_readonly(
            "max_number_of_peaks",
            &BasePeakLocator::max_number_of_peaks
        )
        .def(
            "get_metrics",
            &BasePeakLocator::get_metrics,
            R"pbdoc(
                Get the computed peak metrics.

                Returns
                -------
                dict of numpy.ndarray
                    A dictionary containing arrays of computed peak properties (e.g., positions, widths, areas).
            )pbdoc"
        )
        .def(
            "compute",
            &BasePeakLocator::compute,
            R"pbdoc(
                Perform peak detection on the entire signal.

                Parameters
                ----------
                signal : numpy.ndarray
                    The input 1D signal array.

                Returns
                -------
                dict of numpy.ndarray
                    A dictionary containing arrays for global peak positions and optionally widths/areas.
            )pbdoc"
        )
        .def(
            "run",
            [](BasePeakLocator& self, py::object signal_dataframe) -> py::object {
                py::module_ pandas_module = py::module_::import("pandas");
                py::object peak_dataframe_class =
                    py::module_::import("FlowCyPy.sub_frames.peaks").attr("PeakDataFrame");

                py::object detector_names = signal_dataframe.attr("detector_names");
                py::object segment_ids = signal_dataframe
                    .attr("index")
                    .attr("get_level_values")("SegmentID")
                    .attr("unique")();

                py::object multi_index = pandas_module
                    .attr("MultiIndex")
                    .attr("from_product")(
                        py::make_tuple(
                            detector_names,
                            segment_ids,
                            py::module_::import("builtins").attr("range")(self.max_number_of_peaks)
                        ),
                        py::arg("names") = py::make_tuple("Detector", "SegmentID", "PeakID")
                    );

                py::object output_dataframe = pandas_module.attr("DataFrame")(
                    py::arg("index") = multi_index,
                    py::arg("columns") = py::make_tuple("Index", "Height", "Width", "Area")
                );

                output_dataframe.attr("sort_index")(py::arg("inplace") = true);

                for (py::handle detector_name_handle : detector_names) {
                    py::object detector_name = py::reinterpret_borrow<py::object>(detector_name_handle);

                    py::object detector_series = signal_dataframe.attr("__getitem__")(detector_name);
                    py::object grouped_detector_series = detector_series.attr("groupby")("SegmentID");

                    for (py::handle grouped_item_handle : grouped_detector_series) {
                        py::tuple grouped_item = py::reinterpret_borrow<py::tuple>(grouped_item_handle);

                        py::object segment_id = grouped_item[0];
                        py::object group = grouped_item[1];

                        std::vector<double> signal_vector =
                            group.attr("to_numpy")().cast<std::vector<double>>();

                        std::unordered_map<std::string, std::vector<double>> peak_metrics =
                            self.get_metrics(signal_vector);

                        for (const auto& [metric_name, metric_values] : peak_metrics) {
                            output_dataframe.attr("loc").attr("__setitem__")(
                                py::make_tuple(
                                    py::make_tuple(detector_name, segment_id),
                                    py::str(metric_name)
                                ),
                                py::cast(metric_values)
                            );
                        }
                    }
                }

                return peak_dataframe_class(output_dataframe);
            },
            py::arg("signal_dataframe"),
            R"pbdoc(
                Detect peaks for each detector and segment and return a PeakDataFrame.

                Parameters
                ----------
                signal_dataframe : pandas.DataFrame
                    Input segmented detector signal dataframe.

                Returns
                -------
                PeakDataFrame
                    MultiIndex dataframe containing peak metrics for each detector,
                    segment, and peak identifier.
            )pbdoc"
        )
        ;

    py::class_<SlidingWindowPeakLocator, BasePeakLocator, std::shared_ptr<SlidingWindowPeakLocator>>(module, "SlidingWindowPeakLocator",
        R"pbdoc(
            A sliding-window-based peak detection utility for 1D signals. This class segments the input signal
            into fixed-size windows (which can be overlapping if window_step is less than window_size) and identifies
            the local maximum in each window. Optionally, it computes additional metrics for each peak:
            - Width: the number of contiguous samples above a specified fraction of the peak's height.
            - Area: the sum of signal values under the peak within its window.

            The results are returned as a dictionary containing fixed-length arrays. If fewer peaks are detected than
            max_number_of_peaks, the arrays are padded with padding_value (for indices) or NaN (for numeric values).

            Parameters
            ----------
            window_size : int
                The size of the sliding window used for local peak detection.
            window_step : int, optional
                The step size between consecutive windows. If not provided or set to -1, defaults to window_size
                (i.e., non-overlapping windows). To create overlapping windows, specify a value less than window_size.
            max_number_of_peaks : int, optional
                The maximum number of peaks to report. If fewer peaks are detected, the results are padded. Default is 5.
            padding_value : int, optional
                The value used to pad the output array for indices when fewer than max_number_of_peaks peaks are found.
                Default is -1.
            compute_width : bool, optional
                If True, compute and return the width of each detected peak (in samples). Default is False.
            compute_area : bool, optional
                If True, compute and return the area (sum of signal values) under each detected peak. Default is False.
            threshold : float, optional
                The fraction of the peak's height used to determine the boundaries for width and area calculations.
                For example, a threshold of 0.5 uses 50% of the peak height as the cutoff. Default is 0.5.

            Returns
            -------
            dict
                A dictionary containing the following keys:
                - "Index": A fixed-length array of detected peak indices, padded as necessary.
                - "Height": A fixed-length array of the corresponding peak values.
                - "Width": (optional) A fixed-length array of computed peak widths (if compute_width is True).
                - "Area": (optional) A fixed-length array of computed peak areas (if compute_area is True).
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
            py::arg("threshold") = 0.5
        )
        ;

    py::class_<GlobalPeakLocator, BasePeakLocator, std::shared_ptr<GlobalPeakLocator>>(module, "GlobalPeakLocator",
        R"pbdoc(
            A peak detection utility that identifies the maximum value in each row of a 2D array.

            Optionally, the peak detection can also compute the width and area of the peak.

            The width is computed as the number of contiguous points around the maximum that remain above
            a specified fraction (threshold) of the maximum value. The area is the sum of the values over
            that same region.

            Parameters
            ----------
            padding_value : object, optional
                Value used to pad the output if a row contains no data. Default is -1.
            compute_width : bool, optional
                If True, the width of the peak (number of samples) is computed. Default is False.
            compute_area : bool, optional
                If True, the area (sum of values) of the peak is computed. Default is False.
            threshold : float, optional
                Fraction of the peak value used to determine the boundaries for width and area computation.
                For example, a threshold of 0.5 means the region above 50% of the maximum is considered.
                Default is 0.5.
        )pbdoc"
        )
        .def(py::init<int, int, bool, bool, double>(),
            py::arg("max_number_of_peaks") = 1,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("threshold") = 0.5
        )
    ;
}
