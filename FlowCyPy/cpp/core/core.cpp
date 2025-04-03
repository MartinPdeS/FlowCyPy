#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <stdexcept>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

class FlowCyPySim {
    py::array_t<double> widths;
    // py::array_t<double> m_centers;
    // py::array_t<double> m_coupling_power;
    // py::array_t<double> m_time_array;
    // double m_background_power;

public:
    FlowCyPySim() = default;

    FlowCyPySim(
        const py::array_t<double> &widths
    ) : widths(widths) {}

    // FlowCyPySim(
    //     const py::array_t<double> &widths,
    //     const py::array_t<double> &centers,
    //     const py::array_t<double> &coupling_power,
    //     const py::array_t<double> &time_array,
    //     double background_power
    // )
    // : m_widths(widths), m_centers(centers), m_coupling_power(coupling_power), m_time_array(time_array), m_background_power(background_power)
    // {
        // // --- Basic shape checks ---
        // auto w = m_widths.unchecked<1>();
        // auto c = m_centers.unchecked<1>();
        // auto p = m_coupling_power.unchecked<1>();

        // if (w.shape(0) != c.shape(0) || w.shape(0) != p.shape(0)) {
        //     throw std::runtime_error("widths, centers, coupling_power must have the same length.");
        // }
        // if (m_time_array.ndim() != 1) {
        //     throw std::runtime_error("time_array must be 1D.");
        // }
    // }

    // py::array_t<double> getAcquisition() {
    //     // Get unchecked access to the time array.
    //     auto t = m_time_array.unchecked<1>();
    //     size_t nTimes = t.shape(0);

    //     // Create output array, initialized to background_power.
    //     py::array_t<double> total_power(nTimes);
    //     auto r = total_power.mutable_unchecked<1>();
    //     for (size_t i = 0; i < nTimes; ++i) {
    //         r(i) = m_background_power;
    //     }

    //     // Get unchecked access to particle parameters.
    //     auto w = m_widths.unchecked<1>();
    //     auto c = m_centers.unchecked<1>();
    //     auto p_arr = m_coupling_power.unchecked<1>();
    //     size_t nParticles = w.shape(0);

    //     // Parallelize the outer loop over particles.
    //     // #pragma omp parallel for
    //     for (size_t i = 0; i < nParticles; ++i) {
    //         double w_val = w(i);
    //         double c_val = c(i);
    //         double p_val = p_arr(i);
    //         double inv_denom = 1.0 / (2.0 * w_val * w_val);

    //         for (size_t t_idx = 0; t_idx < nTimes; ++t_idx) {
    //             double dt = t(t_idx) - c_val;
    //             double gauss_val = p_val * std::exp(- (dt * dt) * inv_denom);
    //             // Use atomic update to avoid race conditions
    //             // #pragma omp atomic
    //             r(t_idx) += gauss_val;
    //         }
    //     }
    //     return total_power;
    // }
};


