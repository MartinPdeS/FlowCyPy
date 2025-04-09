import numpy as np
import pandas as pd
from typing import Optional
from pydantic.dataclasses import dataclass
from pydantic import field_validator

from PyMieSim.units import Quantity
from FlowCyPy import units
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
    Represents a photodetector for flow cytometry simulations.

    This class simulates a photodetector that captures light scattering signals in a flow
    cytometry setup. It models the detector's response by incorporating various noise sources
    (shot noise, thermal noise, and dark current noise) into the signal processing workflow,
    thereby providing a realistic representation of detector performance.

    Parameters
    ----------
    name : str, optional
        A unique identifier for the detector. If not provided, a unique ID is generated.
    phi_angle : Quantity
        The primary azimuthal angle of incidence for the detector (in degrees).
    numerical_aperture : Quantity
        The numerical aperture of the detector (dimensionless).
    cache_numerical_aperture : Quantity, optional
        The numerical aperture of the caching element placed in front of the detector
        (dimensionless). Default is 0 AU.
    responsivity : Quantity, optional
        The responsivity of the detector (in amperes per watt). Default is 1 A/W. Typical
        ranges include 0.4–0.7 A/W for silicon-based detectors and 0.8–0.9 A/W for InGaAs-based
        detectors.
    dark_current : Quantity, optional
        The dark current of the detector (in amperes). Default is 0 A. Typical values are in the
        range of 1–100 nA.
    gamma_angle : Quantity, optional
        The complementary (longitudinal) angle of incidence, if applicable (in degrees).
        Default is 0°.
    sampling : Quantity, optional
        The number of spatial sampling points defining the detector’s resolution. Default is 100 AU.

    Attributes
    ----------
    phi_angle : Quantity
        The detector's primary azimuthal angle (in degrees).
    numerical_aperture : Quantity
        The detector's numerical aperture (dimensionless).
    cache_numerical_aperture : Quantity
        The numerical aperture of the cache element (dimensionless).
    responsivity : Quantity
        The responsivity of the detector (in amperes per watt).
    dark_current : Quantity
        The dark current of the detector (in amperes).
    gamma_angle : Quantity
        The complementary (longitudinal) angle (in degrees).
    sampling : Quantity
        The number of spatial sampling points.
    name : str
        The identifier for the detector.
    """
    phi_angle: Quantity
    numerical_aperture: Quantity

    cache_numerical_aperture: Quantity = Quantity(0, units.AU)
    gamma_angle: Optional[Quantity] = Quantity(0, units.degree)
    sampling: Optional[Quantity] = Quantity(100, units.AU)
    responsivity: Optional[Quantity] = Quantity(1, units.ampere / units.watt)
    dark_current: Optional[Quantity] = Quantity(0.0, units.ampere)
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

    def get_dark_current_noise(self, sequence_length: int, bandwidth: Quantity) -> Quantity:
        r"""
        Compute and return the dark current noise.

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
        mean = self.dark_current

        std = np.sqrt(2 * 1.602176634e-19 * units.coulomb * self.dark_current * bandwidth)

        return np.random.normal(
            mean.to('ampere').magnitude,
            std.to('ampere').magnitude,
            size=sequence_length
        ) * units.ampere

    @validate_units(optical_power=units.watt, wavelength=units.meter)
    def get_shot_noise(self, optical_power: Quantity, wavelength: Quantity, bandwidth: Quantity) -> Quantity:
        r"""
        Computes the shot noise photocurrent arising from photon statistics.

        Shot noise is due to the discrete nature of photon arrivals. The process includes:
            1. Calculating the energy per photon.
            2. Estimating the mean number of photons arriving per sampling interval.
            3. Simulating photon counts via Poisson statistics (or a normal approximation for high counts).
            4. Converting photon counts to photocurrent using the detector responsivity.


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
        size = len(optical_power)
        # Step 1: Compute photon energy
        energy_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength  # Photon energy (J)

        # Step 2: Compute mean photon count per sampling interval
        photon_rate = optical_power / energy_photon  # Photon rate (photons/s)

        sampling_interval = 1 / (bandwidth * 2)  # Sampling interval (s)
        mean_photon_count = photon_rate * sampling_interval  # Mean photons per sample

        # Step 3: Simulate photon arrivals using Poisson statistics
        mean = mean_photon_count.to('').magnitude
        if np.max(mean) > 1e6:  # Threshold where Poisson becomes unstable
            photon_counts_distribution = np.random.normal(mean, np.sqrt(mean), size=size).astype(int)
        else:
            photon_counts_distribution = np.random.poisson(mean, size=size)


        # Step 4: Convert photon counts to photocurrent
        photon_power_distribution = photon_counts_distribution * energy_photon * (bandwidth * 2)

        photocurrent_distribution = self.responsivity * photon_power_distribution  # Current (A)

        return photocurrent_distribution

class PMT():
    def __new__(cls,
        name: str,
        phi_angle: Quantity,
        numerical_aperture: Quantity,
        responsivity: Quantity = Quantity(0.2, units.ampere / units.watt),
        dark_current: Quantity = Quantity(1e-9, units.ampere),
        **kwargs):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
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
        **kwargs):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
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
        **kwargs):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )
