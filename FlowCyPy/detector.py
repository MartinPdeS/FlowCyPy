import numpy as np
import pandas as pd
from typing import Optional, Union
import matplotlib.pyplot as plt
from FlowCyPy import units
from FlowCyPy.units import AU, volt, watt, degree, ampere, coulomb, particle, meter
from FlowCyPy.utils import PropertiesReport
from pydantic.dataclasses import dataclass
from pydantic import field_validator
import pint_pandas
from FlowCyPy.physical_constant import PhysicalConstant
from PyMieSim.units import Quantity
from FlowCyPy.noises import NoiseSetting
from FlowCyPy.helper import plot_helper
from FlowCyPy.peak_locator import BasePeakLocator
import logging
from copy import copy
from FlowCyPy.signal_digitizer import SignalDigitizer

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict, unsafe_hash=True)
class Detector(PropertiesReport):
    """
    A class representing a signal detector used in flow cytometry.

    This class models a photodetector, simulating signal acquisition, noise addition, and signal processing
    for analysis.  It can optionally simulate different noise sources: shot noise, thermal noise, and dark current noise.

    Parameters
    ----------
    name : str
        The name or identifier of the detector.
    phi_angle : Quantity
        The detection angle in degrees.
    numerical_aperture : Quantity
        The numerical aperture of the detector, a unitless value.
    responsitivity : Quantity
        Detector's responsivity, default is 1 volt per watt.
    baseline_shift : Quantity
        The baseline shift applied to the signal, default is 0 volts.
    dark_current : Quantity
        The dark current of the detector, default is 0 amperes.
    resistance : Quantity
        Resistance of the detector, used for thermal noise simulation.
    temperature : Quantity
        Temperature of the detector in Kelvin, used for thermal noise simulation.
    """
    phi_angle: Quantity
    numerical_aperture: Quantity
    signal_digitizer: SignalDigitizer

    gamma_angle: Optional[Quantity] = Quantity(0, degree)
    sampling: Optional[Quantity] = 100 * AU
    responsitivity: Optional[Quantity] = Quantity(1, ampere / watt)
    baseline_shift: Optional[Quantity] = Quantity(0.0, volt)
    dark_current: Optional[Quantity] = Quantity(0.0, ampere)  # Dark current
    resistance: Optional[Quantity] = Quantity(50.0, 'ohm')  # Resistance for thermal noise
    temperature: Optional[Quantity] = Quantity(0.0, 'kelvin')  # Temperature for thermal noise
    name: Optional[str] = None


    @field_validator('phi_angle', 'gamma_angle')
    def _validate_angles(cls, value):
        """
        Validates that the provided angles are in degrees.

        Parameters
        ----------
        value : Quantity
            The angle value to validate.

        Returns
        -------
        Quantity
            The validated angle.

        Raises:
            ValueError: If the angle is not in degrees.
        """
        if not value.check('degree'):
            raise ValueError(f"Angle must be in degrees, but got {value.units}")
        return value

    @field_validator('responsitivity')
    def _validate_responsitivity(cls, value):
        """
        Validates that the detector's responsivity is provided in volts per watt.

        Parameters
        ----------
        value : Quantity
            The responsivity value to validate.

        Returns:
            Quantity: The validated responsivity.

        Raises:
            ValueError: If the responsivity is not in volts per watt.
        """
        if not value.check('A / W'):
            raise ValueError(f"Responsitivity must be in ampere per watt, but got {value.units}")
        return value

    @field_validator('baseline_shift')
    def _validate_voltage_attributes(cls, value):
        """
        Validates that noise level, baseline shift, and saturation level are all in volts.

        Parameters
        ----------
        value : Quantity
            The voltage attribute to validate (noise level, baseline shift, or saturation).

        Returns
        -------
        Quantity
            The validated voltage attribute.

        Raises:
            ValueError: If the attribute is not in volts.
        """
        if not value.check('volt'):
            raise ValueError(f"Voltage attributes must be in volts, but got {value.units}")
        return value

    def __post_init__(self) -> None:
        """
        Finalizes the initialization of the detector object and processes the number of bins.
        """
        if self.name is None:
            self.name = str(id(self))

    def _convert_attr_to_SI(self) -> None:
        # Convert all Quantity attributes to base SI units (without any prefixes)
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Quantity):
                setattr(self, attr_name, attr_value.to_base_units())

    @property
    def dataframe(self) -> pd.DataFrame:
        return self.cytometer.dataframe.xs(self.name)

    def get_initialized_signal(self, run_time: Quantity) -> pd.DataFrame:
        """
        Initializes the raw signal for each detector based on the source and flow cell configuration.

        This method prepares the detectors for signal capture by associating each detector with the
        light source and generating a time-dependent raw signal placeholder.

        Effects
        -------
        Each detector's `raw_signal` attribute is initialized with time-dependent values
        based on the flow cell's runtime.

        """
        time_points = int(self.signal_digitizer.sampling_freq * run_time)
        time = np.linspace(0, run_time, time_points)

        return pd.DataFrame(
            data=dict(
                Time=pint_pandas.PintArray(time, dtype=units.second),
                RawSignal=pint_pandas.PintArray(np.zeros_like(time), dtype=units.volt),
                Signal=pint_pandas.PintArray(np.zeros_like(time), dtype=units.volt),
                DigitizedSignal=np.zeros_like(time)
            )
        )

    def _add_thermal_noise_to_raw_signal(self, signal: pd.Series) -> np.ndarray:
        r"""
        Generates thermal noise (Johnson-Nyquist noise) based on temperature, resistance, and bandwidth.

        Thermal noise is caused by the thermal agitation of charge carriers. It is given by:
        \[
            \sigma_{\text{thermal}} = \sqrt{4 k_B T B R}
        \]
        Where:
            - \( k_B \) is the Boltzmann constant (\(1.38 \times 10^{-23}\) J/K),
            - \( T \) is the temperature in Kelvin,
            - \( B \) is the bandwidth,
            - \( R \) is the resistance.

        Returns
        -------
        np.ndarray
            An array of thermal noise values.
        """
        if self.resistance.magnitude == 0 or self.temperature.magnitude == 0 or not NoiseSetting.include_thermal_noise or not NoiseSetting.include_noises:
            return

        noise_std = np.sqrt(
            4 * PhysicalConstant.kb * self.temperature * self.resistance * self.signal_digitizer.bandwidth
        )

        thermal_noise = np.random.normal(0, noise_std.to(volt).magnitude, size=len(signal)) * volt

        signal += thermal_noise

        return thermal_noise

    def _add_dark_current_noise_to_raw_signal(self, signal: pd.Series) -> np.ndarray:
        r"""
        Generates dark current noise (shot noise from dark current).

        Dark current noise is a type of shot noise caused by the random generation of electrons in a detector,
        even in the absence of light. It is given by:
        \[
            \sigma_{\text{dark current}} = \sqrt{2 e I_{\text{dark}} B}
        \]
        Where:
            - \( e \) is the elementary charge,
            - \( I_{\text{dark}} \) is the dark current,
            - \( B \) is the bandwidth.

        Returns
        -------
        np.ndarray
            An array of dark current noise values.
        """
        if self.dark_current.magnitude == 0 or not NoiseSetting.include_dark_current_noise or not NoiseSetting.include_noises:
            return

        dark_current_std = np.sqrt(
            2 * 1.602176634e-19 * coulomb * self.dark_current * self.signal_digitizer.bandwidth
        )

        dark_current_noise = np.random.normal(0, dark_current_std.to(ampere).magnitude, size=len(signal)) * ampere

        dark_voltage_noise = dark_current_noise * self.resistance

        signal += dark_voltage_noise

        return dark_voltage_noise

    def _add_optical_power_to_raw_signal(self, signal: pd.Series, optical_power: Quantity, wavelength: Quantity) -> None:
        r"""
        Simulates photon shot noise based on the given optical power and detector bandwidth, and adds
        the corresponding voltage noise to the raw signal.

        Photon shot noise arises from the random and discrete arrival of photons at the detector. The noise
        follows Poisson statistics. This method computes the photon shot noise and adds it to the raw signal.

        Parameters
        ----------
        optical_power : Quantity
            The optical power incident on the detector, in watts (W).

        Returns
        -------
        np.ndarray
            An array representing the voltage noise due to photon shot noise, in volts (V).

        Physics:
            - The number of photons arriving at the detector \( N_{\text{ph}} \) is given by:
            \[
                N_{\text{ph}} = \frac{P_{\text{opt}}}{E_{\text{photon}}}
            \]
            where:
                - \( P_{\text{opt}} \) is the optical power (W),
                - \( E_{\text{photon}} = \frac{h \cdot c}{\lambda} \) is the energy of a photon (J),
                - \( h \) is Planck's constant (\(6.626 \times 10^{-34}\, \text{J} \cdot \text{s}\)),
                - \( c \) is the speed of light (\(3 \times 10^8 \, \text{m/s}\)),
                - \( \lambda \) is the wavelength of the incident light.

            - The photocurrent is computed as:
            \[
                I_{\text{photon}} = R_{\text{det}} \cdot N_{\text{photon}}
            \]
            where:
                - \( R_{\text{det}} \) is the detector responsivity (A/W).

            - The voltage shot noise is then given by:
            \[
            V_{\text{shot}} = I_{\text{photon}} \cdot R_{\text{load}}
            \]
            where:
                - \( R_{\text{load}} \) is the load resistance of the detector (Ohms).
        """
        # Step 1: Compute photon energy
        energy_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength  # Photon energy (J)

        # Step 2: Compute mean photon count per sampling interval
        photon_rate = optical_power / energy_photon  # Photon rate (photons/s)

        sampling_interval = 1 / self.signal_digitizer.sampling_freq  # Sampling interval (s)
        mean_photon_count = photon_rate * sampling_interval  # Mean photons per sample

        # Step 3: Simulate photon arrivals using Poisson statistics
        photon_counts_distribution = np.random.poisson(mean_photon_count.to('').magnitude, size=len(signal))

        # Step 4: Convert photon counts to photocurrent
        photon_power_distribution = photon_counts_distribution * energy_photon * self.signal_digitizer.sampling_freq

        photocurrent_distribution = self.responsitivity * photon_power_distribution  # Current (A)
        # Step 5: Convert photocurrent to shot noise voltage
        shot_noise_voltage_distribution = photocurrent_distribution * self.resistance  # Voltage (V)

        # Step 6: Add shot noise voltage to the raw signal
        signal += shot_noise_voltage_distribution

        return shot_noise_voltage_distribution

    def capture_signal(self, signal: pd.Series) -> None:
        """
        Processes and captures the final signal by applying noise, baseline shifts, and saturation.
        """
        digitized_signal, is_saturated = self.signal_digitizer.discretize_signal(signal)

        return digitized_signal, is_saturated

    @plot_helper
    def plot_raw(
        self,
        ax: Optional[plt.Axes] = None,
        time_unit: Optional[Union[str, Quantity]] = None,
        signal_unit: Optional[Union[str, Quantity]] = None,
        add_peak_locator: bool = False
    ) -> None:
        """
        Visualizes the signal and optional components (peaks, raw signal) over time.

        This method generates a customizable plot of the processed signal as a function of time.
        Additional components like raw signals and detected peaks can also be overlaid.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            An existing Matplotlib Axes object to plot on. If None, a new Axes will be created.
        time_unit : str or Quantity, optional
            Desired unit for the time axis. If None, defaults to the most compact unit of the `Time` column.
        signal_unit : str or Quantity, optional
            Desired unit for the signal axis. If None, defaults to the most compact unit of the `Signal` column.
        add_peak_locator : bool, optional
            If True, adds the detected peaks (if available) to the plot. Default is False.

        Returns
        -------
        tuple[Quantity, Quantity]
            A tuple containing the units used for the time and signal axes, respectively.

        Notes
        -----
        - The `Time` and `Signal` data are automatically converted to the specified units for consistency.
        - If no `ax` is provided, a new figure and axis will be generated.
        - Warnings are logged if peak locator data is unavailable when `add_peak_locator` is True.
        """
        # Set default units if not provided
        signal_unit = signal_unit or self.dataframe['Signal'].max().to_compact().units
        time_unit = time_unit or self.dataframe['Time'].max().to_compact().units

        x = self.dataframe['Time'].pint.to(time_unit)

        ax.plot(x, self.dataframe['Signal'].pint.to(signal_unit), color='C1', linestyle='--', label=f'{self.name}: Raw', linewidth=1)
        ax.legend(loc='upper right')

        # Overlay peak locator positions, if requested
        if add_peak_locator:
            if not hasattr(self, 'algorithm'):
                logging.warning("The detector does not have a peak locator algorithm. Peaks cannot be plotted.")

            self.algorithm._add_to_ax(ax=ax, signal_unit=signal_unit, time_unit=time_unit)

        # Customize labels
        ax.set_xlabel(f"Time [{time_unit:P}]")
        ax.set_ylabel(f"{self.name} [{signal_unit:P}]")

    def set_peak_locator(self, algorithm: BasePeakLocator, compute_peak_area: bool = True) -> None:
        """
        Assigns a peak detection algorithm to the detector, analyzes the signal,
        and extracts peak features such as height, width, and area.

        Parameters
        ----------
        algorithm : BasePeakLocator
            An instance of a peak detection algorithm derived from BasePeakLocator.
        compute_peak_area : bool, optional
            Whether to compute the area under the detected peaks (default is True).

        Raises
        ------
        TypeError
            If the provided algorithm is not an instance of BasePeakLocator.
        ValueError
            If the algorithm has already been initialized with peak data.
        RuntimeError
            If the detector's signal data (dataframe) is not available.

        Notes
        -----
            - The `algorithm` parameter should be a fresh instance of a peak detection algorithm.
            - The method will analyze the detector's signal immediately upon setting the algorithm.
            - Peak detection results are stored in the algorithm's `peak_properties` attribute.
        """

        # Ensure the algorithm is an instance of BasePeakLocator
        if not isinstance(algorithm, BasePeakLocator):
            raise TypeError("The algorithm must be an instance of BasePeakLocator.")

        # Ensure the detector has signal data available for analysis
        if not hasattr(self, 'dataframe') or self.dataframe is None:
            raise RuntimeError("The detector does not have signal data available for peak detection.")

        # Set the algorithm and perform peak detection
        self.algorithm = copy(algorithm)
        self.algorithm.init_data(self.dataframe)
        self.algorithm.detect_peaks(compute_area=compute_peak_area)

        # Log the result of peak detection
        peak_count = len(self.algorithm.peak_properties) if hasattr(self.algorithm, 'peak_properties') else 0
        logging.info(f"Detector {self.name}: Detected {peak_count} peaks.")

    def print_properties(self) -> None:
        """
        Prints specific properties of the Detector instance, such as coupling factor and medium refractive index.
        This method calls the parent class method to handle the actual property printing logic.

        """
        _dict = {
            'Sampling frequency': self.signal_digitizer.sampling_freq,
            'Phi angle': self.phi_angle,
            'Gamma angle': self.gamma_angle,
            'Numerical aperture': self.numerical_aperture,
            'Responsitivity': self.responsitivity,
            'Saturation Level': self.signal_digitizer.saturation_levels,
            'Dark Current': self.dark_current,
            'Resistance': self.resistance,
            'Temperature': self.temperature,
            'N Bins': self.signal_digitizer.bit_depth
        }

        super(Detector, self).print_properties(**_dict)
