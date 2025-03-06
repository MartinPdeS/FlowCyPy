import numpy as np
import pandas as pd
from typing import Optional
from pydantic.dataclasses import dataclass
from pydantic import field_validator
import pint_pandas

from PyMieSim.units import Quantity
from FlowCyPy import units
from FlowCyPy.noises import NoiseSetting
from FlowCyPy.physical_constant import PhysicalConstant

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict, unsafe_hash=True)
class Detector():
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
    cache_numerical_aperture : Quantity
        The numerical aperture of the cache in front of the detector, a unitless value.
    responsitivity : Quantity
        Detector's responsivity, default is 1 volt per watt.
    dark_current : Quantity
        The dark current of the detector, default is 0 amperes.
    resistance : Quantity
        Resistance of the detector, used for thermal noise simulation.
    temperature : Quantity
        Temperature of the detector in Kelvin, used for thermal noise simulation.
    """
    phi_angle: Quantity
    numerical_aperture: Quantity

    cache_numerical_aperture: Quantity = Quantity(0, units.AU)
    gamma_angle: Optional[Quantity] = Quantity(0, units.degree)
    sampling: Optional[Quantity] = Quantity(100, units.AU)
    responsitivity: Optional[Quantity] = Quantity(1, units.ampere / units.watt)
    dark_current: Optional[Quantity] = Quantity(0.0, units.ampere)  # Dark current
    resistance: Optional[Quantity] = Quantity(50.0, units.ohm)  # Resistance for thermal noise
    temperature: Optional[Quantity] = Quantity(0.0, units.kelvin)  # Temperature for thermal noise
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

    def __post_init__(self) -> None:
        """
        Finalizes the initialization of the detector object and processes the number of bins.
        """
        if self.name is None:
            self.name = str(id(self))

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
        time_points = int(self.signal_digitizer.sampling_rate * run_time)
        time = np.linspace(0, run_time, time_points)

        return pd.DataFrame(
            data=dict(
                Time=pint_pandas.PintArray(time, dtype=units.second),
                Signal=pint_pandas.PintArray(np.zeros_like(time), dtype=units.volt),
            )
        )

    def get_noise_signal(self, sequence_length: int):
        # Generate noise components
        signal = np.zeros(sequence_length) * units.volt
        noise_dictionnary = self.get_noise_parameters()

        for _, parameters in noise_dictionnary.items():
            if parameters is None:
                continue

            signal_units = signal.units
            # Generate noise values for this group
            noise = np.random.normal(
                parameters['mean'].to(signal_units).magnitude,
                parameters['std'].to(signal_units).magnitude,
                size=len(signal)
            ) * signal_units

            # Update the 'Signal' column in the original DataFrame using .loc
            signal += noise

        return signal

    def get_noise_parameters(self) -> dict:
        r"""
        Compute and return the noise parameters for thermal and dark current noise.

        Thermal noise (Johnson–Nyquist noise) results from the thermal agitation of charge carriers
        and is computed using the formula:

        .. math::
            \sigma_{\text{thermal}} = \sqrt{4 k_B T B R}

        where:
        - :math:`k_B` is the Boltzmann constant (1.38×10⁻²³ J/K),
        - :math:`T` is the temperature in Kelvin,
        - :math:`B` is the bandwidth,
        - :math:`R` is the resistance.

        Dark current noise is computed as:

        .. math::
            \sigma_{\text{dark}} = \sqrt{2 q I_d B}

        where:
        - :math:`q` is the elementary charge (1.602176634×10⁻¹⁹ C),
        - :math:`I_d` is the dark current,
        - :math:`B` is the bandwidth.

        Returns
        -------
        dict
            A dictionary with the following structure:
            {
                'thermal': {
                    'mean': 0 * volt,
                    'std': computed thermal noise standard deviation
                },
                'dark_current': {
                    'mean': 0 * volt,
                    'std': computed dark current noise standard deviation
                }
            }
        """
        noises = dict(
            thermal=None,
            dark_current=None
        )

        if not NoiseSetting.include_noises:
            return noises

        # if self.resistance.magnitude == 0 or self.temperature.magnitude == 0 or not NoiseSetting.include_thermal_noise or not NoiseSetting.include_noises:
        if NoiseSetting.include_thermal_noise:
            noises['thermal'] = {
                'mean': 0 * units.volt,
                'std':np.sqrt(4 * PhysicalConstant.kb * self.temperature * self.resistance * self.signal_digitizer.bandwidth)
            }

        if NoiseSetting.include_dark_current_noise:
            noises['dark_current'] = {
                'mean': 0 * units.volt,
                'std': np.sqrt(2 * 1.602176634e-19 * units.coulomb * self.dark_current * self.signal_digitizer.bandwidth) * self.resistance
            }


        return noises

    def get_shot_noise(self, signal: pd.Series, optical_power: Quantity, wavelength: Quantity) -> None:
        if not NoiseSetting.include_shot_noise or not NoiseSetting.include_noises:
            return optical_power * self.responsitivity * self.resistance

        else:
            # Step 1: Compute photon energy
            energy_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength  # Photon energy (J)

            # Step 2: Compute mean photon count per sampling interval
            photon_rate = optical_power / energy_photon  # Photon rate (photons/s)

            sampling_interval = 1 / self.signal_digitizer.sampling_rate  # Sampling interval (s)
            mean_photon_count = photon_rate * sampling_interval  # Mean photons per sample

            # Step 3: Simulate photon arrivals using Poisson statistics
            mean = mean_photon_count.to('').magnitude
            if np.max(mean) > 1e6:  # Threshold where Poisson becomes unstable
                photon_counts_distribution = np.random.normal(mean, np.sqrt(mean), size=len(signal)).astype(int)
            else:
                photon_counts_distribution = np.random.poisson(mean, size=len(signal))


            # Step 4: Convert photon counts to photocurrent
            photon_power_distribution = photon_counts_distribution * energy_photon * self.signal_digitizer.sampling_rate

            photocurrent_distribution = self.responsitivity * photon_power_distribution  # Current (A)
            # Step 5: Convert photocurrent to shot noise voltage
            shot_noise_voltage_distribution = photocurrent_distribution * self.resistance  # Voltage (V)

            return shot_noise_voltage_distribution

    def capture_signal(self, signal: pd.Series, optical_power: Quantity, wavelength: Quantity) -> None:
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
        if not NoiseSetting.include_shot_noise or not NoiseSetting.include_noises:
            return np.ones(len(signal)) * optical_power * self.responsitivity * self.resistance

        else:
            # Step 1: Compute photon energy
            energy_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength  # Photon energy (J)

            # Step 2: Compute mean photon count per sampling interval
            photon_rate = optical_power / energy_photon  # Photon rate (photons/s)

            sampling_interval = 1 / self.signal_digitizer.sampling_rate  # Sampling interval (s)
            mean_photon_count = photon_rate * sampling_interval  # Mean photons per sample

            # Step 3: Simulate photon arrivals using Poisson statistics
            mean = mean_photon_count.to('').magnitude
            if np.max(mean) > 1e6:  # Threshold where Poisson becomes unstable
                photon_counts_distribution = np.random.normal(mean, np.sqrt(mean), size=len(signal)).astype(int)
            else:
                photon_counts_distribution = np.random.poisson(mean, size=len(signal))

            print('photon_counts_distribution', photon_counts_distribution)

            # Step 4: Convert photon counts to photocurrent
            photon_power_distribution = photon_counts_distribution * energy_photon * self.signal_digitizer.sampling_rate

            photocurrent_distribution = self.responsitivity * photon_power_distribution  # Current (A)
            # Step 5: Convert photocurrent to shot noise voltage
            shot_noise_voltage_distribution = photocurrent_distribution * self.resistance  # Voltage (V)

            # Step 6: Add shot noise voltage to the raw signal
            signal += shot_noise_voltage_distribution

            return shot_noise_voltage_distribution
