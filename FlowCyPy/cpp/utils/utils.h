#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

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
void add_gaussian_noise(py::array_t<double> &py_signal, double mean = 0.0, double std_dev = 1.0);

py::array_t<double> fft_filter(py::array_t<double> input, double dt, double fc, int order = 1);