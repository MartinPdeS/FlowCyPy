#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;


class Dummy {
public:
    py::buffer array;

    Dummy(){
        // py::array a = py::array();
    }

};

PYBIND11_MODULE(interface_dummy, module) {
    module.doc() = "Module for efficient signal processing and triggered acquisition using C++";

    py::class_<Dummy>(module, "Dummy")
        .def(py::init<>())
        ;
}
