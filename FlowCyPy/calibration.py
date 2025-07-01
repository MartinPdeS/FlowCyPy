from typing import Tuple, List, Dict

import numpy as np
from FlowCyPy import units
from PyMieSim import experiment
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from pydantic.dataclasses import dataclass

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
        self.coefficient_of_variation = self.std / self.median if self.median != 0 else np.nan
        self.robust_coefficient_of_variation = self.robust_std / self.median if self.median != 0 else np.nan

    def as_dict(self):
        return {
            'mean': self.mean,
            'median': self.median,
            'std': self.std,
            'cv': self.cv,
            'robust_std': self.robust_std,
            'robust_cv': self.robust_cv
        }


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)




@dataclass(config=config_dict)
class CalibrationRecord:
    illumination_power: units.Quantity
    bead_diameter: units.Quantity

    signal_median: units.Quantity = 0.0
    rcv: units.Quantity = 0.0
    csca: units.Quantity = 0.0
    background_median: units.Quantity = 0.0



class CalibrationResults:
    def __init__(self):
        self._records: Dict[Tuple[float, float], CalibrationRecord] = {}

    def set(self, illumination_power: float, bead_diameter: float, **kwargs):
        key = (illumination_power, bead_diameter)
        if key not in self._records:
            self._records[key] = CalibrationRecord(illumination_power.to(units.milliwatt), bead_diameter.to(units.nanometer))
        for k, v in kwargs.items():
            setattr(self._records[key], k, v)

    def get(self, illumination_power: float, bead_diameter: float) -> CalibrationRecord:
        return self._records[(illumination_power, bead_diameter)]

    def select_by_diameter(self, diameter: units.Quantity) -> List[CalibrationRecord]:
        return [rec for (p, d), rec in self._records.items() if d.to(units.nanometer).magnitude == diameter.to(units.nanometer).magnitude]

    def select_by_power(self, power: units.Quantity) -> List[CalibrationRecord]:
        return [rec for (p, d), rec in self._records.items() if p.to(units.milliwatt).magnitude == power.to(units.milliwatt).magnitude]

    def all(self) -> List[CalibrationRecord]:
        return list(self._records.values())

    def __repr__(self) -> str:
        lines = [
            f"<CalibrationResults: {len(self._records)} records>",
            "  IlluminationPower  BeadDiameter   SignalMedian     rCV       Csca      Background"
        ]
        for i, ((power, diameter), rec) in enumerate(self._records.items()):
            if i >= 5:
                lines.append("  ...")
                break
            lines.append(
                f"  {power:>16.1f}  {diameter:>12.1f}  "
                f"{getattr(rec, 'signal_median', float('nan')):>13.3f}  "
                f"{getattr(rec, 'robust_cv', float('nan')):>7.3f}  "
                f"{getattr(rec, 'csca', float('nan')):>9.1f}  "
                f"{getattr(rec, 'background_median', float('nan')):>11.1f}"
            )
        return "\n".join(lines)


