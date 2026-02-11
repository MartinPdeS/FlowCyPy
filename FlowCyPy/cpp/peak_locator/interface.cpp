#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "peak_locator.h"

PYBIND11_MODULE(peak_locator, module) {
    module.doc() = R"pbdoc(
        Peak locator module for identifying signal peaks.

        This module provides fast C++ implementations for locating peaks in 1D signals
        using overlapping sliding windows or global search strategies.

        If `window_step` is not explicitly set in `SlidingWindowPeakLocator`,
        it defaults to `window_size`, resulting in non-overlapping windows.
    )pbdoc";

    pybind11::class_<BasePeakLocator, std::shared_ptr<BasePeakLocator>>(module, "BasePeakLocator")
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
    ;

    pybind11::class_<SlidingWindowPeakLocator, BasePeakLocator, std::shared_ptr<SlidingWindowPeakLocator>>(module, "SlidingWindowPeakLocator",
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
            pybind11::init<int, int, int, int, bool, bool, double>(),
            pybind11::arg("window_size"),
            pybind11::arg("window_step") = -1,
            pybind11::arg("max_number_of_peaks") = 5,
            pybind11::arg("padding_value") = -1,
            pybind11::arg("compute_width") = false,
            pybind11::arg("compute_area") = false,
            pybind11::arg("threshold") = 0.5
        )
        ;

    pybind11::class_<GlobalPeakLocator, BasePeakLocator, std::shared_ptr<GlobalPeakLocator>>(module, "GlobalPeakLocator",
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
        .def(pybind11::init<int, int, bool, bool, double>(),
            pybind11::arg("max_number_of_peaks") = 1,
            pybind11::arg("padding_value") = -1,
            pybind11::arg("compute_width") = false,
            pybind11::arg("compute_area") = false,
            pybind11::arg("threshold") = 0.5
        )
    ;
}
