import numpy as np
import pandas as pd
from typing import Optional, Union
import matplotlib.pyplot as plt
from FlowCyPy.units import AU, volt, watt, degree, second, ampere, coulomb
from FlowCyPy.utils import PropertiesReport
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from functools import cached_property
import pint_pandas
from FlowCyPy.physical_constant import PhysicalConstant
from PyMieSim.units import Quantity
from FlowCyPy.noises import NoiseSetting
from FlowCyPy.helper import plot_helper
from FlowCyPy.peak_locator import BasePeakLocator
import logging
from copy import copy

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
    sampling_freq : Quantity
        The sampling frequency of the detector in hertz.
    phi_angle : Quantity
        The detection angle in degrees.
    numerical_aperture : Quantity
        The numerical aperture of the detector, a unitless value.
    responsitivity : Quantity
        Detector's responsivity, default is 1 volt per watt.
    noise_level : Quantity
        The base noise level added to the signal, default is 0 volts.
    baseline_shift : Quantity
        The baseline shift applied to the signal, default is 0 volts.
    saturation_level : Quantity
        The maximum signal level in volts before saturation, default is infinity.
    dark_current : Quantity
        The dark current of the detector, default is 0 amperes.
    resistance : Quantity
        Resistance of the detector, used for thermal noise simulation.
    temperature : Quantity
        Temperature of the detector in Kelvin, used for thermal noise simulation.
    n_bins : Union[int, str]
        The number of discretization bins or bit-depth (e.g., '12bit').
    """
    sampling_freq: Quantity
    phi_angle: Quantity
    numerical_aperture: Quantity

    gamma_angle: Optional[Quantity] = Quantity(0, degree)
    sampling: Optional[Quantity] = 100 * AU
    responsitivity: Optional[Quantity] = Quantity(1, ampere / watt)
    noise_level: Optional[Quantity] = Quantity(0.0, volt)
    baseline_shift: Optional[Quantity] = Quantity(0.0, volt)
    saturation_level: Optional[Quantity] = Quantity(np.inf, volt)
    dark_current: Optional[Quantity] = Quantity(0.0, ampere)  # Dark current
    resistance: Optional[Quantity] = Quantity(50.0, 'ohm')  # Resistance for thermal noise
    temperature: Optional[Quantity] = Quantity(0.0, 'kelvin')  # Temperature for thermal noise
    n_bins: Optional[Union[int, str]] = None
    name: Optional[str] = None

    @cached_property
    def bandwidth(self) -> Quantity:
        return self.sampling_freq / 2
        """
        Automatically calculates the bandwidth based on the sampling frequency.

        Returns
        -------
        Quantity
            The bandwidth of the detector, which is half the sampling frequency (Nyquist limit).
        """
        return self.sampling_freq / 2

    @field_validator('sampling_freq')
    def _validate_sampling_freq(cls, value):
        """
        Validates that the sampling frequency is provided in hertz.

        Parameters
        ----------
        value : Quantity
            The sampling frequency to validate.

        Returns
        -------
        Quantity
            The validated sampling frequency.

        Raises:
            ValueError: If the sampling frequency is not in hertz.
        """
        if not value.check('Hz'):
            raise ValueError(f"sampling_freq must be in hertz, but got {value.units}")
        return value

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

    @field_validator('noise_level', 'baseline_shift', 'saturation_level')
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

        self._process_n_bins()

    def _convert_attr_to_SI(self) -> None:
        # Convert all Quantity attributes to base SI units (without any prefixes)
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Quantity):
                setattr(self, attr_name, attr_value.to_base_units())

    def _process_n_bins(self) -> None:
        r"""
        Processes the `n_bins` attribute to ensure it is an integer representing the number of bins.

        If `n_bins` is provided as a bit-depth string (e.g., '12bit'), it converts it to an integer number of bins.
        If no valid `n_bins` is provided, a default of 100 bins is used.
        """
        if isinstance(self.n_bins, str):
            bit_depth = int(self.n_bins.rstrip('bit'))
            self.n_bins = 2 ** bit_depth

    def _add_thermal_noise_to_raw_signal(self) -> np.ndarray:
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
            4 * PhysicalConstant.kb * self.temperature * self.resistance * self.bandwidth
        )

        thermal_noise = np.random.normal(0, noise_std.to(volt).magnitude, size=len(self.dataframe)) * volt

        self.dataframe['RawSignal'] += thermal_noise

        return thermal_noise

    def _add_dark_current_noise_to_raw_signal(self) -> np.ndarray:
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
            2 * 1.602176634e-19 * coulomb * self.dark_current * self.bandwidth
        )

        dark_current_noise = np.random.normal(0, dark_current_std.to(ampere).magnitude, size=len(self.dataframe)) * ampere

        dark_voltage_noise = dark_current_noise * self.resistance

        self.dataframe['RawSignal'] += dark_voltage_noise

        return dark_voltage_noise

    def _add_optical_power_to_raw_signal(self, optical_power: Quantity) -> None:
        r"""
        Simulates photon shot noise based on the given optical power and detector bandwidth, and returns
        the corresponding voltage noise due to photon shot noise.

        Photon shot noise arises from the random and discrete arrival of photons at the detector. The noise
        follows Poisson statistics, and the standard deviation of the shot noise depends on the photon flux
        and the detector bandwidth. The result is a voltage noise that models these fluctuations.

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
                - \( h \) is Planck's constant \(6.626 \times 10^{-34}\, \text{J} \cdot \text{s}\),
                - \( c \) is the speed of light \(3 \times 10^8 \, \text{m/s}\),
                - \( \lambda \) is the wavelength of the incident light.

            - The standard deviation of the current noise due to photon shot noise is:
            \[
                \sigma_{I_{\text{shot}}} = \sqrt{2 \cdot e \cdot I_{\text{photon}} \cdot B}
            \]
            where:
                - \( I_{\text{photon}} \) is the photocurrent generated by the incident optical power (A),
                - \( e \) is the elementary charge \(1.602 \times 10^{-19} \, \text{C}\),
                - \( B \) is the bandwidth of the detector (Hz).

            - The voltage shot noise \( \sigma_{V_{\text{shot}}} \) is then given by Ohm's law:
            \[
            \sigma_{V_{\text{shot}}} = \sigma_{I_{\text{shot}}} \cdot R_{\text{load}}
            \]
            where:
                - \( R_{\text{load}} \) is the load resistance of the detector (ohms).
        """
        # Step 1: Compute the photocurrent for all time points at once using vectorization
        I_photon = self.responsitivity * optical_power

        # Step 2: Compute the shot noise current for each time point using vectorization
        i_shot = 2 * PhysicalConstant.e * I_photon * self.bandwidth

        I_shot = np.sqrt(i_shot)

        # Step 3: Convert shot noise current to shot noise voltage using vectorization
        V_shot = I_shot * self.resistance

        # Step 4: Generate Gaussian noise for each time point with standard deviation V_shot
        noise_signal = np.random.normal(0, V_shot.to(volt).magnitude, len(self.dataframe['RawSignal'])) * volt

        self.dataframe['RawSignal'] += optical_power * self.responsitivity * self.resistance

        if NoiseSetting.include_shot_noise and NoiseSetting.include_noises:
            self.dataframe['RawSignal'] += noise_signal

        return noise_signal

    def init_raw_signal(self, run_time: Quantity) -> None:
        r"""
        Initializes the raw signal and time arrays for the detector and generates optional noise.

        Parameters
        ----------
        run_time : Quantity
            The total duration of the signal to simulate (in seconds).

        The photocurrent is calculated as:
        \[
            I_{\text{ph}} = P_{\text{opt}} \times R_{\text{ph}}
        \]
        Where:
            - \( P_{\text{opt}} \) is the optical power,
            - \( R_{\text{ph}} \) is the responsivity in amperes per watt.
        """
        self.run_time = run_time
        time_points = int(self.sampling_freq * run_time)
        time = np.linspace(0, run_time, time_points)

        self.dataframe = pd.DataFrame(
            data=dict(
                Time=pint_pandas.PintArray(time, dtype=second),
                RawSignal=pint_pandas.PintArray(np.zeros_like(time), dtype=volt),
                Signal=pint_pandas.PintArray(np.zeros_like(time), dtype=volt)
            )
        )

    def capture_signal(self) -> None:
        """
        Processes and captures the final signal by applying noise, baseline shifts, and saturation.
        """
        self.dataframe['Signal'] = self.dataframe['RawSignal']

        self._apply_baseline_and_noise()
        self._apply_saturation()
        self._discretize_signal()

        self.is_saturated = True if np.any(self.dataframe.Signal == self.saturation_level.to(volt).magnitude) else False

    def _apply_baseline_and_noise(self) -> None:
        """
        Adds baseline shift and base noise to the raw signal.
        """
        w0 = np.pi / 2 / second
        baseline = self.baseline_shift * np.sin(w0 * self.dataframe.Time)

        # Scale noise level by the square root of the bandwidth
        noise_scaling = np.sqrt(self.bandwidth.to('Hz').magnitude)
        noise = self.noise_level * noise_scaling * np.random.normal(size=len(self.dataframe))

        self.dataframe.Signal += baseline + noise

    def _apply_saturation(self) -> None:
        """
        Applies a saturation limit to the signal.

        Signal values that exceed the saturation level are clipped to the maximum allowed value.
        """
        clipped = np.clip(self.dataframe.Signal, 0 * volt, self.saturation_level)
        self.dataframe.Signal = pint_pandas.PintArray(clipped, clipped.units)

    def _discretize_signal(self) -> None:
        """
        Discretizes the processed signal into a specified number of bins.

        The signal is mapped to discrete levels, depending on the number of bins (derived from `n_bins`).
        """

        if self.n_bins is not None:
            max_level = self.saturation_level if not np.isinf(self.saturation_level) else self.dataframe.Signal.max()

            bins = np.linspace(0 * max_level, max_level, self.n_bins)

            digitized = np.digitize(
                x=self.dataframe.Signal.pint.to(volt).pint.magnitude,
                bins=bins.to(volt).magnitude
            ) - 1
            self.dataframe.Signal = pint_pandas.PintArray(bins[digitized], volt)

    @plot_helper
    def plot(
        self,
        color: str = None,
        ax: Optional[plt.Axes] = None,
        time_unit: Optional[Union[str, Quantity]] = None,
        signal_unit: Optional[Union[str, Quantity]] = None,
        add_captured: bool = True,
        add_peak_locator: bool = False,
        add_raw: bool = False
    ) -> tuple[Quantity, Quantity]:
        """
        Visualizes the signal and optional components (peaks, raw signal) over time.

        This method generates a customizable plot of the processed signal as a function of time.
        Additional components like raw signals and detected peaks can also be overlaid.

        Parameters
        ----------
        color : str, optional
            Color for the processed signal line. Default is 'C0' (default Matplotlib color cycle).
        ax : matplotlib.axes.Axes, optional
            An existing Matplotlib Axes object to plot on. If None, a new Axes will be created.
        time_unit : str or Quantity, optional
            Desired unit for the time axis. If None, defaults to the most compact unit of the `Time` column.
        signal_unit : str or Quantity, optional
            Desired unit for the signal axis. If None, defaults to the most compact unit of the `Signal` column.
        add_captured : bool, optional
            If True, overlays the captured signal data on the plot. Default is True.
        add_peak_locator : bool, optional
            If True, adds the detected peaks (if available) to the plot. Default is False.
        add_raw : bool, optional
            If True, overlays the raw signal data on the plot. Default is False.

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
        signal_unit = signal_unit or self.dataframe.Signal.max().to_compact().units
        time_unit = time_unit or self.dataframe.Time.max().to_compact().units

        # Plot captured signal
        if add_captured:
            self._add_captured_signal_to_ax(ax=ax, time_unit=time_unit, signal_unit=signal_unit, color=color)

        # Overlay peak locator positions, if requested
        if add_peak_locator:
            self._add_peak_locator_to_ax(ax=ax, time_unit=time_unit, signal_unit=signal_unit)

        # Overlay raw signal, if requested
        if add_raw:
            self._add_raw_signal_to_ax(ax=ax, time_unit=time_unit, signal_unit=signal_unit)


        # Customize labels
        ax.set_xlabel(f"Time [{time_unit:P}]")
        ax.set_ylabel(f"{self.name} [{signal_unit:P}]")
        ax.legend()

        return time_unit, signal_unit

    def _add_peak_locator_to_ax(self, ax: plt.Axes, time_unit: Quantity, signal_unit: Quantity) -> None:
        """
        Adds peak positions detected by the algorithm to the plot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axis object to plot on.
        time_unit : Quantity
            Unit for the time axis.
        signal_unit : Quantity
            Unit for the signal axis.
        """
        if not hasattr(self, 'algorithm'):
            logging.warning("The detector does not have a peak locator algorithm. Peaks cannot be plotted.")
            return

        self.algorithm._add_to_ax(ax=ax, signal_unit=signal_unit, time_unit=time_unit)

    def _add_captured_signal_to_ax(self, ax: plt.Axes, time_unit: Quantity, signal_unit: Quantity, color: str = None) -> None:
        """
        Adds the processed (captured) signal to the plot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axis object to plot on.
        time_unit : Quantity
            Unit for the time axis.
        signal_unit : Quantity
            Unit for the signal axis.
        color : str
            Color for the signal line.
        """
        if not hasattr(self.dataframe, 'Signal'):
            logging.warning("The detector does not have a captured signal. Please run .capture_signal() method first.")
            return

        x = self.dataframe['Time'].pint.to(time_unit)
        y = self.dataframe['Signal'].pint.to(signal_unit)
        ax.plot(x, y, color=color, label='Processed Signal')

    def _add_raw_signal_to_ax(self, ax: plt.Axes, time_unit: Quantity, signal_unit: Quantity, color: str = None) -> None:
        """
        Adds the raw signal to the plot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axis object to plot on.
        time_unit : Quantity
            Unit for the time axis.
        signal_unit : Quantity
            Unit for the signal axis.
        color : str
            Color for the raw signal line.
        """
        if not hasattr(self.dataframe, 'RawSignal'):
            logging.warning("The detector does not have a captured signal. Please run .init_raw_signal(run_time) method first.")
            return

        x = self.dataframe['Time'].pint.to(time_unit)
        y = self.dataframe['RawSignal'].pint.to(signal_unit)
        ax.plot(x, y, color=color, linestyle='--', label=f'{self.name}: Raw Signal')

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
            'Sampling frequency': self.sampling_freq,
            'Phi angle': self.phi_angle,
            'Gamma angle': self.gamma_angle,
            'Numerical aperture': self.numerical_aperture,
            'Responsitivity': self.responsitivity,
            'Saturation Level': self.saturation_level,
            'Dark Current': self.dark_current,
            'Resistance': self.resistance,
            'Temperature': self.temperature,
            'N Bins': self.n_bins
        }

        super(Detector, self).print_properties(**_dict)
