from typing import Optional
import numpy as np
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy.binary.interface_signal_generator import SignalGenerator
from PyMieSim.units import Quantity
from FlowCyPy import units
from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy import helper
from FlowCyPy.simulation_settings import SimulationSettings


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
        ranges include 0.4-0.7 A/W for silicon-based detectors and 0.8-0.9 A/W for InGaAs-based
        detectors.
    dark_current : Quantity, optional
        The dark current of the detector (in amperes). Default is 0 A. Typical values are in the
        range of 1-100 nA.
    gamma_angle : Quantity, optional
        The complementary (longitudinal) angle of incidence, if applicable (in degrees).
        Default is 0°.
    sampling : Quantity, optional
        The number of spatial sampling points defining the detector's resolution. Default is 100 AU.
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

    def _transform_coupling_power_to_current(self, signal_generator: SignalGenerator, bandwidth: Quantity, wavelength: Quantity) -> Quantity:
        """
        Converts the coupling power (in watts) to voltage using the detector's responsivity.

        Parameters
        ----------
        signal_generator : SignalGenerator
            The signal generator instance used to apply the conversion.
        wavelength : Quantity
            The wavelength of the incident light (in meters).
        bandwidth : Quantity
            The bandwidth of the signal (in Hz).

        Returns
        -------
        Quantity
            The resulting voltage signal (in volts).
        """
        # Step 1: Add shot noise to optical power if enabled
        if SimulationSettings.include_shot_noise or SimulationSettings.include_noises:
            self.apply_shot_noise(signal_generator=signal_generator, wavelength=wavelength, bandwidth=bandwidth)

        # Step 2: Convert optical power to current using the responsivity
        signal_generator.multiply(
            signal_name=self.name,
            factor=self.responsivity
        )

    def apply_dark_current_noise(self, signal_generator: SignalGenerator, bandwidth: Quantity) -> Quantity:
        r"""
        Compute and return the dark current noise.

        Parameters
        ----------
        signal_generator : SignalGenerator
            The signal generator instance used to apply noise to the signal.
        bandwidth : Quantity
            The bandwidth of the signal (in Hz).

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
        std_noise = np.sqrt(2 * 1.602176634e-19 * units.coulomb * self.dark_current * bandwidth)

        signal_generator.apply_gaussian_noise(
            signal_name=self.name,
            mean=self.dark_current,
            standard_deviation=std_noise
        )

    def _get_optical_power_to_photon_factor(self, wavelength: Quantity, bandwidth: Quantity) -> Quantity:
        """
        Computes the conversion factor from optical power to photon count.

        This factor is derived from the energy of a single photon and the optical power.

        Parameters
        ----------
        bandwidth : Quantity
            The bandwidth of the signal (in Hz).
        wavelength : Quantity
            The wavelength of the incident light (in meters).

        Returns
        -------
        Quantity
            The conversion factor from optical power to photon count (in 1/watt).
        """
        # Step 1: Compute photon energy
        energy_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength

        # Step 2: Compute mean photon count per sampling interval
        sampling_interval = 1 / (bandwidth * 2)  # Sampling interval (s)

        optical_power_to_photo_count_conversion_factor = (sampling_interval / energy_photon).to('1 / watt')  # Conversion factor (1/W)
        return optical_power_to_photo_count_conversion_factor

    def _get_photon_count_to_current_factor(self, wavelength: Quantity, bandwidth: Quantity) -> Quantity:
        """
        Computes the conversion factor from photon count to current.

        This factor is derived from the energy of a single photon and the detector's responsivity.

        Parameters
        ----------
        wavelength : Quantity
            The wavelength of the incident light (in meters).
        bandwidth : Quantity
            The bandwidth of the signal (in Hz).

        Returns
        -------
        Quantity
            The conversion factor from photon count to current (in amperes).
        """
        # Step 1: Compute photon energy
        energy_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength

        # Step 2: Convert photon counts to photocurrent
        photon_to_power_factor =  energy_photon * (bandwidth * 2)

        # Step 3: Convert power to current using the detector's responsivity
        power_to_current_factor = self.responsivity

        return photon_to_power_factor * power_to_current_factor  # Current (A)

    @helper.validate_input_units(optical_power=units.watt, wavelength=units.meter)
    def apply_shot_noise(self, signal_generator: SignalGenerator, wavelength: Quantity, bandwidth: Quantity) -> Quantity:
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
        signal_generator : SignalGenerator
            The signal generator instance used to apply noise to the signal.
        signal : pd.Series
            The raw signal data series (used to infer the number of samples).
        optical_power : Quantity
            The incident optical power on the detector (in watts).
        wavelength : Quantity
            The wavelength of the incident light (in meters).

        Returns
        -------
        Quantity
            The shot noise-added current distribution (in current).
        """
        optical_power_to_photo_count_conversion = self._get_optical_power_to_photon_factor(
            wavelength=wavelength,
            bandwidth=bandwidth
        )

        signal_generator.multiply(
            signal_name=self.name,
            factor=optical_power_to_photo_count_conversion
        )

        signal_generator.apply_poisson_noise(signal_name=self.name)


        signal_generator.multiply(
            signal_name=self.name,
            factor=1 / optical_power_to_photo_count_conversion
        )

from FlowCyPy._detector_instances import *