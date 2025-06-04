#include "signal_generator.h"



namespace py = pybind11;


void apply_baseline_restoration_to_signal(py::buffer signal, const int window_size)
{
    size_t n = signal.request().size;
    double* signal_ptr = static_cast<double*>(signal.request().ptr);

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


void butterworth_lowpass_filter(const py::buffer signal, const double sampling_rate, const double cutoff_frequency, const int order, const double gain) {
    double dt = 1. / sampling_rate;

    py::buffer_info buf = signal.request();

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
        data[i] = gain * in[i] / static_cast<double>(N);
    }

    // Clean up
    fftw_destroy_plan(forward);
    fftw_destroy_plan(backward);
    fftw_free(in);
    fftw_free(out);
}




void generate_pulses(
    py::buffer signal,
    const py::buffer &widths,
    const py::buffer &centers,
    const py::buffer &coupling_power,
    const py::buffer &time,
    const double background_power
) {
    double* output_ptr = static_cast<double*>(signal.request().ptr);

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




void add_gaussian_noise_to_signal(std::vector<double> &signal, const double mean, const double standard_deviation) {
    if (signal.empty()) {
        throw std::runtime_error("Signal vector is empty.");
    }
    std::default_random_engine rng(std::random_device{}());
    std::normal_distribution<double> dist(mean, standard_deviation);

    for (size_t i = 0; i < signal.size(); ++i)
        signal[i] += dist(rng);
}



void apply_bessel_lowpass_filter_to_signal(const py::buffer signal, const double sampling_rate, const double cutoff_frequency, const int order, const double gain) {
    double dt = 1. / sampling_rate;

    py::buffer_info buf = signal.request();

    if (buf.ndim != 1 || buf.format != py::format_descriptor<double>::format()) {
        throw std::runtime_error("Input must be a 1D float64 NumPy array.");
    }

    const size_t N = buf.shape[0];
    double* data = static_cast<double*>(buf.ptr);

    // Allocate temporary FFT buffers
    double* in = (double*) fftw_malloc(sizeof(double) * N);
    fftw_complex* out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * (N / 2 + 1));

    // Copy data to FFT input buffer
    std::copy(data, data + N, in);

    // Create forward FFT plan
    fftw_plan forward = fftw_plan_dft_r2c_1d(static_cast<int>(N), in, out, FFTW_ESTIMATE);
    fftw_execute(forward);

    const double df = 1.0 / (N * dt);

    for (size_t k = 0; k <= N / 2; ++k) {
        double f = k * df;
        // Define s = j * (f / cutoff_frequency)
        std::complex<double> s(0, f / cutoff_frequency);
        std::complex<double> H_complex;

        // Compute the Bessel filter transfer function based on the specified order.
        switch(order) {
            case 1:
                // Order 1: H(s) = 1 / (s + 1)
                H_complex = 1.0 / (s + 1.0);
                break;
            case 2:
                // Order 2: H(s) = 3 / (s^2 + 3s + 3)
                H_complex = 3.0 / (s * s + 3.0 * s + 3.0);
                break;
            case 3:
                // Order 3: H(s) = 15 / (s^3 + 6s^2 + 15s + 15)
                H_complex = 15.0 / (s * s * s + 6.0 * s * s + 15.0 * s + 15.0);
                break;
            case 4:
                // Order 4: H(s) = 105 / (s^4 + 10s^3 + 45s^2 + 105s + 105)
                H_complex = 105.0 / (s * s * s * s + 10.0 * s * s * s + 45.0 * s * s + 105.0 * s + 105.0);
                break;
            default:
                fftw_destroy_plan(forward);
                fftw_free(in);
                fftw_free(out);
                throw std::runtime_error("Bessel filter of the given order is not implemented.");
        }

        // Use the magnitude of the complex transfer function for amplitude attenuation.
        double H = std::abs(H_complex);
        out[k][0] *= H;
        out[k][1] *= H;
    }

    // Create backward FFT plan (inverse FFT)
    fftw_plan backward = fftw_plan_dft_c2r_1d(static_cast<int>(N), out, in, FFTW_ESTIMATE);
    fftw_execute(backward);

    // Normalize and write the filtered data back into the original buffer
    for (size_t i = 0; i < N; ++i) {
        data[i] = gain * in[i] / static_cast<double>(N);
    }

    // Clean up FFTW resources
    fftw_destroy_plan(forward);
    fftw_destroy_plan(backward);
    fftw_free(in);
    fftw_free(out);
}



void add_poisson_noise_to_signal(std::vector<double> &signal) {
    if (signal.empty()) {
        throw std::runtime_error("Signal vector is empty.");
    }

    std::default_random_engine rng(std::random_device{}());

    for (size_t i = 0; i < signal.size(); ++i) {
        if (signal[i] < 0.0) {
            throw std::runtime_error("Poisson noise requires non-negative values");
        }

        std::poisson_distribution<int> dist(signal[i]);
        signal[i] = static_cast<double>(dist(rng));
    }
}





