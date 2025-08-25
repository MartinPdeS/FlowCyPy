#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "utils.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_utils, module) {
    module.doc() = "Signal processing utility functions for filtering, noise, and pulse generation.";

    // ----------------------------
    // Filtering Functions
    // ----------------------------
    module.def(
        "butterworth_lowpass_filter",
        &utils::apply_butterworth_lowpass_filter_to_signal,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff_frequency"),
        py::arg("order"),
        py::arg("gain") = 1.0,
        R"pbdoc(
        Apply a Butterworth low-pass filter to a signal.

        Parameters
        ----------
        signal : List[float]
            Input signal vector.
        sampling_rate : float
            Sampling rate in Hz.
        cutoff_frequency : float
            Cutoff frequency in Hz.
        order : int
            Filter order.
        gain : float, optional
            Optional scaling gain (default is 1.0).

        Returns
        -------
        List[float]
            Filtered signal.
        )pbdoc"
    );

    module.def(
        "bessel_lowpass_filter",
        &utils::apply_bessel_lowpass_filter_to_signal,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff_frequency"),
        py::arg("order"),
        py::arg("gain") = 1.0,
        R"pbdoc(
        Apply a Bessel low-pass filter to a signal.

        Parameters
        ----------
        signal : List[float]
            Input signal vector.
        sampling_rate : float
            Sampling rate in Hz.
        cutoff_frequency : float
            Cutoff frequency in Hz.
        order : int
            Filter order.
        gain : float, optional
            Optional scaling gain (default is 1.0).

        Returns
        -------
        List[float]
            Filtered signal.
        )pbdoc"
    );

    module.def(
        "baseline_restoration",
        &utils::apply_baseline_restoration_to_signal,
        py::arg("signal"),
        py::arg("window_size"),
        R"pbdoc(
        In-place baseline restoration using a moving minimum.

        Parameters
        ----------
        signal : List[float]
            Input/output signal buffer.
        window_size : int
            Size of the sliding window for baseline estimation.
        )pbdoc"
    );

    // ----------------------------
    // Noise Functions
    // ----------------------------
    module.def(
        "add_gaussian_noise",
        &utils::add_gaussian_noise_to_signal,
        py::arg("signal"),
        py::arg("mean"),
        py::arg("standard_deviation"),
        R"pbdoc(
        Add Gaussian noise in-place to a signal.

        Parameters
        ----------
        signal : List[float]
            Signal buffer to modify.
        mean : float
            Mean of the noise distribution.
        standard_deviation : float
            Standard deviation of the noise.
        )pbdoc"
    );

    module.def(
        "add_poisson_noise",
        &utils::add_poisson_noise_to_signal,
        py::arg("signal"),
        R"pbdoc(
        Add Poisson-distributed noise in-place to a non-negative signal.

        Parameters
        ----------
        signal : List[float]
            Signal buffer to modify. Must be non-negative.
        )pbdoc"
    );

    // ----------------------------
    // Pulse Generation
    // ----------------------------
    module.def(
        "generate_pulses",
        &utils::generate_pulses_signal,
        py::arg("signal"),
        py::arg("widths"),
        py::arg("centers"),
        py::arg("coupling_power"),
        py::arg("time"),
        py::arg("background_power"),
        R"pbdoc(
        Generate Gaussian pulses and add them to a signal buffer.

        Each pulse is defined by a center and width, and added with specified coupling and background power.

        Parameters
        ----------
        signal : List[float]
            Output signal buffer to modify.
        widths : List[float]
            List of pulse widths.
        centers : List[float]
            List of pulse center times.
        coupling_power : float
            Amplitude of each Gaussian pulse.
        time : List[float]
            Time axis corresponding to the signal.
        background_power : float
            Constant background signal level.
        )pbdoc"
    );
}
