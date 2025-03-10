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
from FlowCyPy.helper import validate_units

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict, unsafe_hash=True)
class Detector():
    """
    Represents a photodetector in a flow cytometry simulation.

    This class simulates a detector that captures light scattering signals, incorporating
    the effects of noise sources (shot noise, thermal noise, and dark current noise) as part
    of the signal processing workflow.

    Parameters
    ----------
    name : str, optional
        Identifier for the detector. If not provided, a unique ID is assigned.
    phi_angle : Quantity
        The detector's primary angle of incidence (in degrees).
    numerical_aperture : Quantity
        The numerical aperture of the detector (dimensionless).
    cache_numerical_aperture : Quantity, optional
        The numerical aperture of the cache positioned in front of the detector (dimensionless).
    responsivity : Quantity, optional
        Detector responsivity (in ampere per watt). Default is 1 A/W.
    dark_current : Quantity, optional
        The dark current of the detector (in amperes). Default is 0 A.
    resistance : Quantity, optional
        The load resistance of the detector used in thermal noise simulation (in ohms). Default is 50 Ω.
    temperature : Quantity, optional
        Operating temperature of the detector (in kelvin) for thermal noise simulation.
    gamma_angle : Quantity, optional
        An additional angular parameter (in degrees), if applicable.
    sampling : Quantity, optional
        Sampling rate or related parameter (unitless or arbitrary units), default is 100.
    """
    phi_angle: Quantity
    numerical_aperture: Quantity

    cache_numerical_aperture: Quantity = Quantity(0, units.AU)
    gamma_angle: Optional[Quantity] = Quantity(0, units.degree)
    sampling: Optional[Quantity] = Quantity(100, units.AU)
    responsivity: Optional[Quantity] = Quantity(1, units.ampere / units.watt)
    dark_current: Optional[Quantity] = Quantity(0.0, units.ampere)
    resistance: Optional[Quantity] = Quantity(50.0, units.ohm)
    temperature: Optional[Quantity] = Quantity(0.0, units.kelvin)
    name: Optional[str] = None


    @field_validator('dark_current')
    def _validate_current(cls, value):
        """
        Validates that the provided dark_current are in ampere units.

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
        if not value.check(units.ampere):
            raise ValueError(f"dark_current must be in Ampere, but got {value.units}")
        return value

    @field_validator('resistance')
    def _validate_resistance(cls, value):
        """
        Validates that the provided angles are in ohm units.

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
        if not value.check(units.ohm):
            raise ValueError(f"Resistance must be in Ohm, but got {value.units}")
        return value

    @field_validator('temperature')
    def _validate_temperature(cls, value):
        """
        Validates that the provided angles are in arbitrary units.

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
        if not value.check(units.kelvin):
            raise ValueError(f"Angle must be in kelvin, but got {value.units}")
        return value

    @field_validator('numerical_aperture', 'numerical_aperture')
    def _validate_numerical_aperture(cls, value):
        """
        Validates that the provided angles are in arbitrary units.

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
        if not value.check(units.AU):
            raise ValueError(f"Angle must be in arbitrary units, but got {value.units}")
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

    @field_validator('responsivity')
    def _validate_responsivity(cls, value):
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
        """
        Retrieves the detector-specific slice of the cytometer's dataframe.

        Returns
        -------
        pd.DataFrame
            A dataframe corresponding to the detector's recorded data.
        """
        return self.cytometer.dataframe.xs(self.name)

    @validate_units(run_time=units.second)
    def get_initialized_signal(self, run_time: Quantity) -> pd.DataFrame:
        """
        Initializes a placeholder for the detector's raw signal over a specified runtime.

        This method creates a time-dependent DataFrame with columns for time and the
        corresponding signal (initialized to zero volts).

        Parameters
        ----------
        run_time : Quantity
            The total acquisition time for the signal (in seconds).

        Returns
        -------
        pd.DataFrame
            A DataFrame with a time column (in seconds) and a signal column (in volts),
            initialized to zero.
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
        """
        Generates the composite noise signal over a specified sequence length.

        This method computes and aggregates different noise components
        (e.g., thermal and dark current noise) based on their parameters.

        Parameters
        ----------
        sequence_length : int
            The number of data points for which to generate the noise signal.

        Returns
        -------
        Quantity
            The aggregated noise signal (in volts) as a Quantity array.
        """
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

        Thermal noise (Johnson-Nyquist noise) results from the thermal agitation of charge carriers
        and is computed using the formula:

        .. math::
            \sigma_{\text{thermal}} = \sqrt{4 k_B T B R}

        where:
            - :math:`k_B` is the Boltzmann constant (1.38 x 10⁻²³ J/K),
            - :math:`T` is the temperature in Kelvin,
            - :math:`B` is the bandwidth,
            - :math:`R` is the resistance.

        Dark current noise is computed as:

        .. math::
            \sigma_{\text{dark}} = \sqrt{2 q I_d B}

        where:
        - :math:`q` is the elementary charge (1.602176634 x 10⁻¹⁹ C),
        - :math:`I_d` is the dark current,
        - :math:`B` is the bandwidth.

        Returns
        -------
        dict
            Dictionary containing noise parameters for 'thermal' and 'dark_current'.
        """
        noises = dict(
            thermal=None,
            dark_current=None
        )

        if not NoiseSetting.include_noises:
            return noises

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

    @validate_units(optical_power=units.watt, wavelength=units.meter)
    def get_shot_noise(self, signal: pd.Series, optical_power: Quantity, wavelength: Quantity) -> Quantity:
        r"""
        Computes the shot noise voltage arising from photon statistics.

        Shot noise is due to the discrete nature of photon arrivals. The process includes:
            1. Calculating the energy per photon.
            2. Estimating the mean number of photons arriving per sampling interval.
            3. Simulating photon counts via Poisson statistics (or a normal approximation for high counts).
            4. Converting photon counts to photocurrent using the detector responsivity.
            5. Converting the photocurrent to voltage noise using the detector resistance.


        Physics:
            - The number of photons arriving at the detector \( N_{\text{ph}} \) is given by: \[ N_{\text{ph}} = \frac{P_{\text{opt}}}{E_{\text{photon}}} \]

            where:
                - \( P_{\text{opt}} \) is the optical power (W),
                - \( E_{\text{photon}} = \frac{h \cdot c}{\lambda} \) is the energy of a photon (J),
                - \( h \) is Planck's constant (\(6.626 \times 10^{-34}\, \text{J} \cdot \text{s}\)),
                - \( c \) is the speed of light (\(3 \times 10^8 \, \text{m/s}\)),
                - \( \lambda \) is the wavelength of the incident light.

            - The photocurrent is computed as: \[ I_{\text{photon}} = R_{\text{det}} \cdot N_{\text{photon}} \]

            where:
                - \( R_{\text{det}} \) is the detector responsivity (A/W).

            - The voltage shot noise is then given by: \[ V_{\text{shot}} = I_{\text{photon}} \cdot R_{\text{load}} \]

            where:
                - \( R_{\text{load}} \) is the load resistance of the detector (Ohms).

        Parameters
        ----------
        signal : pd.Series
            The raw signal data series (used to infer the number of samples).
        optical_power : Quantity
            The incident optical power on the detector (in watts).
        wavelength : Quantity
            The wavelength of the incident light (in meters).

        Returns
        -------
        Quantity
            The shot noise voltage distribution (in volts).
        """
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

        photocurrent_distribution = self.responsivity * photon_power_distribution  # Current (A)
        # Step 5: Convert photocurrent to shot noise voltage
        shot_noise_voltage_distribution = photocurrent_distribution * self.resistance  # Voltage (V)

        return shot_noise_voltage_distribution

    @validate_units(optical_power=units.watt, wavelength=units.meter)
    def capture_signal(self, signal: pd.Series, optical_power: Quantity, wavelength: Quantity) -> pd.Series:
        r"""
        Simulates the capture of a signal by adding photon shot noise to the raw signal.

        This method calculates the shot noise voltage (based on the given optical power and wavelength)
        and adds it to the existing raw signal to simulate the detector's output.

        Parameters
        ----------
        signal : pd.Series
            The original raw signal data (in volts).
        optical_power : Quantity
            The optical power incident on the detector (in watts).
        wavelength : Quantity
            The wavelength of the incident light (in meters).

        Returns
        -------
        None
            The raw signal is updated in place with the added shot noise.

        Physics Background
        ------------------
        Photon shot noise arises due to the random arrival of photons. The following relationships are used:
            - Photon energy: \( E_{\text{photon}} = \frac{h c}{\lambda} \)
            - Photon rate: \( N_{\text{ph}} = \frac{P_{\text{opt}}}{E_{\text{photon}}} \)
            - Photocurrent: \( I_{\text{photon}} = R_{\text{det}} \cdot N_{\text{photon}} \)
            - Shot noise voltage: \( V_{\text{shot}} = I_{\text{photon}} \cdot R_{\text{load}} \)

        """
        if not NoiseSetting.include_shot_noise or not NoiseSetting.include_noises:
            return signal + (optical_power * self.responsivity * self.resistance)

        return signal + self.get_shot_noise(
            signal=signal,
            optical_power=optical_power,
            wavelength=wavelength
        )

