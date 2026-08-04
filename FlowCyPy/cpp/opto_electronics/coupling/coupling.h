#pragma once

#include <pybind11/pybind11.h>

namespace py = pybind11;

/**
 * @brief Compute sequential PyMieSim scattering for event frames.
 *
 * The class owns references to the Python source and detector models. PyMieSim
 * remains the numerical scattering backend; this native layer performs the
 * event-frame iteration and setup construction without duplicating its physics.
 */
class ScatteringModel {
public:
    ScatteringModel(py::object source, py::object detector);

    /** Compute detector coupling for every non-empty event frame in place. */
    void run(const py::object& event_frames, bool compute_cross_section = false);

private:
    py::object source_;
    py::object detector_;

    py::object build_experiment(const py::object& event_dataframe);
    py::object build_source_set(const py::object& event_dataframe, std::size_t count);
    py::object build_detector_set(std::size_t count);
    py::object build_scatterer_set(const py::object& event_dataframe, std::size_t count);
    void write_results(
        const py::object& event_dataframe,
        const py::object& experiment,
        bool compute_cross_section
    );
};
