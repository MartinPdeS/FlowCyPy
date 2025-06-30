from typing import Tuple, List

import numpy as np
import pandas as pd
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
class Calibration:
    """
    Calibration class for simulating and analyzing scattering-based signal acquisition in flow cytometry.

    This class models how the median detected signal and its variability depend on physical and optical parameters.
    It reproduces a typical calibration protocol used in cytometry by simulating both background and signal events
    using Poisson statistics. Calibration coefficients (J, K) can then be extracted via linear regression.

    Attributes
    ----------
    illumination_powers : units.Quantity [milliwatt]
        List of illumination powers used in the experiment. Each entry corresponds to a distinct optical power level.

    bead_diameters : units.Quantity [nanometer]
        List of bead diameters used to simulate scattering. Each value corresponds to a spherical particle.

    gain : units.Quantity [AU / photoelectron]
        Amplification factor converting photon-generated signal into arbitrary units. Models electronic gain.

    detection_efficiency : units.Quantity [photoelectron / (nm^2 at 20 mW)]
        Conversion efficiency from scattering cross section to detected signal. This value is scaled by illumination power.

    background_level : units.Quantity [nm^2]
        Effective background scattering cross section. Treated as an equivalent signal-generating surface area.

    number_of_background_events : units.Quantity [event]
        Number of acquisition events to simulate for both signal and background.

    dataframe : pd.DataFrame
        Stores computed median signal, robust coefficient of variation, background, and theoretical Csca values
        for each (IlluminationPower, BeadDiameter) pair.
    """

    illumination_powers: units.Quantity
    gain: units.Quantity
    detection_efficiency: units.Quantity
    background_level: units.Quantity
    number_of_background_events: units.Quantity
    number_of_bead_events: units.Quantity


    def _initialize_dataframe(self) -> pd.DataFrame:
        """
        Create and return an empty DataFrame indexed by (IlluminationPower, BeadDiameter).

        Columns:
            - SignalMedian: Corrected median signal for each condition.
            - rCV: Robust coefficient of variation.
            - Csca: Theoretical scattering cross section (nm²).
            - BackGroundMedian: Median background signal (simulated).
        """
        index = pd.MultiIndex.from_product(
            [self.illumination_powers.to('milliwatt').magnitude, self.bead_diameters.to('nanometer').magnitude],
            names=['IlluminationPower', 'BeadDiameter']
        )
        df = pd.DataFrame(index=index, columns=['SignalMedian', 'rCV', 'Csca', 'BackGroundMedian']).astype(float)

        # Populate the DataFrame with background events
        df = df.unstack('BeadDiameter')
        for idx, power in enumerate(self.illumination_powers):
            df.loc[power.to('milliwatt').magnitude] = self.background_events[idx].to(units.milliwatt).magnitude

        df = df.stack('BeadDiameter', future_stack=True).reset_index().set_index(['IlluminationPower', 'BeadDiameter'])

        # Add theoretical scattering cross section (Csca) for each bead diameter
        df = df.unstack('IlluminationPower')

        for diameter, csca in zip(self.bead_diameters, self.csca_values):
            df.loc[diameter.to('nanometer').magnitude, 'Csca'] = csca.to('nanometer**2').magnitude

        df = df.stack('IlluminationPower', future_stack=True).reset_index().set_index(['IlluminationPower', 'BeadDiameter'])

        self.dataframe = df

    def _add_background(self) -> None:
        """
        Simulate background-only events and populate the 'BackGroundMedian' column of the dataframe.

        Background signal is modeled as:
            mean_background = gain * detection_efficiency * (P / 20 mW) * background_level

        For each illumination power, the median of N Poisson-distributed background events is calculated.
        """
        self.background_events = []
        for power in self.illumination_powers:
            Q = self.detection_efficiency * (power / 20)
            mean_background = self.gain * Q * self.background_level

            background_event = self.get_poisson_distribution(mean_background, self.number_of_background_events)

            background_median = np.median(background_event).to(units.milliwatt).magnitude
            self.background_events.append(background_median)

        self.background_events = np.array(self.background_events) * units.milliwatt

    def _add_beads(self, diameters: units.Quantity, wavelength: units.Quantity, refractive_index: units.Quantity, medium_refractive_index: units.Quantity) -> None:
        """
        Compute and insert the theoretical scattering cross section (Csca) for each bead diameter.

        Uses PyMieSim to simulate light scattering from a Gaussian beam on spherical beads in a defined medium.
        Scattering cross section is expressed in nm² and stored for each (IlluminationPower, BeadDiameter) pair.

        Parameters
        ----------
        wavelength : units.Quantity [nanometer]
            Illumination wavelength used for Mie simulation.
        refractive_index : units.Quantity [RIU]
            Refractive index of the beads.
        medium_refractive_index : units.Quantity [RIU]
            Refractive index of the surrounding medium (e.g., water).
        """
        self.bead_diameters = diameters

        source = experiment.source.Gaussian(
            NA=0.3 * units.RIU,
            wavelength=wavelength,
            polarization=0 * units.degree,
            optical_power=5 * units.milliwatt
        )
        sphere = experiment.scatterer.Sphere(
            diameter=diameters,
            medium_property=medium_refractive_index,
            property=refractive_index,
            source=source
        )
        setup = experiment.setup.Setup(source=source, scatterer=sphere)
        self.csca_values = setup.get('Csca', as_numpy=True) * units.meter**2

    def get_poisson_distribution(self, mean: units.Quantity, n_element: units.Quantity) -> np.ndarray:
        """
        Generate Poisson-distributed samples with the given mean and sample count.

        Parameters
        ----------
        mean : units.Quantity
            Expected value of the distribution. Must be unit-compatible.

        n_element : units.Quantity
            Number of samples to draw. Must be in units of 'event'.

        Returns
        -------
        np.ndarray
            Sampled events with units matching `mean`.
        """
        return np.random.poisson(mean.magnitude, n_element.to('event').magnitude) * mean.units

    def _simulate_signals(self) -> None:
        """
        Simulate full signal acquisition for each (Power, Diameter) pair.

        For each pair:
            1. Compute expected particle signal from Csca.
            2. Simulate Poisson-distributed particle + background signal.
            3. Subtract median background.
            4. Store median signal and robust CV.
        """
        self._initialize_dataframe()

        scaled_efficiency = self.detection_efficiency

        for power in self.illumination_powers:

            scaled_efficiency = scaled_efficiency * (power / (20 * units.milliwatt))

            background_mean = self.gain * scaled_efficiency * self.background_level

            for diameter in self.bead_diameters:
                idx = (power.to('milliwatt').magnitude, diameter.to('nanometer').magnitude)
                csca = self.dataframe.loc[idx, 'Csca'] * units.nanometer**2
                particle_mean = self.gain * scaled_efficiency * csca

                particle_events = self.get_poisson_distribution(particle_mean, self.number_of_bead_events)
                background_events = self.get_poisson_distribution(background_mean, self.number_of_bead_events)

                total = particle_events + background_events

                corrected = total - self.dataframe.loc[idx, 'BackGroundMedian']
                stats = SignalStatistics(corrected)

                self.dataframe.loc[idx, 'SignalMedian'] = stats.median
                self.dataframe.loc[idx, 'rCV'] = stats.robust_coefficient_of_variation.magnitude


    def regression_for_J(self, diameter) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Perform regression of rCV vs 1/sqrt(median signal) for a fixed bead diameter.

        Returns
        -------
        slope : float
            Calibration slope J (precision metric).
        x : np.ndarray
            1/sqrt(SignalMedian).
        y : np.ndarray
            rCV values.
        """
        subset = self.dataframe.xs(diameter, level='BeadDiameter')


        x = 1 / np.sqrt(subset['SignalMedian'].values)
        y = subset['rCV'].values
        slope = np.polyfit(x, y, 1)[0]
        return slope, x, y

    def regression_for_K(self, power) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Perform regression of scattering cross section (Csca) vs SignalMedian for a fixed illumination power.

        Returns
        -------
        slope : float
            Calibration slope K (conversion factor).
        x : np.ndarray
            SignalMedian values.
        y : np.ndarray
            Csca values.
        """
        subset = self.dataframe.loc[power]
        x = subset['SignalMedian'].values
        y = subset['Csca'].values
        slope = np.polyfit(x, y, 1)[0]
        return slope, x, y

    def plot_K(self, illumination_powers: list) -> None:
        """
        Plot the relationship between the background-corrected median signal and the
        theoretical scattering cross section for various illumination powers and overlay
        linear regression lines to extract conversion slopes (denoted as K).

        For each illumination power provided in the list, the function:
          - Extracts data for that power from the DataFrame. (The DataFrame is assumed to be
            indexed by illumination power.)
          - Retrieves the background-corrected median signal ('SignalMedian') and the scattering
            cross section ('Csca') for different bead sizes.
          - Performs a linear regression (using regression_for_K) of the scattering cross section
            versus the median signal, yielding the slope K.
          - Plots the data points and the corresponding regression line, labeling each curve with
            the illumination power and the computed slope.

        Parameters:
            dataframe (pd.DataFrame): A DataFrame that contains the columns 'SignalMedian' and 'Csca'.
            illumination_powers (list): A list of illumination power values (e.g., in mW) for which the regression and plotting are to be performed.

        Returns:
            None. The function creates and displays a matplotlib plot.
        """
        with plt.style.context(mps):
            figure, ax = plt.subplots(1, 1, figsize=(10, 5))

            ax.set_xlabel('Median background-corrected signal (a.u.)')
            ax.set_ylabel(r'Scattering cross section $\sigma_s$ (nm$^2$)')
            ax.set_title('Regression for K at various illumination powers')

            for idx, power in enumerate(illumination_powers):
                # Compute regression for the given illumination power.
                K_fit, median_signals, sigma_values = self.regression_for_K(power=power)

                color = f'C{idx}'
                x_fit = np.linspace(median_signals.min(), median_signals.max(), 100)
                y_fit = K_fit * x_fit

                ax.scatter(median_signals, sigma_values, color=color, label=f'{power} mW | Fit: slope={K_fit:.1f}')
                ax.plot(x_fit, y_fit, color=color)

            ax.legend(fontsize=14)
            plt.tight_layout()
            plt.show()

    def plot_J(self, bead_diameters: List[float]) -> None:
        """
        Plot the robust coefficient of variation versus the inverse square root
        of the median signal for multiple bead diameters and overlay linear regression
        lines to extract calibration slopes (denoted as J).

        For each specified bead diameter, the function:
          - Extracts the data (median signal and robust CV) for that bead diameter from
            the provided DataFrame. (The DataFrame is assumed to have a MultiIndex level
            named 'BeadSize' that contains the bead diameters.)
          - Computes the inverse square root of the median signal.
          - Computes a linear regression (using regression_for_J) between the robust CV and
            1/sqrt(median signal) to obtain the slope (J).
          - Plots the data points as a scatter plot and overlays the regression line, labeling
            each curve with the bead diameter and the computed slope.

        Parameters:
            dataframe (pd.DataFrame): A DataFrame that contains at least the columns 'SignalMedian' and 'rCV', indexed by a MultiIndex that includes a level named 'BeadSize'.
            bead_diameters (list): A list of bead diameters (in nm) for which the regression is to be performed and plotted.

        Returns:
            None. The function creates and displays a matplotlib plot.
        """
        with plt.style.context(mps):
            figure, ax = plt.subplots(1, 1, figsize=(10, 5))

            ax.set_xlabel('1 / sqrt(Median signal)')
            ax.set_ylabel('Robust CV')
            ax.set_title('Regression for J (across bead diameters)')

            for idx, diameter in enumerate(bead_diameters):
                color = f'C{idx}'
                # Compute regression for the given bead diameter.
                J_fit, x_data, y_data = self.regression_for_J(diameter=diameter)

                # Create fitted regression line data.
                x_fit = np.linspace(x_data.min(), x_data.max(), 100)
                y_fit = J_fit * x_fit

                ax.scatter(x_data, y_data, color=color, label=f'{diameter} nm | Fit: slope={J_fit:.3f}')
                ax.plot(x_fit, y_fit, color=color)

            ax.legend(fontsize=14)
            plt.tight_layout()
            plt.show()


