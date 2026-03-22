#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <cmath>
#include <string>
#include <vector>

#include "digitizer.h"
#include <utils/casting.h>
#include <pint/pint.h>

namespace py = pybind11;


PYBIND11_MODULE(digitizer, module) {
    py::object ureg = get_shared_ureg();

    py::class_<Digitizer>(
        module,
        "Digitizer",
        R"pbdoc(
            Digitize and clip voltage signals.

            The ``Digitizer`` class models a digitization stage for voltage signals.
            It can optionally clip the signal to a voltage range and quantize it
            according to a specified bit depth.

            A bit depth of ``0`` disables digitization. In that case, the signal remains
            continuous and only optional clipping is applied.

            The voltage range is defined by ``min_voltage`` and ``max_voltage``.
            If both are unset, clipping is disabled and digitization cannot proceed
            unless a range is inferred automatically.

            The bandwidth is optional. If ``bandwidth`` is not provided, it remains unset
            and is not considered in any computation.

            Automatic range inference can be enabled persistently by setting
            ``use_auto_range=True`` at construction, or temporarily per call with
            the corresponding method argument.

            Parameters
            ----------
            sampling_rate : pint.Quantity
                Sampling rate of the digitizer. Must be compatible with hertz.
            bandwidth : pint.Quantity or None, default=None
                Digitizer bandwidth. Must be compatible with hertz. If ``None``,
                bandwidth remains unset.
            bit_depth : int, default=0
                Number of quantization bits. A value of ``0`` disables digitization.
            min_voltage : pint.Quantity or None, default=None
                Minimum clipping voltage. Must be compatible with volts.
            max_voltage : pint.Quantity or None, default=None
                Maximum clipping voltage. Must be compatible with volts.
            use_auto_range : bool, default=False
                If ``True``, :meth:`process_signal` and :meth:`capture_signal`
                will infer ``min_voltage`` and ``max_voltage`` from the input signal
                when their overload without explicit override is used.

            Attributes
            ----------
            bandwidth : pint.Quantity or None
                Bandwidth of the digitizer, or ``None`` if unset.
            sampling_rate : pint.Quantity
                Sampling rate of the digitizer.
            bit_depth : int
                Number of quantization bits.
            min_voltage : pint.Quantity or None
                Minimum clipping voltage.
            max_voltage : pint.Quantity or None
                Maximum clipping voltage.
            use_auto_range : bool
                Persistent automatic range inference mode.

            Notes
            -----
            Signals are expected to be Pint quantities compatible with volts.

            NaN values are ignored when estimating the signal range and are preserved
            during clipping and digitization.

            Examples
            --------
            Create a digitizer with explicit bandwidth and voltage limits:

            >>> digitizer = Digitizer(
            ...     sampling_rate=100e6 * ureg.hertz,
            ...     bandwidth=20e6 * ureg.hertz,
            ...     bit_depth=12,
            ...     min_voltage=-1.0 * ureg.volt,
            ...     max_voltage=1.0 * ureg.volt,
            ... )

            Create a digitizer with no bandwidth constraint:

            >>> digitizer = Digitizer(
            ...     sampling_rate=100e6 * ureg.hertz,
            ...     bandwidth=None,
            ...     bit_depth=12,
            ... )
            >>> digitizer.bandwidth is None
            True

            Enable persistent automatic range inference:

            >>> digitizer = Digitizer(
            ...     sampling_rate=100e6 * ureg.hertz,
            ...     bit_depth=8,
            ...     use_auto_range=True,
            ... )
            >>> processed = digitizer.process_signal(signal)
        )pbdoc"
    )
        .def(
            py::init([](
                py::object sampling_rate,
                py::object bandwidth,
                size_t bit_depth,
                py::object min_voltage,
                py::object max_voltage,
                bool use_auto_range
            ) {
                const double sampling_rate_value = Casting::cast_py_to_scalar<double>(
                    sampling_rate,
                    "sampling_rate",
                    "hertz"
                );

                const double bandwidth_value = bandwidth.is_none()
                    ? std::numeric_limits<double>::quiet_NaN()
                    : Casting::cast_py_to_scalar<double>(
                        bandwidth,
                        "bandwidth",
                        "hertz"
                    );

                return Digitizer(
                    bandwidth_value,
                    sampling_rate_value,
                    bit_depth,
                    Casting::cast_py_to_optional_scalar<double>(
                        min_voltage,
                        "min_voltage",
                        "volt"
                    ),
                    Casting::cast_py_to_optional_scalar<double>(
                        max_voltage,
                        "max_voltage",
                        "volt"
                    ),
                    use_auto_range
                );
            }),
            py::arg("sampling_rate"),
            py::arg("bandwidth") = py::none(),
            py::arg("bit_depth") = 0,
            py::arg("min_voltage") = py::none(),
            py::arg("max_voltage") = py::none(),
            py::arg("use_auto_range") = false,
            R"pbdoc(
                Initialize a digitizer.

                If ``bandwidth`` is not provided, it remains unset and is not used.

                Parameters
                ----------
                sampling_rate : pint.Quantity
                    Sampling rate in hertz.
                bandwidth : pint.Quantity or None, default=None
                    Digitizer bandwidth in hertz. If ``None``, bandwidth remains unset.
                bit_depth : int, default=0
                    Number of quantization bits. A value of ``0`` disables digitization.
                min_voltage : pint.Quantity or None, default=None
                    Minimum clipping voltage.
                max_voltage : pint.Quantity or None, default=None
                    Maximum clipping voltage.
                use_auto_range : bool, default=False
                    Persistent automatic range inference mode.
            )pbdoc"
        )

        .def(
            "has_bandwidth",
            &Digitizer::has_bandwidth,
            R"pbdoc(
                Return whether the digitizer bandwidth is defined.

                Returns
                -------
                bool
                    ``True`` if bandwidth is set.
            )pbdoc"
        )

        .def_property(
            "bandwidth",
            [ureg](const Digitizer& self) -> py::object {
                if (std::isnan(self.bandwidth)) {
                    return py::none();
                }

                return (py::float_(self.bandwidth) * ureg.attr("hertz")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.bandwidth = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "bandwidth",
                    "hertz"
                );

                if (!std::isnan(self.bandwidth) && self.bandwidth <= 0.0) {
                    throw std::invalid_argument("Digitizer bandwidth must be strictly positive when provided.");
                }
            },
            R"pbdoc(
                Bandwidth of the digitizer.

                Returns
                -------
                pint.Quantity or None
                    Bandwidth in hertz, or ``None`` if unset.
            )pbdoc"
        )

        .def_property(
            "sampling_rate",
            [ureg](const Digitizer& self) -> py::object {
                return (py::float_(self.sampling_rate) * ureg.attr("hertz")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.sampling_rate = Casting::cast_py_to_scalar<double>(
                    value,
                    "sampling_rate",
                    "hertz"
                );

                if (self.sampling_rate <= 0.0) {
                    throw std::invalid_argument("Digitizer sampling_rate must be strictly positive.");
                }
            },
            R"pbdoc(
                Sampling rate of the digitizer.

                Returns
                -------
                pint.Quantity
                    Sampling rate in hertz.
            )pbdoc"
        )

        .def_readwrite(
            "bit_depth",
            &Digitizer::bit_depth,
            R"pbdoc(
                Number of quantization bits.

                A value of ``0`` disables digitization.

                Returns
                -------
                int
                    Quantization bit depth.
            )pbdoc"
        )

        .def_readwrite(
            "use_auto_range",
            &Digitizer::use_auto_range,
            R"pbdoc(
                Persistent automatic range inference mode.

                When ``True``, the overloads of :meth:`process_signal` and
                :meth:`capture_signal` that do not receive an explicit override
                will infer ``min_voltage`` and ``max_voltage`` from the signal
                before proceeding.

                Returns
                -------
                bool
                    Automatic range inference flag.
            )pbdoc"
        )

        .def_property(
            "min_voltage",
            [ureg](const Digitizer& self) -> py::object {
                if (std::isnan(self.min_voltage)) {
                    return py::none();
                }

                return (py::float_(self.min_voltage) * ureg.attr("volt")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.min_voltage = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "min_voltage",
                    "volt"
                );

                if (
                    !std::isnan(self.min_voltage) &&
                    !std::isnan(self.max_voltage) &&
                    self.max_voltage <= self.min_voltage
                ) {
                    throw std::invalid_argument("Digitizer requires max_voltage to be greater than min_voltage.");
                }
            },
            R"pbdoc(
                Minimum clipping voltage.

                Returns
                -------
                pint.Quantity or None
                    Minimum clipping voltage in volts, or ``None`` if unset.
            )pbdoc"
        )

        .def_property(
            "max_voltage",
            [ureg](const Digitizer& self) -> py::object {
                if (std::isnan(self.max_voltage)) {
                    return py::none();
                }

                return (py::float_(self.max_voltage) * ureg.attr("volt")).attr("to_compact")();
            },
            [](Digitizer& self, const py::object& value) {
                self.max_voltage = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "max_voltage",
                    "volt"
                );

                if (
                    !std::isnan(self.min_voltage) &&
                    !std::isnan(self.max_voltage) &&
                    self.max_voltage <= self.min_voltage
                ) {
                    throw std::invalid_argument("Digitizer requires max_voltage to be greater than min_voltage.");
                }
            },
            R"pbdoc(
                Maximum clipping voltage.

                Returns
                -------
                pint.Quantity or None
                    Maximum clipping voltage in volts, or ``None`` if unset.
            )pbdoc"
        )

        .def(
            "has_voltage_range",
            &Digitizer::has_voltage_range,
            R"pbdoc(
                Return whether both clipping bounds are defined.

                Returns
                -------
                bool
                    ``True`` if both ``min_voltage`` and ``max_voltage`` are set.
            )pbdoc"
        )

        .def(
            "should_digitize",
            &Digitizer::should_digitize,
            R"pbdoc(
                Return whether quantization is enabled.

                Returns
                -------
                bool
                    ``True`` if ``bit_depth > 0``.
            )pbdoc"
        )

        .def(
            "clear_bandwidth",
            &Digitizer::clear_bandwidth,
            R"pbdoc(
                Clear the bandwidth setting.

                After calling this method, the bandwidth becomes unset and is not
                considered in any computation.
            )pbdoc"
        )

        .def(
            "clear_voltage_range",
            &Digitizer::clear_voltage_range,
            R"pbdoc(
                Clear the clipping bounds.

                After calling this method, both ``min_voltage`` and ``max_voltage`` are unset.
                Clipping is disabled until a new range is assigned or inferred.
            )pbdoc"
        )

        .def(
            "set_auto_range",
            [](Digitizer& self, const py::object& signal) {
                self.set_auto_range(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Infer the voltage range from a signal.

                The minimum and maximum finite values of the input signal are used
                to update ``min_voltage`` and ``max_voltage``.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.

                Notes
                -----
                NaN values are ignored when estimating the range.
            )pbdoc"
        )

        .def(
            "get_min_max",
            [ureg](const Digitizer& self, const py::object& signal) -> py::object {
                auto [minimum_value, maximum_value] = self.get_min_max(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );

                return py::make_tuple(
                    (py::float_(minimum_value) * ureg.attr("volt")).attr("to_compact")(),
                    (py::float_(maximum_value) * ureg.attr("volt")).attr("to_compact")()
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Return the minimum and maximum finite values of a signal.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.

                Returns
                -------
                tuple of pint.Quantity
                    Minimum and maximum finite values in volts.

                Notes
                -----
                NaN values are ignored. An exception is raised if all values are NaN.
            )pbdoc"
        )

        .def(
            "clip_signal",
            [ureg](const Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector = Casting::cast_py_to_vector<double>(
                    signal,
                    "volt"
                );

                self.clip_signal(signal_vector);

                return py::array_t<double>(signal_vector.size(), signal_vector.data()) * ureg.attr("volt");
            },
            py::arg("signal"),
            R"pbdoc(
                Clip a signal to the configured voltage range.

                If no voltage range is configured, the input signal is returned unchanged.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.

                Returns
                -------
                pint.Quantity
                    Clipped signal values in volts.

                Notes
                -----
                NaN values are preserved.
            )pbdoc"
        )

        .def(
            "digitize_signal",
            [ureg](const Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector = Casting::cast_py_to_vector<double>(
                    signal,
                    "volt"
                );

                self.digitize_signal(signal_vector);

                return py::array_t<double>(signal_vector.size(), signal_vector.data()) * ureg.attr("volt");
            },
            py::arg("signal"),
            R"pbdoc(
                Quantize a signal according to the configured bit depth.

                If ``bit_depth == 0``, the input signal is returned unchanged.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.

                Returns
                -------
                pint.Quantity
                    Quantized signal values in volts.

                Raises
                ------
                RuntimeError
                    If digitization is enabled but the voltage range is not defined.
            )pbdoc"
        )

        .def(
            "process_signal",
            [ureg](Digitizer& self, const py::object& signal) -> py::object {
                std::vector<double> signal_vector = Casting::cast_py_to_vector<double>(
                    signal,
                    "volt"
                );

                self.process_signal(signal_vector);

                return py::array_t<double>(signal_vector.size(), signal_vector.data());
            },
            py::arg("signal"),
            R"pbdoc(
                Process a signal using the persistent ``use_auto_range`` setting.

                If ``use_auto_range`` is enabled on the instance, the voltage range is
                inferred from the signal before clipping and digitization.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.

                Returns
                -------
                pint.Quantity
                    Processed signal values in volts.

                Notes
                -----
                Processing proceeds in this order:

                1. optional automatic range inference
                2. clipping
                3. digitization
            )pbdoc"
        )

        .def(
            "process_signal",
            [ureg](Digitizer& self, const py::object& signal, bool use_auto_range) -> py::object {
                std::vector<double> signal_vector = Casting::cast_py_to_vector<double>(
                    signal,
                    "volt"
                );

                self.process_signal(signal_vector, use_auto_range);

                return py::array_t<double>(signal_vector.size(), signal_vector.data());
            },
            py::arg("signal"),
            py::arg("use_auto_range"),
            R"pbdoc(
                Process a signal with an explicit automatic range inference override.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.
                use_auto_range : bool
                    If ``True``, infer ``min_voltage`` and ``max_voltage`` from the signal
                    before processing, regardless of the instance setting.

                Returns
                -------
                pint.Quantity
                    Processed signal values in volts.

                Notes
                -----
                Processing proceeds in this order:

                1. optional automatic range inference
                2. clipping
                3. digitization
            )pbdoc"
        )

        .def(
            "capture_signal",
            [](Digitizer& self, const py::object& signal) {
                self.capture_signal(
                    Casting::cast_py_to_vector<double>(signal, "volt")
                );
            },
            py::arg("signal"),
            R"pbdoc(
                Update internal range information using the persistent ``use_auto_range`` setting.

                This method does not return a processed signal. It updates internal state only.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.
            )pbdoc"
        )

        .def(
            "capture_signal",
            [](Digitizer& self, const py::object& signal, bool use_auto_range) {
                self.capture_signal(
                    Casting::cast_py_to_vector<double>(signal, "volt"),
                    use_auto_range
                );
            },
            py::arg("signal"),
            py::arg("use_auto_range"),
            R"pbdoc(
                Update internal range information with an explicit automatic range inference override.

                This method does not return a processed signal. It updates internal state only.

                Parameters
                ----------
                signal : pint.Quantity
                    Input voltage signal.
                use_auto_range : bool
                    If ``True``, infer ``min_voltage`` and ``max_voltage`` from the signal.
            )pbdoc"
        )

        .def(
            "get_time_series",
            [ureg](const Digitizer& self, const py::object& run_time) -> py::object {
                std::vector<double> time_series = self.get_time_series(
                    Casting::cast_py_to_scalar<double>(
                        run_time,
                        "run_time",
                        "second"
                    )
                );

                return py::array_t<double>(time_series.size(), time_series.data()) * ureg.attr("second");
            },
            py::arg("run_time"),
            R"pbdoc(
                Return the sampling time axis for a given acquisition duration.

                Parameters
                ----------
                run_time : pint.Quantity
                    Acquisition duration. Must be compatible with seconds.

                Returns
                -------
                pint.Quantity
                    Time axis in seconds.

                Notes
                -----
                The returned sequence is generated as:

                ``index / sampling_rate`` for ``index`` in ``[0, sample_count)``

                where ``sample_count = floor(sampling_rate * run_time)``.
            )pbdoc"
        )

        .def(
            "__repr__",
            [](const Digitizer& self) {
                return
                    "Digitizer("
                    "bandwidth=" + (
                        std::isnan(self.bandwidth) ? std::string("None") : std::to_string(self.bandwidth)
                    ) +
                    ", sampling_rate=" + std::to_string(self.sampling_rate) +
                    ", bit_depth=" + std::to_string(self.bit_depth) +
                    ", min_voltage=" + (
                        std::isnan(self.min_voltage) ? std::string("None") : std::to_string(self.min_voltage)
                    ) +
                    ", max_voltage=" + (
                        std::isnan(self.max_voltage) ? std::string("None") : std::to_string(self.max_voltage)
                    ) +
                    ", use_auto_range=" + std::string(self.use_auto_range ? "True" : "False") +
                    ")";
            },
            R"pbdoc(
                Return a string representation of the digitizer.
            )pbdoc"
        );
}
