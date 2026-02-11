#include <pybind11/pybind11.h>
#include <source/source.h>
#include <pint/pint.h>

void register_source(pybind11::module& module) {
    py::object ureg = get_shared_ureg();

    pybind11::class_<BaseSource, std::shared_ptr<BaseSource>>(module, "BaseSource")
    .def_property_readonly(
        "frequency",
        &BaseSource::get_frequency
    )
    .def_property_readonly(
        "photon_energy",
        &BaseSource::get_photon_energy
    )
    .def_property_readonly(
        "rin_linear",
        &BaseSource::get_rin_linear
    )
    .def(
        "add_rin_to_signal",
        &BaseSource::add_rin_to_signal,
        pybind11::arg("amplitudes"),
        pybind11::arg("bandwidth")
    )
    ;

    pybind11::class_<Gaussian, std::shared_ptr<Gaussian>>(module, "Gaussian")
    .def_readonly(
        "waist",
        &Gaussian::waist,
        R"doc(
            The beam waist in meters.
        )doc"
    )
    .def(
        "set_waist",
        &Gaussian::set_waist,
        pybind11::arg("waist"),
        R"doc(
            Set the beam waist directly.

            Parameters
            ----------
            waist : float
                The beam waist in meters.
        )doc"
    )
    .def(
        "set_numerical_apreture",
        &Gaussian::set_numerical_apreture,
        pybind11::arg("numerical_aperture"),
        R"doc(
            Set the beam waist from the numerical aperture.

            Parameters
            ----------
            numerical_aperture : float
                The numerical aperture (NA) of the beam.
        )doc"
    )
    ;

    pybind11::class_<AsymetricGaussian, std::shared_ptr<AsymetricGaussian>>(module, "AsymetricGaussian")
    .def_readonly(
        "waist_y",
        &AsymetricGaussian::waist_y,
        R"doc(
            The beam waist along the Y axis in meters.
        )doc"
    )
    .def_readonly(
        "waist_z",
        &AsymetricGaussian::waist_z,
        R"doc(
            The beam waist along the Z axis in meters.
        )doc"
    )
    .def(
        "set_waist",
        &AsymetricGaussian::set_waist,
        // [ureg]
        pybind11::arg("waist_y"),
        pybind11::arg("waist_z"),
        R"doc(
            Set the beam waists directly.
            Parameters
            ----------
            waist_y : float
                The beam waist along the Y axis in meters.
            waist_z : float
                The beam waist along the Z axis in meters.
        )doc"
    )
    .def(
        "set_numerical_apreture",
        &AsymetricGaussian::set_numerical_apreture,
        pybind11::arg("numerical_aperture_y"),
        pybind11::arg("numerical_aperture_z"),
        R"doc(
            Set the beam waists from the numerical apertures.
            Parameters
            ----------
            numerical_aperture_y : float
                The numerical aperture (NA) of the beam along the Y axis.
            numerical_aperture_z : float
                The numerical aperture (NA) of the beam along the Z axis.
        )doc"
    )
    ;
}