if __name__ == "__main__":
    from FlowCyPy import units
    illumination_powers = np.array([20, 30, 40, 60, 80, 100, 120]) * units.milliwatt
    number_of_bead_events = 1000 * units.event        # Number of bead events per condition
    number_of_background_events = 10000 * units.event  # Number of background events to simulate


    # Constants and base parameters
    gain = 1 * units.AU / units.photoelectron                                  # Gain (a.u. per photoelectron)
    detection_efficiency = 7.3e-05 * units.photoelectron / units.nanometer**2  # Base detection efficiency at 20 mW (photoelectrons per nm^2)
    background_level = (200.0 * units.nanometer)**2                            # Background level expressed in nm² (assumed constant)



    bead_diameters = np.array([200, 400, 600, 800, 1000, 1200, 2000]) * units.nanometer  # Bead diameters in nanometers


    calibration  = Calibration(
        illumination_powers=illumination_powers,
        gain=gain,
        detection_efficiency=detection_efficiency,
        background_level=background_level,
        number_of_background_events=number_of_background_events,
        number_of_bead_events=number_of_bead_events
    )



    calibration._add_background()

    calibration._add_beads(
        diameters=bead_diameters,
        wavelength=455 * units.nanometer,
        refractive_index=1.4 * units.RIU,
        medium_refractive_index=1.0 * units.RIU
    )


    calibration._simulate_signals()


    calibration.plot_J(bead_diameters=[400, 600])

    _ = calibration.plot_K([20, 40])

