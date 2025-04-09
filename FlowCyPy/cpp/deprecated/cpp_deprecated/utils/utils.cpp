#include <stdlib.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <random>
#include <cstddef>
#include <cmath>
#include <fftw3.h>

namespace py = pybind11;

/**
 * @brief Adds Gaussian noise to the input signal in-place.
 *
 * This function modifies the provided NumPy array by adding random Gaussian noise to each element.
 * The noise is generated using the C++ standard library's random number generator with a specified mean
 * and standard deviation.
 *
 * @param py_signal NumPy array containing the signal to be modified (in-place).
 * @param mean The mean of the Gaussian noise (default: 0.0).
 * @param std_dev The standard deviation of the Gaussian noise (default: 1.0).
 */
void add_gaussian_noise(py::array_t<double> &py_signal, double mean = 0.0, double std_dev = 1.0)
{
    // Get buffer information from the input array.
    py::buffer_info buf = py_signal.request();
    size_t n_samples = buf.shape[0];
    double *data = static_cast<double *>(buf.ptr);

    // Initialize random number generator with a non-deterministic seed.
    std::random_device rd;
    std::default_random_engine generator(rd());
    std::normal_distribution<double> distribution(mean, std_dev);

    // Add Gaussian noise to each element of the signal.
    for (size_t i = 0; i < n_samples; ++i)
        data[i] += distribution(generator);
}

py::array_t<double> fft_filter(py::array_t<double> input, double dt, double fc, int order = 1) {
    // Get buffer info from the input numpy array.
    py::buffer_info buf = input.request();
    if (buf.ndim != 1)
        throw std::runtime_error("Input must be one-dimensional");

    size_t N = buf.shape[0];
    double* in_data = static_cast<double*>(buf.ptr);

    // Allocate memory for FFTW arrays.
    // 'in' for the real input and 'out' for the complex FFT output.
    double* in = (double*) fftw_malloc(sizeof(double) * N);
    fftw_complex* out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * (N/2 + 1));

    // Copy input data to the FFTW input array.
    for (size_t i = 0; i < N; i++) {
        in[i] = in_data[i];
    }

    // Create a plan for the forward FFT (real-to-complex) and execute it.
    fftw_plan forwardPlan = fftw_plan_dft_r2c_1d(static_cast<int>(N), in, out, FFTW_ESTIMATE);
    fftw_execute(forwardPlan);

    // Frequency resolution is df = 1/(N * dt)
    double df = 1.0 / (N * dt);

    // Apply the cascaded low-pass filter in the frequency domain.
    // The single-stage filter response is H(f) = 1/sqrt(1 + (f/fc)^2)
    // and the cascaded response is H(f)^order.
    for (size_t k = 0; k < (N/2 + 1); k++) {
        double f = k * df;
        double H_single = 1.0 / std::sqrt(1.0 + std::pow(f / fc, 2));
        double H = std::pow(H_single, order);  // Emulate cascading
        out[k][0] *= H; // scale the real part
        out[k][1] *= H; // scale the imaginary part
    }

    // Create a plan for the inverse FFT (complex-to-real) and execute it.
    fftw_plan backwardPlan = fftw_plan_dft_c2r_1d(static_cast<int>(N), out, in, FFTW_ESTIMATE);
    fftw_execute(backwardPlan);

    // Normalize the inverse FFT result (FFTW does not perform normalization).
    for (size_t i = 0; i < N; i++) {
        in[i] /= N;
    }

    // Create a NumPy array to hold the filtered result.
    auto result = py::array_t<double>(N);
    py::buffer_info res_buf = result.request();
    double* res_ptr = static_cast<double*>(res_buf.ptr);
    for (size_t i = 0; i < N; i++) {
        res_ptr[i] = in[i];
    }

    // Cleanup FFTW resources.
    fftw_destroy_plan(forwardPlan);
    fftw_destroy_plan(backwardPlan);
    fftw_free(in);
    fftw_free(out);

    return result;
}