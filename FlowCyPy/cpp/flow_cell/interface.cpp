#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "flow_cell.h"


PYBIND11_MODULE(interface_flow_cell, module) {

    pybind11::class_<FluidRegion>(module, "FLUIDREGION")
        .def_readwrite("_cpp_width", &FluidRegion::width)
        .def_readwrite("_cpp_height", &FluidRegion::height)
        .def_readwrite("_cpp_volume_flow", &FluidRegion::volume_flow)
        .def_readwrite("_cpp_area", &FluidRegion::area)
        .def_readwrite("_cpp_max_flow_speed", &FluidRegion::max_flow_speed)
        .def_readwrite("_cpp_average_flow_speed", &FluidRegion::average_flow_speed)
        ;

    pybind11::class_<FlowCell>(module, "FLOWCELL")
        .def(
            pybind11::init<double, double, double, double, double, int, int>(),
            pybind11::arg("width"),
            pybind11::arg("height"),
            pybind11::arg("sample_volume_flow"),
            pybind11::arg("sheath_volume_flow"),
            pybind11::arg("viscosity"),
            pybind11::arg("N_terms") = 25,
            pybind11::arg("n_int") = 200,
            R"pbdoc(
                Initialize a FlowCell with specified parameters.

                Parameters
                ----------
                width : float
                    Width of the flow cell in meters.
                height : float
                    Height of the flow cell in meters.
                sample_volume_flow : float
                    Volume flow rate of the sample in m^3/s.
                sheath_volume_flow : float
                    Volume flow rate of the sheath fluid in m^3/s.
                viscosity : float
                    Viscosity of the fluid in Pa.s.
                N_terms : int, optional
                    Number of terms for series expansion (default is 25).
                n_int : int, optional
                    Number of integration points (default is 200).
            )pbdoc"
        )
        .def_readonly("_cpp_sample",
            &FlowCell::sample,
            R"pbdoc(
                Sample fluid region of the flow cell.
                This region represents the sample area with its dimensions, volume flow rate,
                maximum flow speed, and average flow speed.
            )pbdoc"
        )
        .def_readonly("_cpp_sheath",
            &FlowCell::sheath,
            R"pbdoc(
                Sheath fluid region of the flow cell.
                This region represents the sheath area with its dimensions, volume flow rate,
                maximum flow speed, and average flow speed.
            )pbdoc"
        )
        .def_readonly("_cpp_dpdx_ref",
            &FlowCell::dpdx_ref,
            R"pbdoc(
                Reference pressure gradient for the flow cell.
                This value is used to compute the local pressure gradient based on the total flow rate.
            )pbdoc"
        )
        .def_readonly("_cpp_Q_total",
            &FlowCell::Q_total,
            R"pbdoc(
                Total volumetric flow rate in the flow cell.
                This is the sum of the sample and sheath volume flow rates.
            )pbdoc"
        )
        .def_readonly("_cpp_u_center",
            &FlowCell::u_center,
            R"pbdoc(
                Centerline velocity of the flow cell.
                This is the velocity at the center of the flow cell, calculated based on the flow rates and dimensions.
            )pbdoc"
        )
        .def("_cpp_sample_transverse_profile",
            &FlowCell::sample_transverse_profile,
            pybind11::arg("n_samples"),
            R"pbdoc(
                Sample the transverse velocity profile of the flow cell.
                This method generates a list of tuples representing the transverse profile
                of the flow cell, where each tuple contains the y-coordinate, z-coordinate,
                and the corresponding velocity at that point.
                The coordinates are sampled uniformly within the flow cell's dimensions.
                The velocity is calculated based on the flow cell's parameters and the
                transverse position within the flow cell. The method returns a vector of tuples,
                where each tuple contains the y-coordinate, z-coordinate, and velocity at that point.
                The number of samples is specified by the `n_samples` parameter.
                The returned vector contains `n_samples` tuples, each representing a point in the transverse profile
                of the flow cell, with the y and z coordinates in meters and the velocity in m/s.

                Parameters
                ----------
                n_samples : int
                    Number of samples to generate for the transverse profile.

                Returns
                -------
                Tuple[List[float], List[float], List[float]]
                    A list of tuples, each containing the y-coordinate, z-coordinate, and velocity at that
                    point in the transverse profile of the flow cell.
            )pbdoc"
        )
        .def("_cpp_get_velocity",
            &FlowCell::get_velocity,
            pybind11::arg("y"),
            pybind11::arg("z"),
            pybind11::arg("dpdx_local"),
            R"pbdoc(
                Computes the local axial velocity \( u(y, z) \) at the point (y, z) in a rectangular microchannel
                using the analytical Fourier series solution for pressure-driven flow.

                The velocity profile is derived from solving the Stokes equation under the assumption of fully developed,
                incompressible, laminar flow with no-slip boundary conditions. The series solution is expressed as:

                .. math::

                u(y, z) = \frac{16 b^2}{\pi^3 \mu} \left( -\frac{dp}{dx} \right)
                \sum_{n=1,3,5,\ldots}^{\infty}
                \frac{1}{n^3}
                \left[
                    1 - \frac{
                        \cosh\left( \frac{n \pi y}{2b} \right)
                    }{
                        \cosh\left( \frac{n \pi a}{2b} \right)
                    }
                \right]
                \sin\left( \frac{n \pi (z + b)}{2b} \right)

                where:

                - \( a \) is half the channel width (in the y-direction)
                - \( b \) is half the channel height (in the z-direction)
                - \( \mu \) is the dynamic viscosity
                - \( \frac{dp}{dx} \) is the axial pressure gradient
                - \( n \) iterates over odd integers

                Parameters
                ----------
                y : float
                    Lateral (width-wise) position in meters.
                z : float
                    Vertical (height-wise) position in meters.
                dpdx_local : float
                    Pressure gradient (Pa/m) used for the computation.

                Returns
                -------
                float
                    Local axial velocity (in m/s) at the given (y, z) position.
            )pbdoc"
        )
    .def("_cpp_compute_channel_flow",
        &FlowCell::compute_channel_flow,
        pybind11::arg("dpdx_input"),
        R"pbdoc(
            Numerically compute the total volumetric flow rate in the channel for a given pressure gradient.

            The volumetric flow rate is defined as:

            .. math::

            Q = \int_{-b}^{b}\int_{-a}^{a} u(y,z) \, dy \, dz

            where :math:`u(y,z)` is the local velocity computed from the Fourier series solution.

            Parameters
            ----------
            dpdx : float
                Pressure gradient (Pa/m).
            n_int : int
                Number of grid points per dimension for integration.

            Returns
            -------
            Q : float
                Total volumetric flow rate (m³/s).
        )pbdoc"
    )
    ;
}
