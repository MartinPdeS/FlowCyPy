#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "circuits.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_circuits, module) {
    module.doc() = "FlowCyPy C++ Circuit Interface";

    py::class_<BaseCircuit>(module, "BaseCircuit")
        .def("process", &BaseCircuit::process, "Process the signal generator");

    py::class_<BaseLineRestoration, BaseCircuit>(module, "BaseLineRestoration")
        .def(py::init<>(), "Initialize with window size")
        .def_readwrite(
            "_cpp_window_size",
            &BaseLineRestoration::window_size,
            "Size of the window for baseline restoration"
        )
        .def(
            "_cpp_process",
            &BaseLineRestoration::process,
            "Process the signal generator for baseline restoration"
        )
        .def("__repr__", [](const BaseLineRestoration &self) {
            return "<BaseLineRestoration window_size=" + std::to_string(self.window_size) + ">";
        })
    ;


    py::class_<ButterworthLowPassFilter, BaseCircuit>(module, "ButterworthLowPassFilter")
        .def(
            py::init<>(),
            "Default constructor for ButterworthLowPassFilter"
        )
        .def(
            py::init<double, double, int, double>(),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Initialize with sampling rate, cutoff frequency, order, and gain"
        )
        .def_readwrite(
            "_cpp_sampling_rate",
            &ButterworthLowPassFilter::sampling_rate,
            "Sampling rate for the Butterworth filter"
        )
        .def_readwrite(
            "_cpp_cutoff_frequency",
            &ButterworthLowPassFilter::cutoff_frequency,
            "Cutoff frequency for the Butterworth filter"
        )
        .def_readwrite(
            "_cpp_order",
            &ButterworthLowPassFilter::order,
            "Order of the Butterworth filter"
        )
        .def_readwrite(
            "_cpp_gain",
            &ButterworthLowPassFilter::gain,
            "Gain factor for the Butterworth filter"
        )
        .def(
            "_cpp_process",
            &ButterworthLowPassFilter::process,
            "Process the signal generator with the Butterworth low-pass filter"
        )
        .def("__repr__", [](const ButterworthLowPassFilter &self) {
            return "<ButterworthLowPassFilter sampling_rate=" + std::to_string(self.sampling_rate) +
                   ", cutoff_frequency=" + std::to_string(self.cutoff_frequency) +
                   ", order=" + std::to_string(self.order) +
                   ", gain=" + std::to_string(self.gain) + ">";
        })
    ;

    py::class_<BesselLowPassFilter, BaseCircuit>(module, "BesselLowPassFilter")
        .def(
            py::init<>(),
            "Default constructor for BesselLowPassFilter"
        )
        .def(
            py::init<double, double, int, double>(),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Initialize with sampling rate, cutoff frequency, order, and gain"
        )
        .def_readwrite(
            "_cpp_sampling_rate",
            &BesselLowPassFilter::sampling_rate,
            "Sampling rate for the Bessel filter"
        )
        .def_readwrite(
            "_cpp_cutoff_frequency",
            &BesselLowPassFilter::cutoff_frequency,
            "Cutoff frequency for the Bessel filter"
        )
        .def_readwrite(
            "_cpp_order",
            &BesselLowPassFilter::order,
            "Order of the Bessel filter"
        )
        .def_readwrite(
            "_cpp_gain",
            &BesselLowPassFilter::gain,
            "Gain factor for the Bessel filter"
        )
        .def(
            "_cpp_process",
            &BesselLowPassFilter::process,
            "Process the signal generator with the Bessel low-pass filter"
        )
        .def("__repr__", [](const BesselLowPassFilter &self) {
            return "<BesselLowPassFilter sampling_rate=" + std::to_string(self.sampling_rate) +
                   ", cutoff_frequency=" + std::to_string(self.cutoff_frequency) +
                   ", order=" + std::to_string(self.order) +
                   ", gain=" + std::to_string(self.gain) + ">";
        })
    ;
}
