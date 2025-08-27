#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "circuits.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_circuits, module) {
    module.doc() = R"pbdoc(
        FlowCyPy C++ Circuit Interface

        This module exposes C++ signal processing circuits to Python using pybind11.
        It includes base and derived filter classes for signal conditioning tasks,
        such as baseline restoration and low-pass filtering.
    )pbdoc";

    py::class_<BaseCircuit>(module, "BaseCircuit")
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

    py::class_<BaseLineRestoration, BaseCircuit>(module, "BaseLineRestoration")
        .def(
            py::init<>(),
            R"pbdoc(
                Initialize the baseline restoration filter with default parameters.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_window_size",
            &BaseLineRestoration::window_size,
            R"pbdoc(
                int: Size of the sliding window used for baseline estimation.
            )pbdoc"
        )
        .def(
            "_cpp_process",
            &BaseLineRestoration::process,
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

    py::class_<ButterworthLowPassFilter, BaseCircuit>(module, "ButterworthLowPassFilter")
        .def(py::init<>())
        .def(py::init<double, double, int, double>(),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"pbdoc(
                Initialize the Butterworth filter.

                Parameters
                ----------
                sampling_rate : float
                    Sampling rate of the input signal in Hz.
                cutoff_frequency : float
                    Cutoff frequency of the filter in Hz.
                order : int
                    Filter order. Higher values yield steeper roll-off.
                gain : float
                    Gain factor applied to the output.
            )pbdoc")
        .def_readwrite(
            "_cpp_sampling_rate",
            &ButterworthLowPassFilter::sampling_rate,
            R"pbdoc(
                float: Sampling rate in Hz.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_cutoff_frequency",
            &ButterworthLowPassFilter::cutoff_frequency,
            R"pbdoc(
                float: Cutoff frequency in Hz.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_order",
            &ButterworthLowPassFilter::order,
            R"pbdoc(
                int: Order of the filter.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_gain",
            &ButterworthLowPassFilter::gain,
            R"pbdoc(
                float: Output gain factor.
            )pbdoc"
        )
        .def(
            "_cpp_process",
            &ButterworthLowPassFilter::process,
            R"pbdoc(
                Apply the Butterworth filter to the input signal.

                Returns
                -------
                None
            )pbdoc"
        )
        .def("__repr__", [](const ButterworthLowPassFilter &self) {
            return "<ButterworthLowPassFilter sampling_rate=" + std::to_string(self.sampling_rate) +
                   ", cutoff_frequency=" + std::to_string(self.cutoff_frequency) +
                   ", order=" + std::to_string(self.order) +
                   ", gain=" + std::to_string(self.gain) + ">";
        });

    py::class_<BesselLowPassFilter, BaseCircuit>(module, "BesselLowPassFilter")
        .def(py::init<>())
        .def(py::init<double, double, int, double>(),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"pbdoc(
                Initialize the Bessel filter.

                Parameters
                ----------
                sampling_rate : float
                    Sampling rate of the input signal in Hz.
                cutoff_frequency : float
                    Cutoff frequency of the filter in Hz.
                order : int
                    Filter order. Affects sharpness of transition band.
                gain : float
                    Gain factor applied to the output.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_sampling_rate",
            &BesselLowPassFilter::sampling_rate,
            R"pbdoc(
                float: Sampling rate in Hz.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_cutoff_frequency",
            &BesselLowPassFilter::cutoff_frequency,
            R"pbdoc(
                float: Cutoff frequency in Hz.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_order",
            &BesselLowPassFilter::order,
            R"pbdoc(
                int: Order of the filter.
            )pbdoc"
        )
        .def_readwrite(
            "_cpp_gain",
            &BesselLowPassFilter::gain,
            R"pbdoc(
                float: Output gain factor.
            )pbdoc"
        )
        .def(
            "_cpp_process",
            &BesselLowPassFilter::process,
            R"pbdoc(
                Apply the Bessel filter to the input signal.

                Returns
                -------
                None
            )pbdoc"
        )
        .def("__repr__", [](const BesselLowPassFilter &self) {
            return "<BesselLowPassFilter sampling_rate=" + std::to_string(self.sampling_rate) +
                   ", cutoff_frequency=" + std::to_string(self.cutoff_frequency) +
                   ", order=" + std::to_string(self.order) +
                   ", gain=" + std::to_string(self.gain) + ">";
        });
}
