#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "peak_locator.h"

PYBIND11_MODULE(interface_peak_locator, module) {
    module.doc() = R"pbdoc(
        Peak locator module for identifying signal peaks.

        This module provides fast C++ implementations for locating peaks in 1D signals
        using overlapping sliding windows or global search strategies.

        If `window_step` is not explicitly set in `SlidingWindowPeakLocator`,
        it defaults to `window_size`, resulting in non-overlapping windows.
    )pbdoc";

    pybind11::class_<BasePeakLocator>(module, "BasePeakLocator")
        .def("get_metric",
            &BasePeakLocator::get_metric_py,
            R"pbdoc(
                Get the computed peak metrics.

                Returns
                -------
                dict of numpy.ndarray
                    A dictionary containing arrays of computed peak properties (e.g., positions, widths, areas).
            )pbdoc"
        )
    ;

    pybind11::class_<SlidingWindowPeakLocator, BasePeakLocator>(module, "SlidingWindowPeakLocator", R"pbdoc(
        Detect peaks in a signal using an overlapping sliding window strategy.

        Each window is processed independently to find local peaks, which can be useful
        for non-stationary signals or signals with multiple regions of interest.

        Parameters
        ----------
        window_size : int
            Size of the sliding window.
        window_step : int, optional
            Step size between successive windows. Defaults to `window_size` (no overlap).
        max_number_of_peaks : int, optional
            Maximum number of peaks to return per window.
        padding_value : int, optional
            Value to assign to missing results if fewer than `max_number_of_peaks` are found.
        compute_width : bool, optional
            Whether to compute full-width at half-maximum (FWHM) for each peak.
        compute_area : bool, optional
            Whether to compute area under each detected peak.
        threshold : float, optional
            Minimum normalized peak value (0–1) to be considered valid.
    )pbdoc")
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
        .def("compute", &SlidingWindowPeakLocator::compute, R"pbdoc(
            Perform peak detection on the signal.

            This method scans the signal using overlapping windows and identifies local peaks.

            Parameters
            ----------
            signal : numpy.ndarray
                The input 1D signal array.

            Returns
            -------
            dict of numpy.ndarray
                A dictionary containing per-window arrays for peak positions and optionally widths/areas.
        )pbdoc");

    pybind11::class_<GlobalPeakLocator, BasePeakLocator>(module, "GlobalPeakLocator", R"pbdoc(
        Detect peaks by analyzing the entire signal at once.

        This is best for stationary signals where global peak prominence is important.
        Unlike the sliding version, only one global pass is made across the full signal.

        Parameters
        ----------
        max_number_of_peaks : int, optional
            Maximum number of peaks to detect.
        padding_value : int, optional
            Value to assign to missing results if fewer than `max_number_of_peaks` are found.
        compute_width : bool, optional
            Whether to compute full-width at half-maximum (FWHM) for each peak.
        compute_area : bool, optional
            Whether to compute area under each detected peak.
        threshold : float, optional
            Minimum normalized peak value (0-1) to be considered valid.
    )pbdoc")
        .def(pybind11::init<int, int, bool, bool, double>(),
            pybind11::arg("max_number_of_peaks") = 1,
            pybind11::arg("padding_value") = -1,
            pybind11::arg("compute_width") = false,
            pybind11::arg("compute_area") = false,
            pybind11::arg("threshold") = 0.5
        )
        .def("compute", &GlobalPeakLocator::compute, R"pbdoc(
            Perform peak detection on the entire signal.

            Parameters
            ----------
            signal : numpy.ndarray
                The input 1D signal array.

            Returns
            -------
            dict of numpy.ndarray
                A dictionary containing arrays for global peak positions and optionally widths/areas.
        )pbdoc");
}
