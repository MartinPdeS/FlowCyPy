#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "flow_cell.h"
#include <pint/pint.h>
#include <utils/numpy.h>


PYBIND11_MODULE(flow_cell, module) {

    py::object ureg = get_shared_ureg();

    pybind11::class_<FluidRegion, std::shared_ptr<FluidRegion>>(module, "FluidRegion")
        .def_property_readonly(
            "width",
            [ureg](const FluidRegion& self){

                py::object output = py::float_(self.width) * ureg.attr("meter");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the width of the flow.
            )pbdoc"
        )
        .def_property_readonly(
            "height",
            [ureg](const FluidRegion& self){

                py::object output = py::float_(self.height) * ureg.attr("meter");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the height of the flow.
            )pbdoc"
        )
        .def_property_readonly(
            "volume_flow",
            [ureg](const FluidRegion& self){

                py::object output = py::float_(self.volume_flow) * ureg.attr("meter**3/second");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the volume flow.
            )pbdoc"
        )
        .def_property_readonly(
            "area",
            [ureg](const FluidRegion& self){

                py::object output = py::float_(self.height * self.width) * ureg.attr("meter**2");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the area of the flow.
            )pbdoc"
        )
        .def_property_readonly(
            "average_flow_speed",
            [ureg](const FluidRegion& self){

                py::object output = py::float_(self.average_flow_speed) * ureg.attr("meter/second");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the area of the flow.
            )pbdoc"
        )
        .def_property_readonly(
            "max_flow_speed",
            [ureg](const FluidRegion& self){

                py::object output = py::float_(self.max_flow_speed) * ureg.attr("meter/second");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the area of the flow.
            )pbdoc"
        )
        ;

    pybind11::class_<FlowCell, std::shared_ptr<FlowCell>>(module, "FlowCell")
        .def(
            py::init(
                    [ureg](
                    const py::object &width,
                    const py::object &height,
                    const py::object &sample_volume_flow,
                    const py::object &sheath_volume_flow,
                    const py::object &viscosity,
                    const size_t &N_terms,
                    const size_t &n_int
                ) {
                    py::object Length = py::module_::import("FlowCyPy.units").attr("Length");
                    py::object FlowRate = py::module_::import("FlowCyPy.units").attr("FlowRate");
                    py::object Viscosity = py::module_::import("FlowCyPy.units").attr("Viscosity");

                    Length.attr("check")(width);
                    Length.attr("check")(height);

                    FlowRate.attr("check")(sample_volume_flow);
                    FlowRate.attr("check")(sheath_volume_flow);

                    Viscosity.attr("check")(viscosity);

                    double _width = width.attr("to")(ureg.attr("meter")).attr("magnitude").cast<double>();
                    double _height = height.attr("to")(ureg.attr("meter")).attr("magnitude").cast<double>();

                    double _sample_volume_flow = sample_volume_flow.attr("to")(ureg.attr("meter**3/second")).attr("magnitude").cast<double>();
                    double _sheath_volume_flow = sheath_volume_flow.attr("to")(ureg.attr("meter**3/second")).attr("magnitude").cast<double>();

                    double _viscosity = viscosity.attr("to")(ureg.attr("pascal*second")).attr("magnitude").cast<double>();

                    return std::make_shared<FlowCell>(
                        _height,
                        _width,
                        _sample_volume_flow,
                        _sheath_volume_flow,
                        _viscosity,
                        N_terms,
                        n_int
                    );
                }
            ),
            pybind11::arg("width"),
            pybind11::arg("height"),
            pybind11::arg("sample_volume_flow"),
            pybind11::arg("sheath_volume_flow"),
            pybind11::arg("viscosity") = py::float_(1e-3) * ureg.attr("pascal*second"),
            pybind11::arg("N_terms") = 25,
            pybind11::arg("n_int") = 200,
            R"pbdoc(
                Represents a rectangular flow cell in which the velocity field is computed from an
                analytical Fourier series solution for pressure-driven flow. The focused sample region
                is estimated from the volumetric flow rates of the sample and sheath fluids.

                The analytical solution for the x-direction velocity in a rectangular channel is given by:

                .. math::

                u(y,z) = \frac{16b^2}{\pi^3 \mu}\left(-\frac{dp}{dx}\right)
                        \sum_{\substack{n=1,3,5,\ldots}}^{\infty} \frac{1}{n^3}
                        \left[
                            1 - \frac{
                                    \cosh\left(\frac{n\pi y}{2b}\right)
                                }{
                                    \cosh\left(\frac{n\pi a}{2b}\right)
                                }
                        \right]
                \sin\left(\frac{n\pi (z+b)}{2b}\right)

                where:

                - :math:`a` is the half-width of the channel (in the y-direction),
                - :math:`b` is the half-height of the channel (in the z-direction),
                - :math:`mu` is the dynamic viscosity,
                - :math:`dp/dx` is the pressure gradient driving the flow,
                - the summation is over odd integers (i.e. :math:`n = 1, 3, 5, ...`).

                The derivation of this solution is based on the method of separation of variables and
                eigenfunction expansion applied to the Poisson equation for fully developed laminar flow.
                The validity of this approach and the resulting solution for rectangular ducts is well documented
                in classical fluid mechanics texts.

                **References**

                - Shah, R.K. & London, A.L. (1978). *Laminar Flow in Ducts*. Academic Press.
                - White, F.M. (2006). *Viscous Fluid Flow* (3rd ed.). McGraw-Hill.
                - Happel, J. & Brenner, H. (1983). *Low Reynolds Number Hydrodynamics*. Martinus Nijhoff.
                - Di Carlo, D. (2009). "Inertial Microfluidics," *Lab on a Chip*, 9, 3038-3046.

                In flow cytometry, hydrodynamic focusing is used to narrow the sample stream for optimal optical interrogation.
                The same theoretical framework for rectangular duct flow is applied to these microfluidic devices.

                Parameters
                ----------
                width : Length
                    Width of the channel in the y-direction (m).
                height : Length
                    Height of the channel in the z-direction (m).
                mu : Quantity
                    Dynamic viscosity of the fluid (Pa·s).
                sample_volume_flow : FlowRate
                    Volumetric flow rate of the sample fluid (m³/s).
                sheath_volume_flow : FlowRate
                    Volumetric flow rate of the sheath fluid (m³/s).
                N_terms : int, optional
                    Number of odd terms to use in the Fourier series solution (default: 25).
                n_int : int, optional
                    Number of grid points for numerical integration over the channel cross-section (default: 200).

                Attributes
                ----------
                Q_total : Quantity
                    Total volumetric flow rate (m³/s).
                dpdx : float
                    Computed pressure gradient (Pa/m) driving the flow.
                u_center : float
                    Centerline velocity, i.e. u(0,0) (m/s).
                width_sample : Quantity
                    Width of the focused sample region (m).
                height_sample : Quantity
                    Height of the focused sample region (m).
                event_scheme : str
                    Scheme for event sampling, 'uniform-random', 'sorted', 'poisson', 'preserve' (default: 'preserve').
            )pbdoc"
        )
        .def_property_readonly("width",
            [ureg](const FlowCell& self){

                py::object output = py::float_(self.width) * ureg.attr("meter");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the width of the flowcell.
            )pbdoc"
        )
        .def_property_readonly("height",
            [ureg](const FlowCell& self){

                py::object output = py::float_(self.height) * ureg.attr("meter");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the height of the flowcell.
            )pbdoc"
        )
        .def_property_readonly("area",
            [ureg](const FlowCell& self){

                py::object output = py::float_(self.area) * ureg.attr("meter**2");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the area of the flowcell.
            )pbdoc"
        )
        .def("get_sample_volume",
            [ureg](const FlowCell& self, const py::object &run_time){
                py::object output = py::float_(self.area * self.sample.average_flow_speed) * ureg.attr("meter**3 / second");

                output = output * run_time;
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Computes the volume passing through the flow cell over the given run time.
            )pbdoc"
        )
        .def_readonly("sample",
            &FlowCell::sample,
            R"pbdoc(
                Sample fluid region of the flow cell.
                This region represents the sample area with its dimensions, volume flow rate,
                maximum flow speed, and average flow speed.
            )pbdoc"
        )
        .def_readonly("sheath",
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
        .def("sample_transverse_profile",
            [ureg](const FlowCell& self, const size_t n_samples)
            {
                    auto [y, z, velocities] = self.sample_transverse_profile(n_samples);

                    size_t n_elements = y.size();
                    std::vector<size_t> shape = {n_elements};


                    py::object _y = vector_move_from_numpy(y, shape) * ureg.attr("meter");
                    py::object _z = vector_move_from_numpy(z, shape) * ureg.attr("meter");
                    py::object _velocities = vector_move_from_numpy(velocities, shape) * ureg.attr("meter/second");

                    return py::make_tuple(_y, _z, _velocities);
            },
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
    .def("sample_arrival_times",
        [ureg](const FlowCell& self, const size_t n_events, const py::object &run_time) {
            double _run_time = run_time.attr("to")("second").attr("magnitude").cast<double>();

            auto arrival_times = self.sample_arrival_times_(n_events, _run_time);

            size_t n_elements = arrival_times.size();
            std::vector<size_t> shape = {n_elements};

            py::object output = vector_move_from_numpy(arrival_times, shape) * ureg.attr("second");
            return output;
        },
        pybind11::arg("n_events"),
        pybind11::arg("run_time"),
        R"pbdoc(
            Sample the arrival times of particles in the flow cell based on the specified run time and particle flux.

            This method computes the expected arrival times of particles in the flow cell based on the
            total flow rate, dimensions, and specified particle flux. It returns a vector of arrival times
            for particles that would be present in the flow cell during the specified run time.

            Parameters
            ----------
            run_time : float
                Total run time for which to sample arrival times (in seconds).
            particle_flux : float
                Particle flux (particles per second) used to compute expected arrival times.

            Returns
            -------
            List[float]
                A list of arrival times for particles in seconds.
        )pbdoc"
    )
    ;
}