class PMT():
    def __new__(cls,
        name: str,
        phi_angle: Quantity,
        numerical_aperture: Quantity,
        responsivity: Quantity = Quantity(0.2, units.ampere / units.watt),
        dark_current: Quantity = Quantity(1e-9, units.ampere),
        resistance: Quantity = Quantity(50, units.ohm),
        temperature: Quantity = Quantity(293, units.kelvin),
        **kwargs):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            resistance=resistance,
            temperature=temperature,
            **kwargs
        )

# Predefined PIN Photodiode Detector
class PIN():
    def __new__(cls,
        name: str,
        phi_angle: Quantity,
        numerical_aperture: Quantity,
        responsivity=Quantity(0.5, units.ampere / units.watt),  # Higher responsivity for PIN
        dark_current=Quantity(1e-8, units.ampere),               # Slightly higher dark current
        resistance=Quantity(100, units.ohm),
        temperature=Quantity(293, units.kelvin),
        **kwargs):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            resistance=resistance,
            temperature=temperature,
            **kwargs
        )


# Predefined Avalanche Photodiode (APD) Detector
class APD():
    def __new__(cls,
        name: str,
        phi_angle: Quantity,
        numerical_aperture: Quantity,
        responsivity=Quantity(0.7, units.ampere / units.watt),  # APDs often have high responsivity
        dark_current=Quantity(5e-9, units.ampere),
        resistance=Quantity(75, units.ohm),
        temperature=Quantity(293, units.kelvin),
        **kwargs):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            resistance=resistance,
            temperature=temperature,
            **kwargs
        )
