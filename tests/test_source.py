import pytest
from PyMieSim.units import watt, meter, degree, volt, AU
from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.source import GaussianBeam, AstigmaticGaussianBeam


def test_GaussianBeam_initialization():
    """
    Test the initialization and calculations of the GaussianBeam class.
    """
    # Define test parameters for a basic Gaussian beam
    optical_power = 1 * watt  # 1 W power
    wavelength = 532e-9 * meter  # 532 nm (green laser)
    numerical_aperture = 0.1 * AU  # Small numerical aperture
    polarization = 0 * degree  # Linear polarization

    # Initialize the GaussianBeam object
    beam = GaussianBeam(
        optical_power=optical_power,
        wavelength=wavelength,
        numerical_aperture=numerical_aperture,
        polarization=polarization
    )

    # Assert waist calculation is correct
    expected_waist = beam.wavelength / (PhysicalConstant.pi * beam.numerical_aperture)
    assert beam.waist.units == expected_waist.units, "Waist should have correct units"
    assert abs(beam.waist - expected_waist) < 1e-12 * meter, "Calculated waist does not match expected value"

    # Assert electric field amplitude is calculated correctly
    amplitude = beam.calculate_field_amplitude_at_focus()
    assert amplitude.units == volt / meter, "Amplitude should be in volts per meter"
    assert amplitude > 0, "Amplitude should be positive"


def test_astigmatic_gaussian_beam_initialization():
    """
    Test the initialization and calculations of the AstigmaticGaussianBeam class.
    """
    # Define test parameters for an astigmatic beam
    optical_power = 1 * watt  # 1 W power
    wavelength = 532e-9 * meter  # 532 nm (green laser)
    numerical_aperture_x = 0.15 * AU  # NA in x-direction
    numerical_aperture_y = 0.1 * AU  # NA in y-direction
    polarization = 0 * degree  # Linear polarization

    # Initialize the AstigmaticGaussianBeam object
    beam = AstigmaticGaussianBeam(
        optical_power=optical_power,
        wavelength=wavelength,
        numerical_aperture_x=numerical_aperture_x,
        numerical_aperture_y=numerical_aperture_y,
        polarization=polarization
    )

    # Calculate expected waists
    expected_waist_x = wavelength / (PhysicalConstant.pi * numerical_aperture_x)
    expected_waist_y = wavelength / (PhysicalConstant.pi * numerical_aperture_y)

    # Assert that the calculated waists match the expected values
    assert beam.waist_x.units == expected_waist_x.units, "Waist_x should have correct units"
    assert abs(beam.waist_x - expected_waist_x) < 1e-12 * meter, "Calculated waist_x does not match expected value"

    assert beam.waist_y.units == expected_waist_y.units, "Waist_y should have correct units"

    assert abs(beam.waist_y - expected_waist_y) < 1e-12 * meter, "Calculated waist_y does not match expected value"

    # Assert electric field amplitude at focus is calculated correctly
    amplitude = beam.calculate_field_amplitude_at_focus()

    assert amplitude.units == volt / meter, "Amplitude should be in volts per meter"
    assert amplitude > 0, "Amplitude should be positive"


def test_validate_astygmatic_equal_gaussian():
    optical_power = 1 * watt  # 1 W power
    wavelength = 532e-9 * meter  # 532 nm (green laser)
    numerical_aperture = 0.15 * AU  # NA in x-direction
    polarization = 0 * degree  # Linear polarization

    # Initialize the AstigmaticGaussianBeam object
    beam_0 = AstigmaticGaussianBeam(
        optical_power=optical_power,
        wavelength=wavelength,
        numerical_aperture_x=numerical_aperture,
        numerical_aperture_y=numerical_aperture,
        polarization=polarization
    )

    beam_1 = GaussianBeam(
        optical_power=optical_power,
        wavelength=wavelength,
        numerical_aperture=numerical_aperture,
        polarization=polarization
    )

    assert beam_0.waist_y == beam_0.waist_x == beam_1.waist, "Mismatch between two equivalent beam definitions"


def test_invalid_units():
    """
    Test that invalid units raise appropriate validation errors.
    """
    optical_power = 1 * watt  # Valid power
    wavelength = 532e-9 * meter  # Valid wavelength
    numerical_aperture_y = 0.1 * AU  # Valid NA

    # Attempt to create GaussianBeam with invalid wavelength unit
    with pytest.raises(ValueError):
        GaussianBeam(optical_power=optical_power, wavelength=532 * watt, numerical_aperture=0.1, polarization=0 * degree)

    # Attempt to create AstigmaticGaussianBeam with invalid numerical aperture units
    with pytest.raises(ValueError):
        AstigmaticGaussianBeam(
            optical_power=optical_power,
            wavelength=wavelength,
            numerical_aperture_x=-0.1 * AU,  # Invalid NA (negative)
            numerical_aperture_y=numerical_aperture_y
        )

    # Attempt to create AstigmaticGaussianBeam with NA greater than 1
    with pytest.raises(ValueError):
        AstigmaticGaussianBeam(
            optical_power=optical_power,
            wavelength=wavelength,
            numerical_aperture_x=1.5,  # Invalid NA (>1)
            numerical_aperture_y=numerical_aperture_y
        )


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
