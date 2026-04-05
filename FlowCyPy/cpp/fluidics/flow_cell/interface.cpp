#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "flow_cell.h"
#include <pint/pint.h>
#include <utils/numpy.h>

namespace py = pybind11;

PYBIND11_MODULE(flow_cell, module) {

    py::object ureg = get_shared_ureg();

    py::class_<FluidRegion, std::shared_ptr<FluidRegion>>(module, "FluidRegion")
        .def_property_readonly(
            "width",
            [ureg](const FluidRegion& self){
                py::object output = py::float_(self.width) * ureg.attr("meter");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the width of the flow region.
            )pbdoc"
        )
        .def_property_readonly(
            "height",
            [ureg](const FluidRegion& self){
                py::object output = py::float_(self.height) * ureg.attr("meter");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the height of the flow region.
            )pbdoc"
        )
        .def_property_readonly(
            "volume_flow",
            [ureg](const FluidRegion& self){
                py::object output = py::float_(self.volume_flow) * ureg.attr("meter**3/second");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the volumetric flow rate of the region.
            )pbdoc"
        )
        .def_property_readonly(
            "area",
            [ureg](const FluidRegion& self){
                py::object output = py::float_(self.area) * ureg.attr("meter**2");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the cross sectional area of the region.
            )pbdoc"
        )
        .def_property_readonly(
            "average_flow_speed",
            [ureg](const FluidRegion& self){
                py::object output = py::float_(self.average_flow_speed) * ureg.attr("meter/second");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the average axial flow speed in the region.
            )pbdoc"
        )
        .def_property_readonly(
            "max_flow_speed",
            [ureg](const FluidRegion& self){
                py::object output = py::float_(self.max_flow_speed) * ureg.attr("meter/second");
                return output.attr("to_compact")();
            },
            R"pbdoc(
                Return the maximum axial flow speed in the region.
            )pbdoc"
        );

    py::class_<FlowCell, std::shared_ptr<FlowCell>>(
        module,
        "FlowCell",
        R"pbdoc(
            Represents a rectangular flow cell in which the velocity field is computed from an
            analytical Fourier series solution for pressure driven flow. The focused sample region
            is estimated from the volumetric flow rates of the sample and sheath fluids.

            The analytical solution for the x direction velocity in a rectangular channel is given by:

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

        )pbdoc"
    )
    .def(
        py::init(

            [ureg](
                const py::object& width,
                const py::object& height,
                const py::object& sample_volume_flow,
                const py::object& sheath_volume_flow,
                const py::object& viscosity,
                const size_t& N_terms,
                const size_t& n_int,
                const std::string& event_scheme,
                const bool perfectly_aligned
            ) {
                py::object Length = py::module_::import("FlowCyPy.units").attr("Length");
                py::object FlowRate = py::module_::import("FlowCyPy.units").attr("FlowRate");
                py::object Viscosity = py::module_::import("FlowCyPy.units").attr("Viscosity");

                Length.attr("check")(width);
                Length.attr("check")(height);

                FlowRate.attr("check")(sample_volume_flow);
                FlowRate.attr("check")(sheath_volume_flow);

                Viscosity.attr("check")(viscosity);

                const double _width = width.attr("to")(ureg.attr("meter")).attr("magnitude").cast<double>();
                const double _height = height.attr("to")(ureg.attr("meter")).attr("magnitude").cast<double>();

                const double _sample_volume_flow =
                    sample_volume_flow.attr("to")(ureg.attr("meter**3/second")).attr("magnitude").cast<double>();

                const double _sheath_volume_flow =
                    sheath_volume_flow.attr("to")(ureg.attr("meter**3/second")).attr("magnitude").cast<double>();

                const double _viscosity =
                    viscosity.attr("to")(ureg.attr("pascal*second")).attr("magnitude").cast<double>();

                return std::make_shared<FlowCell>(
                    _width,
                    _height,
                    _sample_volume_flow,
                    _sheath_volume_flow,
                    _viscosity,
                    static_cast<int>(N_terms),
                    static_cast<int>(n_int),
                    event_scheme,
                    perfectly_aligned
                );
            }
        ),
        py::arg("width"),
        py::arg("height"),
        py::arg("sample_volume_flow"),
        py::arg("sheath_volume_flow"),
        py::arg("viscosity") = py::float_(1e-3) * ureg.attr("pascal*second"),
        py::arg("N_terms") = 25,
        py::arg("n_int") = 200,
        py::arg("event_scheme") = "uniform-random",
        py::arg("perfectly_aligned") = false,
        R"pbdoc(
            Parameters
            ----------
            width : Length
                Width of the channel in the y-direction.
            height : Length
                Height of the channel in the z-direction.
            sample_volume_flow : FlowRate
                Volumetric flow rate of the sample fluid.
            sheath_volume_flow : FlowRate
                Volumetric flow rate of the sheath fluid.
            viscosity : Viscosity
                Dynamic viscosity of the fluid.
            N_terms : int, optional
                Number of odd terms to use in the Fourier series solution.
            n_int : int, optional
                Number of grid points per axis for numerical integration.
            event_scheme : str, optional
                Default event sampling scheme. Must be one of
                ``"uniform-random"``, ``"linear"``, or ``"poisson"``.
            perfectly_aligned : bool, optional
                If True, the sample stream is perfectly aligned with the centerline.
                Default is False.
        )pbdoc"
    )
    .def_property_readonly(
        "width",
        [ureg](const FlowCell& self){
            py::object output = py::float_(self.width) * ureg.attr("meter");
            return output.attr("to_compact")();
        },
        R"pbdoc(
            Return the width of the flow cell.
        )pbdoc"
    )
    .def_property_readonly(
        "height",
        [ureg](const FlowCell& self){
            py::object output = py::float_(self.height) * ureg.attr("meter");
            return output.attr("to_compact")();
        },
        R"pbdoc(
            Return the height of the flow cell.
        )pbdoc"
    )
    .def_property_readonly(
        "area",
        [ureg](const FlowCell& self){
            py::object output = py::float_(self.area) * ureg.attr("meter**2");
            return output.attr("to_compact")();
        },
        R"pbdoc(
            Return the cross sectional area of the flow cell.
        )pbdoc"
    )
    .def_property_readonly(
        "event_scheme",
        [](const FlowCell& self){
            return self.event_scheme;
        },
        R"pbdoc(
            Return the default event sampling scheme used by the flow cell.
        )pbdoc"
    )
    .def(
        "get_sample_volume",
        [ureg](const FlowCell& self, const py::object& run_time){
            py::object output = py::float_(self.sample.volume_flow) * ureg.attr("meter**3/second");
            output = output * run_time;
            return output.attr("to_compact")();
        },
        py::arg("run_time"),
        R"pbdoc(
            Compute the sample volume that passes through the flow cell during the specified run time.

            Parameters
            ----------
            run_time : Time
                Total run duration.

            Returns
            -------
            Quantity
                Sample volume transported during the run.
        )pbdoc"
    )
    .def_readonly(
        "sample",
        &FlowCell::sample,
        R"pbdoc(
            Sample fluid region of the flow cell.
            This region represents the focused sample area with its dimensions, volume flow rate,
            maximum flow speed, and average flow speed.
        )pbdoc"
    )
    .def_readonly(
        "sheath",
        &FlowCell::sheath,
        R"pbdoc(
            Sheath fluid region of the flow cell.
            This region represents the remaining sheath area with its dimensions, volume flow rate,
            maximum flow speed, and average flow speed.
        )pbdoc"
    )
    .def_readonly(
        "_cpp_dpdx_ref",
        &FlowCell::dpdx_ref,
        R"pbdoc(
            Reference pressure gradient used to calibrate the flow field.
        )pbdoc"
    )
    .def_readonly(
        "_cpp_Q_total",
        &FlowCell::Q_total,
        R"pbdoc(
            Total volumetric flow rate in the flow cell.
            This is the sum of the sample and sheath flow rates.
        )pbdoc"
    )
    .def_readonly(
        "_cpp_u_center",
        &FlowCell::u_center,
        R"pbdoc(
            Centerline velocity of the flow cell.
            This corresponds to the local velocity at y = 0 and z = 0.
        )pbdoc"
    )
    .def(
        "sample_transverse_profile",
        [ureg](const FlowCell& self, const size_t n_samples)
        {
            auto [y, z, velocities] = self.sample_transverse_profile(static_cast<int>(n_samples));

            const size_t n_elements = y.size();
            std::vector<size_t> shape = {n_elements};

            py::object _y = vector_move_from_numpy(y, shape) * ureg.attr("meter");
            py::object _z = vector_move_from_numpy(z, shape) * ureg.attr("meter");
            py::object _velocities = vector_move_from_numpy(velocities, shape) * ureg.attr("meter/second");

            return py::make_tuple(_y, _z, _velocities);
        },
        py::arg("n_samples"),
        R"pbdoc(
            Sample the transverse velocity profile of the focused sample region.

            This method draws random transverse coordinates within the sample region and
            evaluates the corresponding local axial velocity in the channel.

            Parameters
            ----------
            n_samples : int
                Number of transverse samples to generate.

            Returns
            -------
            tuple
                Tuple containing:

                - y coordinates
                - z coordinates
                - local axial velocities
        )pbdoc"
    )
    .def(
        "_cpp_get_velocity",
        &FlowCell::get_velocity,
        py::arg("y"),
        py::arg("z"),
        py::arg("dpdx_local"),
        R"pbdoc(
            Compute the local axial velocity :math:`u(y, z)` at the point :math:`(y, z)` in a rectangular channel
            using the analytical Fourier series solution for pressure-driven flow.

            The velocity profile is derived from solving the Stokes equation under the assumption of fully developed,
            incompressible, laminar flow with no-slip boundary conditions.

            Parameters
            ----------
            y : float
                Lateral position in meters.
            z : float
                Vertical position in meters.
            dpdx_local : float
                Pressure gradient in Pa/m used for the computation.

            Returns
            -------
            float
                Local axial velocity in m/s.
        )pbdoc"
    )
    .def(
        "_cpp_compute_channel_flow",
        &FlowCell::compute_channel_flow,
        py::arg("dpdx_input"),
        R"pbdoc(
            Numerically compute the total volumetric flow rate in the channel for a given pressure gradient.

            The volumetric flow rate is defined as the integral of the local velocity field over the
            rectangular channel cross section.

            Parameters
            ----------
            dpdx_input : float
                Pressure gradient in Pa/m.

            Returns
            -------
            float
                Total volumetric flow rate in m^3/s.
        )pbdoc"
    )
    .def(
        "sample_arrival_times",
        [ureg](
            const FlowCell& self,
            const std::size_t n_events,
            const py::object& run_time,
            const double particle_flux
        ) {
            const double _run_time =
                run_time.attr("to")(ureg.attr("second")).attr("magnitude").cast<double>();

            auto arrival_times = self.sample_arrival_times(
                n_events,
                _run_time,
                particle_flux
            );

            const size_t n_elements = arrival_times.size();
            std::vector<size_t> shape = {n_elements};

            py::object output = vector_move_from_numpy(arrival_times, shape) * ureg.attr("second");
            return output;
        },
        py::arg("n_events"),
        py::arg("run_time"),
        py::arg("particle_flux") = 0.0,
        R"pbdoc(
            Sample event arrival times over a specified run duration using the flow cell's configured event scheme.

            Configured schemes
            ------------------
            ``"uniform-random"``
                Draw ``n_events`` random times uniformly over the run duration and sort them.

            ``"linear"``
                Generate ``n_events`` linearly spaced times over the run duration.
                This is particularly useful for debugging and deterministic tests.

            ``"poisson"``
                Generate arrival times from a Poisson process with rate ``particle_flux``.
                In this mode, ``n_events`` is ignored and the number of returned events is stochastic.

            Parameters
            ----------
            n_events : int
                Number of events to generate for deterministic schemes.
            run_time : Time
                Total duration over which events are sampled.
            particle_flux : float, optional
                Event rate in events per second used only when ``event_scheme="poisson"``.

            Returns
            -------
            Quantity
                Event arrival times expressed in seconds.
        )pbdoc"
    );
}
