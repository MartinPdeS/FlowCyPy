import matplotlib.pyplot as plt
import numpy as np
from MPSPlots import helper
from TypedUnit import ureg

from FlowCyPy import FlowCytometer, circuits, peak_locator
from FlowCyPy.population import Sphere
from FlowCyPy.triggering_system import DynamicWindow


class SignalStatistics:
    """
    Compute robust and standard statistics from an event signal array.
    """

    def __init__(self, data):
        self.data = data
        self.median = np.median(data)
        self.perc84 = np.percentile(data, 84.13)
        self.perc15 = np.percentile(data, 15.87)
        self.mean = np.mean(data)
        self.std = np.std(data)
        self.robust_std = (self.perc84 - self.perc15) / 2.0
        self.coefficient_of_variation = (
            self.std / self.median if self.median != 0 else np.nan
        )
        self.robust_coefficient_of_variation = (
            self.robust_std / self.median if self.median != 0 else np.nan
        )

    def as_dict(self):
        return {
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "cv": self.cv,
            "robust_std": self.robust_std,
            "robust_cv": self.robust_cv,
        }


class BaseEstimator:
    def _get_peaks(self, flow_cytometer):
        flow_cytometer.signal_processing.analog_processing = [
            circuits.BaselineRestorator(window_size=10 * ureg.microsecond),
        ]

        flow_cytometer.signal_processing.triggering_system = DynamicWindow(
            trigger_detector_name="default",
            threshold=0.5 * ureg.millivolt,
            max_triggers=-1,
            pre_buffer=20,
            post_buffer=20,
        )

        flow_cytometer.signal_processing.peak_algorithm = (
            peak_locator.GlobalPeakLocator(compute_width=False)
        )

        results = flow_cytometer.run(
            run_time=1.5 * ureg.millisecond, compute_cross_section=True
        )

        if self.debug_mode:
            results.trigger.plot()

        return results.peaks


