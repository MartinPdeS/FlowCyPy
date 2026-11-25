#include <pybind11/pybind11.h>

#include "coupling.h"

namespace py = pybind11;

PYBIND11_MODULE(coupling_model, module) {
    module.doc() = R"pdoc(
        Native event-frame orchestration for PyMieSim scattering calculations.

        The numerical scattering backend remains PyMieSim. This extension
        constructs its sequential source, scatterer, and detector sets and writes
        the resulting quantities back into FlowCyPy event frames.
    )pdoc";

    py::class_<ScatteringModel>(
        module,
        "ScatteringModel",
        R"pdoc(
            Compute PyMieSim scattering signals for FlowCyPy event frames.

            Parameters
            ----------
            source : BaseSource
                Source model used to evaluate illumination amplitudes.
            detector : Detector
                Detector model used to construct the PyMieSim photodiode set.

            Notes
            -----
            ``run`` updates each non-empty event frame in place. Empty frames are
            skipped. PyMieSim remains responsible for the scattering physics and
            its sequential setup validation.
        )pdoc"
    )
        .def(
            py::init<py::object, py::object>(),
            py::arg("source"),
            py::arg("detector"),
            R"pdoc(
                Create a scattering model for one source and detector channel.

                Parameters
                ----------
                source : BaseSource
                    Illumination source.
                detector : Detector
                    Detection channel.
            )pdoc"
        )
        .def(
            "run",
            &ScatteringModel::run,
            py::arg("event_frames"),
            py::arg("compute_cross_section") = false,
            R"pdoc(
                Compute scattering for each event frame in place.

                Parameters
                ----------
                event_frames : iterable of EventDataFrame
                    Event frames containing spatial coordinates and scatterer
                    properties.
                compute_cross_section : bool, optional
                    If true, also writes the ``Csca`` column in square meters.

                Raises
                ------
                ValueError
                    If an event frame has an unsupported scatterer type.
            )pdoc"
        );
}
