#include "signal_generator.h"

#include <stdexcept>
#include <random>
#include <fftw3.h>
#include <cmath>

namespace py = pybind11;

void lowpass_filter(py::array signal, double dt, double cutoff_frequency, int order) {
    auto buf = signal.request();

    if (buf.ndim != 1 || buf.format != py::format_descriptor<double>::format()) {
        throw std::runtime_error("Output must be a 1D float64 NumPy array.");
    }

    const size_t N = buf.shape[0];
    double* data = static_cast<double*>(buf.ptr);

    // Allocate temporary FFT buffers
    double* in = (double*) fftw_malloc(sizeof(double) * N);
    fftw_complex* out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * (N/2 + 1));

    // Copy data to FFT input buffer
    std::copy(data, data + N, in);

    // Create forward FFT plan
    fftw_plan forward = fftw_plan_dft_r2c_1d(static_cast<int>(N), in, out, FFTW_ESTIMATE);
    fftw_execute(forward);

    const double df = 1.0 / (N * dt);

    for (size_t k = 0; k <= N / 2; ++k) {
        double f = k * df;
        double H_single = 1.0 / std::sqrt(1.0 + std::pow(f / cutoff_frequency, 2));
        double H = std::pow(H_single, order);
        out[k][0] *= H;
        out[k][1] *= H;
    }

    // Create backward FFT plan (inverse FFT)
    fftw_plan backward = fftw_plan_dft_c2r_1d(static_cast<int>(N), out, in, FFTW_ESTIMATE);
    fftw_execute(backward);

    // Normalize and write back into original buffer
    for (size_t i = 0; i < N; ++i) {
        data[i] = in[i] / static_cast<double>(N);
    }

    // Clean up
    fftw_destroy_plan(forward);
    fftw_destroy_plan(backward);
    fftw_free(in);
    fftw_free(out);
}

void SignalGenerator::pulse_generation(
    const py::buffer &widths,
    const py::buffer &centers,
    const py::buffer &coupling_power,
    const py::buffer &time,
    const double background_power
) {
    double* output_ptr = static_cast<double*>(this->signal.request().ptr);

    if (widths.request().size != centers.request().size || widths.request().size != coupling_power.request().size)
        throw std::runtime_error("widths, centers, coupling_power must have the same length.");

    size_t
        time_size = time.request().size,
        n_pulses = widths.request().size;


    for (size_t i = 0; i < time_size; ++i)
        output_ptr[i] = background_power;

    double
        *widths_ptr = static_cast<double*>(widths.request().ptr),
        *centers_ptr = static_cast<double*>(centers.request().ptr),
        *coupling_power_ptr = static_cast<double*>(coupling_power.request().ptr),
        *time_ptr = static_cast<double*>(time.request().ptr);


    // #pragma omp parallel for  // Parallelize the outer loop over particles.
    for (size_t i = 0; i < n_pulses; ++i) {
        double inv_denom = 1.0 / (2.0 * widths_ptr[i] * widths_ptr[i]);

        for (size_t t_idx = 0; t_idx < time_size; ++t_idx) {

            double dt = time_ptr[t_idx] - centers_ptr[i];
            double gauss_val = coupling_power_ptr[i] * std::exp(- (dt * dt) * inv_denom);

            // #pragma omp atomic  // Use atomic update to avoid race conditions
            output_ptr[t_idx] += gauss_val;
        }
    }
}


void SignalGenerator::add_gaussian_noise(double mean, double standard_deviation) {
    py::buffer_info info = this->signal.request();

    if (info.ndim != 1 || info.format != py::format_descriptor<double>::format()) {
        throw std::runtime_error("Output must be a 1D float64 NumPy array");
    }

    double* data = static_cast<double*>(info.ptr);
    const size_t size = info.shape[0];

    std::default_random_engine rng(std::random_device{}());
    std::normal_distribution<double> dist(mean, standard_deviation);

    for (size_t i = 0; i < size; ++i)
        data[i] += dist(rng);
}