class JEstimator(BaseEstimator):
    """
    Class for estimating the J parameter that characterizes the relationship between signal variability
    (RCV: Robust Coefficient of Variation) and signal strength (Median) across varying illumination powers.


    Notes
    -----
    To estimate J we need to measure the RCV and the Median Signal at different illumination powers.


    The relationship follows:
        RCV ≈ J / sqrt(Median Signal)

    Parameters
    ----------
    debug_mode : bool, optional
        If True, detailed internal computation information is printed.
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self._medians = []
        self._robust_stds = []
        self._robust_cvs = []
        self._illumination_powers = []

    def add_measurement(
        self, signal_array: np.ndarray, illumination_power: ureg.Quantity
    ) -> None:
        """
        Add a single signal measurement and compute its statistics.

        Parameters
        ----------
        signal_array : np.ndarray
            Raw signal values in arbitrary ureg.
        illumination_power : ureg.Quantity
            Illumination power associated with this signal.
        """
        stats = SignalStatistics(signal_array)

        self._medians.append(stats.median)
        self._robust_stds.append(stats.robust_std)
        self._robust_cvs.append(stats.robust_coefficient_of_variation)
        self._illumination_powers.append(illumination_power)

        if self.debug_mode:
            print(f"[DEBUG] Illumination Power: {illumination_power}")
            print(f"[DEBUG] Median: {stats.median:.3e} AU")
            print(f"[DEBUG] Robust STD: {stats.robust_std:.3e} AU")
            print(f"[DEBUG] Robust CV: {stats.robust_coefficient_of_variation:.5f}")

    def add_batch(
        self,
        particle_count,
        bead_diameter: ureg.Quantity,
        illumination_powers: ureg.Quantity,
        flow_cytometer: FlowCytometer,
    ) -> None:
        """
        Add multiple signal measurements across a range of illumination powers using a provided generator.

        Parameters
        ----------
        bead_diameter : ureg.Quantity
            Bead size used in the experiment (for `run_function`).
        illumination_powers : ureg.Quantity
            Sequence of illumination powers to test.
        run_function : callable
            Function that accepts bead_diameter and illumination_power, and returns a signal peak dataframe.
        """
        for idx, power in enumerate(illumination_powers):
            print(f"[INFO] Running simulation {idx+1}/{len(illumination_powers)}")

            result_df = self._run_experiment(
                flow_cytometer=flow_cytometer,
                bead_diameter=bead_diameter,
                illumination_power=power,
                particle_count=particle_count,
            )

            signal_array = result_df["Height"].values.astype(float)
            self.add_measurement(signal_array, power)

    def _run_experiment(
        self,
        flow_cytometer: FlowCytometer,
        bead_diameter,
        illumination_power,
        particle_count,
    ):
        population_0 = Sphere(
            name="population",
            particle_count=particle_count,
            diameter=bead_diameter,
            refractive_index=1.47 * ureg.RIU,
        )

        flow_cytometer.fluidics.scatterer_collection.populations = [population_0]

        flow_cytometer.opto_electronics.source.optical_power = illumination_power

        return self._get_peaks(flow_cytometer)

    def estimate_j(self) -> ureg.Quantity:
        """
        Estimate the J parameter by performing a linear fit of RCV vs 1/sqrt(Median).

        Returns
        -------
        j_estimate : ureg.Quantity
            Estimated slope J in √AU ureg.
        """
        assert (
            len(self._medians) >= 2
        ), "At least two measurements are required to estimate J."

        x = 1 / np.sqrt(np.array(self._medians))
        y = np.array(self._robust_cvs)

        slope, _ = np.polyfit(x, y, 1)

        if self.debug_mode:
            for i, (xi, yi) in enumerate(zip(x, y)):
                print(f"[DEBUG] x={xi:.3e}, y={yi:.3e}")
            print(f"[DEBUG] Estimated J = {slope:.5f} √AU")

        return slope * ureg.AU**0.5

    @helper.pre_plot(nrows=1, ncols=1)
    def plot(self, axes: plt.Axes) -> None:
        """
        Plot RCV vs 1/sqrt(Median) with linear fit (J estimation).
        This is the main plot representing the J-scaling behavior.
        """
        if len(self._medians) < 2:
            raise ValueError("At least two measurements are required to plot.")

        x = 1 / np.sqrt(np.array(self._medians))
        y = np.array(self._robust_cvs)
        slope, intercept = np.polyfit(x, y, 1)
        x_fit = np.linspace(min(x), max(x), 200)
        y_fit = slope * x_fit + intercept

        axes.scatter(x, y, label="Measured RCV", zorder=3)
        axes.plot(
            x_fit,
            y_fit,
            "--",
            label=rf"$RCV = {slope:.3e} \cdot x + {intercept:.3e}$",
            zorder=2,
        )
        axes.set(
            xlabel=r"$1 / \sqrt{\mathrm{Median\ Signal}}$",
            ylabel="Robust CV",
            title="J Parameter Estimation",
        )
        axes.legend()

    @helper.pre_plot(nrows=2, ncols=1)
    def plot_statistics(self, axes: plt.Axes) -> None:
        """
        Plot:
        1. Median vs Illumination Power
        2. Robust STD vs Illumination Power with √(Median) fit
        """
        assert (
            len(self._medians) >= 2
        ), "At least two measurements are required to plot statistics."

        powers = np.array(
            [float(p.to("mW").magnitude) for p in self._illumination_powers]
        )
        medians = np.array(self._medians)
        stds = np.array(self._robust_stds)

        # Median vs Illumination
        axes[0].plot(powers, medians, "o-", color="C0", label="Median")
        axes[0].set(
            xlabel="Illumination Power [mW]",
            ylabel="Median [AU]",
            title="Median Signal vs Illumination Power",
        )
        axes[0].legend()

        # STD vs Illumination + sqrt(Median) fit
        sqrt_medians = np.sqrt(medians)
        coeffs = np.polyfit(sqrt_medians, stds, 1)
        std_fit = coeffs[0] * sqrt_medians + coeffs[1]

        axes[1].plot(powers, stds, "o", color="C1", label="Robust STD")
        axes[1].plot(
            powers,
            std_fit,
            "--",
            color="C1",
            label=rf"$STD = {coeffs[0]:.2e} \cdot \sqrt{{M}} + {coeffs[1]:.2e}$",
        )
        axes[1].set(
            xlabel="Illumination Power [mW]",
            ylabel="Robust STD [AU]",
            title="STD vs Illumination Power",
        )
        axes[1].legend()


class KEstimator(BaseEstimator):
    """
    Estimate the K parameter characterizing how Robust STD scales with sqrt(Median Signal),
    across varying bead diameters under fixed illumination power.

    The expected relationship is:
        Robust STD ≈ K * sqrt(Median)

    Parameters
    ----------
    debug_mode : bool, optional
        If True, prints internal computation info.
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self._medians = []
        self._robust_stds = []
        self._bead_diameters = []

    def add_measurement(
        self, signal_array: np.ndarray, bead_diameter: ureg.Quantity
    ) -> None:
        """
        Add a measurement corresponding to a single bead size.

        Parameters
        ----------
        signal_array : np.ndarray
            Measured peak signal array (AU).
        bead_diameter : ureg.Quantity
            Diameter of the simulated bead.
        """
        stats = SignalStatistics(signal_array)

        self._medians.append(stats.median)
        self._robust_stds.append(stats.robust_std)
        self._bead_diameters.append(bead_diameter)

        if self.debug_mode:
            print(f"[DEBUG] Bead diameter: {bead_diameter}")
            print(f"[DEBUG] Median: {stats.median:.3e} AU")
            print(f"[DEBUG] Robust STD: {stats.robust_std:.3e} AU")

    def add_batch(
        self,
        particle_count: int,
        bead_diameters: list[ureg.Quantity],
        illumination_power: ureg.Quantity,
        flow_cytometer: FlowCytometer,
    ) -> None:
        """
        Add multiple measurements for different bead sizes at a fixed illumination power.

        Parameters
        ----------
        particle_count : int
            Number of particles per bead population.
        bead_diameters : list of ureg.Quantity
            List of bead sizes to simulate.
        illumination_power : ureg.Quantity
            Constant power for all simulations.
        flow_cytometer : FlowCytometer
            Simulation engine.
        """
        for idx, diameter in enumerate(bead_diameters):
            print(f"[INFO] Simulating bead {idx+1}/{len(bead_diameters)}: {diameter}")
            peaks = self._run_experiment(
                flow_cytometer, diameter, illumination_power, particle_count
            )
            signal_array = peaks["Height"].values.astype(float)
            self.add_measurement(signal_array, diameter)

    def _run_experiment(
        self, flow_cytometer, bead_diameter, illumination_power, particle_count
    ):
        population = Sphere(
            name="population",
            particle_count=particle_count,
            diameter=bead_diameter,
            refractive_index=1.47 * ureg.RIU,
        )
        flow_cytometer.fluidics.scatterer_collection.populations = [population]
        flow_cytometer.opto_electronics.source.optical_power = illumination_power

        return self._get_peaks(flow_cytometer)

    def estimate_k(self) -> ureg.Quantity:
        """
        Estimate the K parameter from a linear fit of STD vs sqrt(Median).

        Returns
        -------
        k_estimate : ureg.Quantity
            Estimated K in AU^0.5
        """
        if len(self._medians) < 2:
            raise ValueError("At least two measurements are required to estimate K.")

        x = np.sqrt(np.array(self._medians))
        y = np.array(self._robust_stds)
        slope, _ = np.polyfit(x, y, 1)

        if self.debug_mode:
            for xi, yi in zip(x, y):
                print(f"[DEBUG] sqrt(Median): {xi:.3e}, STD: {yi:.3e}")
            print(f"[DEBUG] Estimated K = {slope:.5f} AU^0.5")

        return slope * ureg.AU**0.5

    @helper.pre_plot(nrows=1, ncols=1)
    def plot(self, axes: plt.Axes) -> None:
        """
        Plot STD vs sqrt(Median) with linear fit (K estimation).
        """
        assert (
            len(self._medians) >= 2
        ), "At least two measurements are required to plot."

        x = np.sqrt(np.array(self._medians))
        y = np.array(self._robust_stds)
        slope, intercept = np.polyfit(x, y, 1)
        x_fit = np.linspace(min(x), max(x), 200)
        y_fit = slope * x_fit + intercept

        axes.scatter(x, y, label="Measured STD", zorder=3)
        axes.plot(
            x_fit,
            y_fit,
            "--",
            label=rf"$STD = {slope:.3e} \cdot \sqrt{{M}} + {intercept:.3e}$",
            zorder=2,
        )
        axes.set(
            xlabel=r"$\sqrt{\mathrm{Median\ Signal}}$",
            ylabel="Robust STD",
            title="K Parameter Estimation",
        )
        axes.legend()

    @helper.pre_plot(nrows=2, ncols=1)
    def plot_statistics(self, axes: plt.Axes) -> None:
        """
        Plot Median and STD vs Bead Diameter.
        """
        assert (
            len(self._medians) >= 2
        ), "At least two measurements are required to plot statistics."

        diameters = [float(d.to("micrometer").magnitude) for d in self._bead_diameters]
        medians = np.array(self._medians)
        stds = np.array(self._robust_stds)

        axes[0].plot(diameters, medians, "o-", color="C0", label="Median")
        axes[0].set(
            xlabel="Bead Diameter [µm]",
            ylabel="Median [AU]",
            title="Median vs Bead Diameter",
        )
        axes[0].legend()

        axes[1].plot(diameters, stds, "o-", color="C1", label="Robust STD")
        axes[1].set(
            xlabel="Bead Diameter [µm]",
            ylabel="Robust STD [AU]",
            title="STD vs Bead Diameter",
        )
        axes[1].legend()