class Calibration:
    def __init__(self,
        illumination_powers: units.Quantity,
        bead_diameters: units.Quantity,
        gain: units.Quantity,
        detection_efficiency: units.Quantity,
        background_level: units.Quantity,
        number_of_background_events: units.Quantity,
        number_of_bead_events: units.Quantity):
        """
        Initialize the calibration with parameters.

        Parameters
        ----------
        illumination_powers : units.Quantity
            Array of illumination powers in milliwatts.
        bead_diameters : units.Quantity
            Array of bead diameters in nanometers.
        gain : units.Quantity
            Gain in arbitrary units per photoelectron.
        detection_efficiency : units.Quantity
            Detection efficiency in photoelectrons per nm² at 20 mW.
        background_level : units.Quantity
            Background level in nm².
        number_of_background_events : units.Quantity
            Number of background events to simulate.
        number_of_bead_events : units.Quantity
            Number of bead events to simulate.

        """
        self.illumination_powers = illumination_powers
        self.bead_diameters = bead_diameters
        self.gain = gain
        self.detection_efficiency = detection_efficiency
        self.background_level = background_level
        self.number_of_background_events = number_of_background_events
        self.number_of_bead_events = number_of_bead_events
        self.results = CalibrationResults()

    def get_poisson_distribution(self, mean: units.Quantity, n_element: units.Quantity) -> np.ndarray:
        """
        Generate a Poisson distribution based on the mean and number of elements.
        Parameters
        ----------
        mean : units.Quantity
            Mean of the Poisson distribution in arbitrary units.
        n_element : units.Quantity
            Number of elements to simulate, in events.
        Returns
        -------
        np.ndarray
            Array of simulated events based on the Poisson distribution.
        """
        return np.random.poisson(mean.magnitude, int(n_element.to('event').magnitude)) * mean.units

    def add_background(self):
        for power in self.illumination_powers:
            scaled_eff = self.detection_efficiency * (power / (20 * units.milliwatt))
            mean_bg = self.gain * scaled_eff * self.background_level
            samples = self.get_poisson_distribution(mean_bg, self.number_of_background_events)
            median = np.median(samples).item()

            for diameter in self.bead_diameters:
                self.results.set(power, diameter, background_median=median)

    def add_beads(self, wavelength, refractive_index, medium_refractive_index):
        source = experiment.source.Gaussian(
            NA=0.3 * units.RIU,
            wavelength=wavelength,
            polarization=0 * units.degree,
            optical_power=5 * units.milliwatt
        )
        sphere = experiment.scatterer.Sphere(
            diameter=self.bead_diameters,
            medium_property=medium_refractive_index,
            property=refractive_index,
            source=source
        )
        setup = experiment.setup.Setup(source=source, scatterer=sphere)
        csca_values = setup.get('Csca', as_numpy=True) * units.meter**2

        for diameter, csca in zip(self.bead_diameters, csca_values):
            for power in self.illumination_powers:
                self.results.set(power, diameter, csca=csca)

    def simulate_signals(self, debug_mode: bool = False):
        """
        Simulate the signals for each combination of illumination power and bead diameter.
        Includes detailed debug output at each step to trace internal computations.
        """
        self.add_background()

        for power in self.illumination_powers:

            # Scale detection efficiency to current power
            scaled_eff = self.detection_efficiency * (power / (20 * units.milliwatt))

            mean_background = self.gain * scaled_eff * self.background_level

            if debug_mode:
                print("-------------")
                print(f"\n  [DEBUG] Illumination Power: {power}")
                print(f"  [DEBUG] Scaled Detection Efficiency: {scaled_eff:.2~P}")
                print(f"  [DEBUG] Mean Background (no Csca): {mean_background:.2~P}")

            background_and_beads_samples = self.get_poisson_distribution(mean_background, self.number_of_bead_events)

            for diameter in self.bead_diameters:

                record = self.results.get(power, diameter)

                mean_signal = (self.gain * scaled_eff * record.csca).to('dimensionless')

                signal_samples = self.get_poisson_distribution(mean_signal, self.number_of_bead_events)

                total_signal = signal_samples.to('dimensionless') + background_and_beads_samples.to('dimensionless')

                corrected = total_signal - record.background_median

                stats = SignalStatistics(corrected)

                if debug_mode:
                    print(f"\n  [DEBUG] Bead Diameter: {diameter}")
                    print(f"  [DEBUG] Mean Particle Signal (Csca scaled): {mean_signal:.2~P}")
                    print(f"  [DEBUG] Median(corrected signal): {stats.median:.2f}")
                    print(f"  [DEBUG] Background median: {record.background_median:.2f}")
                    print(f"  [DEBUG] Robust CV: {stats.robust_coefficient_of_variation:.4f}")

                self.results.set(power, diameter, signal_median=stats.median, rcv=stats.robust_coefficient_of_variation)

    def regression_for_J(self, diameter: units.Quantity) -> Tuple[float, np.ndarray, np.ndarray]:
        records = self.results.select_by_diameter(diameter)
        x = np.array([1 / np.sqrt(r.signal_median) for r in records])
        y = np.array([r.rcv for r in records])

        slope = np.polyfit(x, y, 1)[0] * (1 * units.AU)**0.5

        return slope, x, y

    def regression_for_K(self, power: units.Quantity) -> Tuple[float, np.ndarray, np.ndarray]:
        records = self.results.select_by_power(power)
        x = np.array([r.signal_median.to('dimensionless').magnitude for r in records])
        y = np.array([r.csca.to('nanometer**2').magnitude for r in records])

        slope = np.polyfit(x, y, 1)[0] * units.nanometer**2 / units.AU

        return slope, x, y

    def plot_J(self, bead_diameters: List[float]):
        with plt.style.context(mps):
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_xlabel('1 / sqrt(Median signal)')
            ax.set_ylabel('Robust CV')
            for idx, d in enumerate(bead_diameters):
                slope, x, y = self.regression_for_J(d)
                x_fit = np.linspace(min(x), max(x), 100)
                ax.scatter(x, y, label=f"{d} nm | J = {slope:.3f}", color=f"C{idx}")
                ax.plot(x_fit, slope * x_fit, color=f"C{idx}")
            ax.legend()
            plt.tight_layout()
            plt.show()

    def plot_K(self, illumination_powers: List[float]):
        with plt.style.context(mps):
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_xlabel('Median signal (AU)')
            ax.set_ylabel('Scattering cross-section (nm²)')
            for idx, p in enumerate(illumination_powers):
                slope, x, y = self.regression_for_K(p)
                x_fit = np.linspace(min(x), max(x), 100)
                ax.scatter(x, y, label=f"{p} mW | K = {slope:.1f}", color=f"C{idx}")
                ax.plot(x_fit, slope * x_fit, color=f"C{idx}")
            ax.legend()
            plt.tight_layout()
            plt.show()

