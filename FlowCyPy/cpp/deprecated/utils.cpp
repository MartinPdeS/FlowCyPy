#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <random>
#include <cstddef>

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
    {
        data[i] += distribution(generator);
    }
}

PYBIND11_MODULE(Interface, m) {
    m.doc() = "Module for in-place signal processing operations using C++ and pybind11";
    m.def("add_gaussian_noise", &add_gaussian_noise,
          py::arg("signal"),
          py::arg("mean") = 0.0,
          py::arg("std_dev") = 1.0,
          "Adds Gaussian noise (with specified mean and standard deviation) to the input signal in-place.");
}
