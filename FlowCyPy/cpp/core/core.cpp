// #include "core.h"
// #include <stdexcept>

// #include <pybind11/pybind11.h>
// #include <pybind11/stl.h>
// #include <pybind11/numpy.h>
// namespace py = pybind11;

// FlowCyPySim::FlowCyPySim(
//     const py::array_t<double> &widths,
//     const py::array_t<double> &centers,
//     const py::array_t<double> &coupling_power,
//     const py::array_t<double> &time_array,
//     const double background_power
// ) : widths(widths), centers(centers), coupling_power(coupling_power), time_array(time_array), background_power(background_power)
// {
//     if (this->widths.size() != this->centers.size() || this->widths.size() != this->coupling_power.size())
//         throw std::runtime_error("widths, centers, coupling_power must have the same length.");
// }

// py::array_t<double> FlowCyPySim::get_acquisition() {
//     // Create output array, initialized to background_power.
//     py::array_t<double> total_power(time_array.size());
//     auto r = total_power.mutable_unchecked<1>();

//     for (size_t i = 0; i < time_array.size(); ++i)
//         r(i) = background_power;

//     // Parallelize the outer loop over particles.
//     #pragma omp parallel for
//     for (size_t i = 0; i < widths.size(); ++i) {
//         double inv_denom = 1.0 / (2.0 * this->widths[i] * this->widths[i]);

//         for (size_t t_idx = 0; t_idx < time_array.size(); ++t_idx) {
//             double dt = time_array[t_idx] - this->centers[i];
//             double gauss_val = this->coupling_power[i] * std::exp(- (dt * dt) * inv_denom);
//             // Use atomic update to avoid race conditions
//             #pragma omp atomic
//             r(t_idx) += gauss_val;
//         }
//     }
//     return total_power;
// }









#include "core.h"
#include <stdexcept>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

FlowCyPySim::FlowCyPySim(
    const py::array_t<double> &widths,
    const py::array_t<double> &centers,
    const py::array_t<double> &coupling_power,
    const py::array_t<double> &time_array,
    const double background_power
)
{
    if (this->widths.request().size != this->centers.request().size || this->widths.request().size != this->coupling_power.request().size)
        throw std::runtime_error("widths, centers, coupling_power must have the same length.");
}

py::array_t<double> FlowCyPySim::get_acquisition() {
    // // Create output array, initialized to background_power.
    // py::array_t<double> total_power(time_array.size());
    // auto r = total_power.mutable_unchecked<1>();

    // for (size_t i = 0; i < time_array.size(); ++i)
    //     r(i) = background_power;

    // // Parallelize the outer loop over particles.
    // #pragma omp parallel for
    // for (size_t i = 0; i < widths.size(); ++i) {
    //     double inv_denom = 1.0 / (2.0 * this->widths[i] * this->widths[i]);

    //     for (size_t t_idx = 0; t_idx < time_array.size(); ++t_idx) {
    //         double dt = time_array[t_idx] - this->centers[i];
    //         double gauss_val = this->coupling_power[i] * std::exp(- (dt * dt) * inv_denom);
    //         // Use atomic update to avoid race conditions
    //         #pragma omp atomic
    //         r(t_idx) += gauss_val;
    //     }
    // }
    // return total_power;
}
