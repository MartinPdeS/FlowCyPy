#include "core.h"
#include <stdexcept>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

FlowCyPySim::FlowCyPySim(
    const std::vector<double> &widths,
    const std::vector<double> &centers,
    const std::vector<double> &coupling_power,
    const std::vector<double> &time_array,
    const double background_power
) : widths(widths), centers(centers), coupling_power(coupling_power), time_array(time_array), background_power(background_power)
{
    if (this->widths.size() != this->centers.size() || this->widths.size() != this->coupling_power.size())
        throw std::runtime_error("widths, centers, coupling_power must have the same length.");
}

std::vector<double> FlowCyPySim::get_acquisition() {
    size_t
        time_size = time_array.size(),
        n_pulses = widths.size();

    std::vector<double> total_power(time_size);

    for (size_t i = 0; i < time_size; ++i)
        total_power[i] = background_power;


    #pragma omp parallel for  // Parallelize the outer loop over particles.
    for (size_t i = 0; i < n_pulses; ++i) {
        double inv_denom = 1.0 / (2.0 * widths[i] * widths[i]);

        for (size_t t_idx = 0; t_idx < time_size; ++t_idx) {
            double dt = time_array[t_idx] - centers[i];
            double gauss_val = coupling_power[i] * std::exp(- (dt * dt) * inv_denom);

            #pragma omp atomic  // Use atomic update to avoid race conditions
            total_power[t_idx] += gauss_val;
        }
    }
    return total_power;
}