void SignalGenerator::add_poisson_noise() {
    auto info = this->signal.request();

    if (info.ndim != 1 || info.format != py::format_descriptor<double>::format()) {
        throw std::runtime_error("Expected a 1D float64 output array");
    }

    double* data = static_cast<double*>(info.ptr);
    const size_t size = info.shape[0];

    std::default_random_engine rng(std::random_device{}());

    for (size_t i = 0; i < size; ++i) {
        if (data[i] < 0.0) {
            throw std::runtime_error("Poisson noise requires non-negative values");
        }

        std::poisson_distribution<int> dist(data[i]);
        data[i] = static_cast<double>(dist(rng));
    }
}


void SignalGenerator::lowpass_filter(double dt, double cutoff_frequency, int order) {
    auto buf = this->signal.request();

    if (buf.ndim != 1 || buf.format != py::format_descriptor<double>::format()) {
        throw std::runtime_error("Output must be a 1D float64 NumPy array.");
    }

    const size_t N = buf.shape[0];
    double* data = static_cast<double*>(buf.ptr);

    // Allocate temporary FFT buffers
    double* in = (double*) fftw_malloc(sizeof(double) * N);
    fftw_complex* out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * (N/2 + 1));

    // Copy data to FFT input buffer
    std::copy(data, data + N, in);

    // Create forward FFT plan
    fftw_plan forward = fftw_plan_dft_r2c_1d(static_cast<int>(N), in, out, FFTW_ESTIMATE);
    fftw_execute(forward);

    const double df = 1.0 / (N * dt);

    for (size_t k = 0; k <= N / 2; ++k) {
        double f = k * df;
        double H_single = 1.0 / std::sqrt(1.0 + std::pow(f / cutoff_frequency, 2));
        double H = std::pow(H_single, order);
        out[k][0] *= H;
        out[k][1] *= H;
    }

    // Create backward FFT plan (inverse FFT)
    fftw_plan backward = fftw_plan_dft_c2r_1d(static_cast<int>(N), out, in, FFTW_ESTIMATE);
    fftw_execute(backward);

    // Normalize and write back into original buffer
    for (size_t i = 0; i < N; ++i) {
        data[i] = in[i] / static_cast<double>(N);
    }

    // Clean up
    fftw_destroy_plan(forward);
    fftw_destroy_plan(backward);
    fftw_free(in);
    fftw_free(out);
}



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
void SignalGenerator::apply_baseline_restoration(int window_size)
{
    size_t n = this->signal.request().size;
    double* signal_ptr = static_cast<double*>(this->signal.request().ptr);

    // Make a copy of the original signal so that modifications do not affect future computations.
    std::vector<double> orig(signal_ptr, signal_ptr + signal.request().shape[0]);

    // Case: Infinite window (-1) => use all previous samples [0, i)
    if (window_size == -1)
    {
        double global_min = orig[0];
        // For i==0, no previous sample exists, so leave signal[0] unchanged.
        for (size_t i = 1; i < n; ++i)
        {
            global_min = std::min(global_min, orig[i]);  // Now look until the last point included
            // global_min = std::min(global_min, orig[i - 1]);  // Originally for look until the last point excluded
            signal_ptr[i] = orig[i] - global_min;
        }
        return;
    }

    // For a finite window: for each index i, consider the window [max(0, i-window_size), i)
    signal_ptr[0] = 0;  // No previous samples, so leave the first sample unchanged.
    for (size_t i = 1; i < n; ++i)
    {
        size_t start = (i < static_cast<size_t>(window_size)) ? 0 : i - window_size;
        double local_min = *std::min_element(orig.begin() + start, orig.begin() + i + 1);  // Now look until the last point included
        // double local_min = *std::min_element(orig.begin() + start, orig.begin() + i);  // Originally for look until the last point excluded
        signal_ptr[i] = orig[i] - local_min;
    }
}

