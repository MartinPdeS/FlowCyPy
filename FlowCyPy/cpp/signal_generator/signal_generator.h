#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class SignalGenerator {
public:

    py::buffer signal;

    // Constructor taking a std::vector<double> by value.
    SignalGenerator(py::buffer signal) : signal(signal) {
        py::buffer_info info = this->signal.request();

        if (info.ndim != 1 || info.format != py::format_descriptor<double>::format())
            throw std::runtime_error("Expected a 1D float64 output array");

    };

    void pulse_generation(
        const py::buffer &widths,
        const py::buffer &centers,
        const py::buffer &coupling_power,
        const py::buffer &time_array,
        const double background_power
    );

    void add_gaussian_noise(double mean, double standard_deviation);

    void add_poisson_noise();

    void fft_filtering(double dt, double cutoff_freq, int order = 1);


    /**
     * @brief Performs baseline restoration on a signal using a rolling window minimum.
     *
     * For each index \( i \) (with \( i \ge 1 \)) in the input signal, this function computes
     * the minimum value among the previous `window_size` samples (i.e. indices from
     * \(\max(0, i - \text{window_size})\) to \( i-1 \)) based on the original unmodified signal.
     * It then subtracts that minimum value from the current sample.
     *
     * If `window_size == -1`, then for each \( i > 0 \) the function uses the minimum value
     * from indices \([0, i)\).
     *
     * @param signal The input signal vector. The function does not update the original signal in-place
     *               during computation; instead, it computes a new baseline-restored signal and writes
     *               it back into the same vector.
     * @param window_size The number of previous samples to consider for the minimum. If set to -1,
     *                    the window is treated as infinite (using all samples from index 0 to \(i-1\)).
     */
    void apply_baseline_restoration(int window_size);









};