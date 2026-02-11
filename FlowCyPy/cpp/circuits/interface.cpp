#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <pint/pint.h>
#include "circuits.h"

namespace py = pybind11;

PYBIND11_MODULE(circuits, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"pbdoc(
        FlowCyPy C++ Circuit Interface

        This module exposes C++ signal processing circuits to Python using pybind11.
        It includes base and derived filter classes for signal conditioning tasks,
        such as baseline restoration and low-pass filtering.
    )pbdoc";

    py::class_<BaseCircuit, std::shared_ptr<BaseCircuit>>(module, "BaseCircuit")
        .def(
            "process",
            &BaseCircuit::process,
            R"pbdoc(
                Process the input signal.

                This method should be overridden by derived classes to implement specific
                signal processing behavior.

                Returns
                -------
                None
            )pbdoc"
        )
        ;

    py::class_<BaseLineRestoration, std::shared_ptr<BaseLineRestoration>>(module, "BaselineRestorator")
        .def(
            py::init(
                [ureg](const py::object &window_size_py){
                    double window_size_second = window_size_py.attr("to")("second").attr("magnitude").cast<double>();

                    return std::make_shared<BaseLineRestoration>(
                        window_size_second
                    );
                }
            ),
            py::arg("window_size")
        )
        .def(
            py::init<>(),
            R"pbdoc(
                Initialize the baseline restoration filter with default parameters.
            )pbdoc"
        )
        .def_readwrite(
            "window_size",
            &BaseLineRestoration::window_size,
            R"pbdoc(
                int: Size of the sliding window used for baseline estimation.
            )pbdoc"
        )
        .def(
            "process",
            &BaseLineRestoration::process,
            py::arg("signal_generator"),
            R"pbdoc(
                Process the input signal and perform baseline restoration.

                Returns
                -------
                None
            )pbdoc"
        )
        .def("__repr__",
            [](const BaseLineRestoration &self) {
                return "<BaseLineRestoration window_size=" + std::to_string(self.window_size) + ">";
            }
        )
        ;

    py::class_<ButterworthLowPassFilter, std::shared_ptr<ButterworthLowPassFilter>>(module, "ButterworthLowPass")
        .def(
            py::init<>(
                [ureg](
                    const py::object &cutoff,
                    const size_t order,
                    const double gain
                ) {
                    double cutoff_hertz = cutoff.attr("to")("hertz").attr("magnitude").cast<double>();

                    return std::make_shared<ButterworthLowPassFilter>(
                        cutoff_hertz,
                        order,
                        gain
                    );
                }
            ),
            py::arg("cutoff"),
            py::arg("order"),
            py::arg("gain")
        )
        .def_readonly(
            "cutoff",
            &ButterworthLowPassFilter::cutoff_frequency,
            R"pbdoc(
                float: Cutoff frequency in Hz.
            )pbdoc"
        )
        .def_readonly(
            "order",
            &ButterworthLowPassFilter::order,
            R"pbdoc(
                int: Order of the filter.
            )pbdoc"
        )
        .def_readonly(
            "gain",
            &ButterworthLowPassFilter::gain,
            R"pbdoc(
                float: Output gain factor.
            )pbdoc"
        )
        .def(
            "process",
            &ButterworthLowPassFilter::process,
            py::arg("signal_generator"),
            R"pbdoc(
                Apply the Butterworth filter to the input signal.

                Returns
                -------
                None
            )pbdoc"
        )
        .def("__repr__", [](const ButterworthLowPassFilter &self) {
            return ", cutoff=" + std::to_string(self.cutoff_frequency) +
                   ", order=" + std::to_string(self.order) +
                   ", gain=" + std::to_string(self.gain) + ">";
        });

    py::class_<BesselLowPassFilter, std::shared_ptr<BesselLowPassFilter>>(module, "BesselLowPass")
        .def(py::init<>())
        .def(
            py::init(
                [ureg](
                    const py::object &cutoff,
                    const size_t order,
                    const double gain
                ) {
                    double cutoff_hertz = cutoff.attr("to")("hertz").attr("magnitude").cast<double>();

                    return std::make_shared<BesselLowPassFilter>(
                        cutoff_hertz,
                        order,
                        gain
                    );
                }
            ),
            py::arg("cutoff"),
            py::arg("order"),
            py::arg("gain")
        )
        .def_readonly(
            "cutoff",
            &BesselLowPassFilter::cutoff_frequency,
            R"pbdoc(
                float: Cutoff frequency in Hz.
            )pbdoc"
        )
        .def_readonly(
            "order",
            &BesselLowPassFilter::order,
            R"pbdoc(
                int: Order of the filter.
            )pbdoc"
        )
        .def_readonly(
            "gain",
            &BesselLowPassFilter::gain,
            R"pbdoc(
                float: Output gain factor.
            )pbdoc"
        )
        .def(
            "process",
            &BesselLowPassFilter::process,
            py::arg("signal_generator"),
            R"pbdoc(
                Apply the Bessel filter to the input signal.

                Returns
                -------
                None
            )pbdoc"
        )
        .def("__repr__", [](const BesselLowPassFilter &self) {
            return ", cutoff=" + std::to_string(self.cutoff_frequency) +
                   ", order=" + std::to_string(self.order) +
                   ", gain=" + std::to_string(self.gain) + ">";
        });
}