class JKEstimator:
    def __init__(self):
        self._records: Dict[units.Quantity, List[Dict]] = {}

    def add_beads_signal(self, diameter: units.Quantity, signal_array: np.ndarray, csca: units.Quantity = None):
        """
        Add a raw signal array for a given bead diameter. Computes median and RCV internally.
        """
        stats = SignalStatistics(signal_array)
        if diameter not in self._records:
            self._records[diameter] = []

        self._records[diameter].append({
            'signal': stats.median,
            'rcv': stats.robust_coefficient_of_variation,
            'csca': csca.to('nanometer**2').magnitude if csca else None
        })

    def estimate_J(self, diameter: units.Quantity) -> units.Quantity:
        records = self._records.get(diameter, [])
        if not records:
            raise ValueError(f"No records for diameter {diameter}")
        x = np.array([1 / np.sqrt(r['signal']) for r in records])
        y = np.array([r['rcv'] for r in records])
        slope = np.polyfit(x, y, 1)[0]
        return slope * (units.AU)**0.5

    def estimate_K(self, diameter: units.Quantity) -> units.Quantity:
        records = [r for r in self._records.get(diameter, []) if r['csca'] is not None]
        if not records:
            raise ValueError(f"No Csca data for diameter {diameter}")
        x = np.array([r['signal'] for r in records])
        y = np.array([r['csca'] for r in records])
        slope = np.polyfit(x, y, 1)[0]
        return slope * units.nanometer**2 / units.AU

    def plot_J(self, diameter: units.Quantity):
        """
        Plot RCV vs 1/sqrt(signal) and linear regression fit for given diameter.
        """
        records = self._records.get(diameter, [])
        if not records:
            raise ValueError(f"No records for diameter {diameter}")

        x = np.array([1 / np.sqrt(r['signal']) for r in records])
        y = np.array([r['rcv'] for r in records])
        slope = np.polyfit(x, y, 1)[0]
        x_fit = np.linspace(min(x), max(x), 100)

        plt.figure(figsize=(8, 5))
        plt.scatter(x, y, label="Measured points")
        plt.plot(x_fit, slope * x_fit, '--', label=f"Fit: J = {slope:.3f} √AU")
        plt.xlabel(r"$1 / \sqrt{\mathrm{Median\ Signal}}$")
        plt.ylabel("Robust CV")
        plt.title(f"J Estimation – Diameter {diameter:~}")
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_K(self, diameter: units.Quantity):
        """
        Plot Csca vs signal and linear regression fit for given diameter.
        """
        records = [r for r in self._records.get(diameter, []) if r['csca'] is not None]
        if not records:
            raise ValueError(f"No Csca records for diameter {diameter}")

        x = np.array([r['signal'] for r in records])
        y = np.array([r['csca'] for r in records])
        slope = np.polyfit(x, y, 1)[0]
        x_fit = np.linspace(min(x), max(x), 100)

        plt.figure(figsize=(8, 5))
        plt.scatter(x, y, label="Measured points")
        plt.plot(x_fit, slope * x_fit, '--', label=f"Fit: K = {slope:.1f} nm²/AU")
        plt.xlabel("Median signal (AU)")
        plt.ylabel("Scattering cross-section (nm²)")
        plt.title(f"K Estimation – Diameter {diameter:~}")
        plt.legend()
        plt.tight_layout()
        plt.show()
