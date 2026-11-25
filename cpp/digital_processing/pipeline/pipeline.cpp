#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace {
struct DigitalProcessing {
    py::object discriminator;
    py::object peak_locator;
};
}

PYBIND11_MODULE(pipeline, module) {
    module.doc() = "Digital processing configuration for acquired signals.";
    py::module_::import("FlowCyPy.units");
    module.attr("discriminator") = py::module_::import("FlowCyPy.digital_processing.discriminator");
    module.attr("peak_locator") = py::module_::import("FlowCyPy.digital_processing.peak_locator");

    py::class_<DigitalProcessing>(module, "DigitalProcessing", R"doc(
        Configure triggering and peak extraction for an acquisition.

        Parameters
        ----------
        discriminator : BaseDiscriminator, optional
            Selects triggered segments from the analog signal.
        peak_locator : BasePeakLocator, optional
            Measures peaks in the digitized segments.
    )doc")
        .def(py::init<py::object, py::object>(),
             py::arg("discriminator") = py::none(), py::kw_only(),
             py::arg("peak_locator") = py::none())
        .def("__repr__", [](const DigitalProcessing& pipeline) {
            const auto stage_name = [](const py::object& stage) -> py::str {
                return stage.is_none() ? py::str("None") : py::str(py::type::of(stage).attr("__name__"));
            };
            return py::str("DigitalProcessing(discriminator={}, peak_locator={})")
                .format(stage_name(pipeline.discriminator),
                        stage_name(pipeline.peak_locator));
        })
        .def_readwrite("discriminator", &DigitalProcessing::discriminator)
        .def_readwrite("peak_locator", &DigitalProcessing::peak_locator);
}
