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
) : widths(widths), centers(centers), coupling_power(coupling_power), time_array(time_array), background_power(background_power)
{
    if (this->widths.request().size != this->centers.request().size || this->widths.request().size != this->coupling_power.request().size)
        throw std::runtime_error("widths, centers, coupling_power must have the same length.");
}

py::array_t<double> FlowCyPySim::get_acquisition() {
    size_t
        time_size = time_array.request().size,
        n_pulses = widths.request().size;

    py::array_t<double> total_power(time_size);

    double
        *time_ptr = static_cast<double*>(time_array.request().ptr),
        *widths_ptr = static_cast<double*>(widths.request().ptr),
        *centers_ptr = static_cast<double*>(centers.request().ptr),
        *coupling_ptr = static_cast<double*>(coupling_power.request().ptr),
        *power_ptr = static_cast<double*>(total_power.request().ptr);

    for (size_t i = 0; i < time_size; ++i)
        power_ptr[i] = background_power;


    #pragma omp parallel for  // Parallelize the outer loop over particles.
    for (size_t i = 0; i < n_pulses; ++i) {
        double inv_denom = 1.0 / (2.0 * widths_ptr[i] * widths_ptr[i]);

        for (size_t t_idx = 0; t_idx < time_size; ++t_idx) {
            double dt = time_ptr[t_idx] - centers_ptr[i];
            double gauss_val = coupling_ptr[i] * std::exp(- (dt * dt) * inv_denom);

            #pragma omp atomic  // Use atomic update to avoid race conditions
            power_ptr[t_idx] += gauss_val;
        }
    }
    return total_power;
}
