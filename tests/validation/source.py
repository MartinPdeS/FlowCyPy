import numpy as np
import pytest
from TypedUnit import ureg

import FlowCyPy
from FlowCyPy.physical_constant import PhysicalConstant

FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging


pi = PhysicalConstant.pi
epsilon_0 = PhysicalConstant.epsilon_0
c = PhysicalConstant.c

# These imports assume your classes are defined in a module called "laser_beams"
from FlowCyPy.source import AstigmaticGaussianBeam, GaussianBeam


# GaussianBeam Tests
def test_gaussian_beam_with_numerical_aperture():
    # Parameters: 1 W laser, 500 nm wavelength, numerical_aperture=0.1
    P = 1.0 * ureg.watt  # watt
    wavelength = 500 * ureg.nanometer  # nanometers
    NA = 0.1 * ureg.AU
    beam = GaussianBeam(optical_power=P, wavelength=wavelength, numerical_aperture=NA)

    # Compute waist and expected field amplitude:
    waist = wavelength / (pi * NA)

    # Gaussian on-axis amplitude: E(0) = sqrt(4P/(pi * w0^2 * epsilon0 * c))
    expected_E = np.sqrt(4 * P / (pi * waist**2 * epsilon_0 * c)).to("volt/meter")
    computed_E = beam.calculate_field_amplitude_at_focus().to("volt/meter")

    np.testing.assert_allclose(computed_E, expected_E, rtol=1e-6)


def test_gaussian_beam_with_waist():
    # Parameters: 1 W laser, 500 nm wavelength, waist provided instead of numerical_aperture.
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    waist = wavelength / (pi * 0.1)  # equivalent to NA=0.1
    beam = GaussianBeam(
        optical_power=P, wavelength=wavelength, numerical_aperture=None, waist=waist
    )

    expected_E = np.sqrt(4 * P / (pi * waist**2 * epsilon_0 * c)).to("volt/meter")
    computed_E = beam.calculate_field_amplitude_at_focus().to("volt/meter")

    np.testing.assert_allclose(computed_E, expected_E, rtol=1e-6)


def test_gaussian_beam_invalid_inputs():
    with pytest.raises(ValueError):
        GaussianBeam(
            optical_power=1.0, wavelength=500e-9, numerical_aperture=None, waist=None
        )
    with pytest.raises(ValueError):
        GaussianBeam(
            optical_power=1.0,
            wavelength=500e-9,
            numerical_aperture=0.1,
            waist=500e-9 / (pi * 0.1),
        )


# Additional tests for amplitude_at in GaussianBeam
def test_gaussian_beam_amplitude_at_scalar():
    # Create a Gaussian beam
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    NA = 0.1 * ureg.AU
    beam = GaussianBeam(optical_power=P, wavelength=wavelength, numerical_aperture=NA)
    waist = wavelength / (pi * NA)
    E0 = beam.calculate_field_amplitude_at_focus().to("volt/meter")

    # At the center (0,0), amplitude should equal E0
    amp_center = beam.amplitude_at(0 * ureg.meter, 0 * ureg.meter).to("volt/meter")
    np.testing.assert_allclose(amp_center, E0, rtol=1e-6)

    # At an offset, using the Gaussian decay: E(x,0) = E0 * exp(-x^2/waist^2)
    y_val = 100 * ureg.nanometer
    expected_amp = E0 * np.exp(-(y_val**2) / waist**2)
    amp_offset = beam.amplitude_at(0 * ureg.meter, y_val).to("volt/meter")
    np.testing.assert_allclose(amp_offset, expected_amp, rtol=1e-6)


def test_gaussian_beam_amplitude_at_array():
    # Test with vectorized inputs
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    NA = 0.1 * ureg.AU
    beam = GaussianBeam(optical_power=P, wavelength=wavelength, numerical_aperture=NA)
    waist = wavelength / (pi * NA)
    E0 = beam.calculate_field_amplitude_at_focus().to("volt/meter")

    # Create arrays of x and y positions (in meters)
    x = np.linspace(-1e-6, 1e-6, 50) * ureg.meter
    y = np.linspace(-1e-6, 1e-6, 50) * ureg.meter
    X, Y = np.meshgrid(
        x.magnitude, y.magnitude
    )  # assume units are stored in .magnitude
    # Reapply units
    X = X * ureg.meter
    Y = Y * ureg.meter

    # Compute expected amplitude (element-wise)
    r2 = X**2 + Y**2
    expected_amp = E0 * np.exp(-(Y**2) / waist**2)
    computed_amp = beam.amplitude_at(X, Y).to("volt/meter")
    np.testing.assert_allclose(
        computed_amp.magnitude, expected_amp.magnitude, rtol=1e-6
    )


# AstigmaticGaussianBeam Tests
def test_astigmatic_beam_with_numerical_apertures():
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    NAx = 0.1 * ureg.AU
    NAy = 0.12 * ureg.AU
    beam = AstigmaticGaussianBeam(
        optical_power=P,
        wavelength=wavelength,
        numerical_aperture_z=NAx,
        numerical_aperture_y=NAy,
    )
    waist_z = wavelength / (pi * NAx)
    waist_y = wavelength / (pi * NAy)
    expected_E = np.sqrt(4 * P / (pi * waist_z * waist_y * epsilon_0 * c)).to(
        "volt/meter"
    )
    computed_E = beam.calculate_field_amplitude_at_focus().to("volt/meter")
    np.testing.assert_allclose(computed_E, expected_E, rtol=1e-6)


def test_astigmatic_beam_with_waists():
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    waist_z = wavelength / (pi * 0.1)
    waist_y = wavelength / (pi * 0.12)
    beam = AstigmaticGaussianBeam(
        optical_power=P,
        wavelength=wavelength,
        numerical_aperture_z=None,
        waist_z=waist_z,
        numerical_aperture_y=None,
        waist_y=waist_y,
    )
    expected_E = np.sqrt(4 * P / (pi * waist_z * waist_y * epsilon_0 * c)).to(
        "volt/meter"
    )
    computed_E = beam.calculate_field_amplitude_at_focus().to("volt/meter")
    np.testing.assert_allclose(computed_E, expected_E, rtol=1e-6)


def test_astigmatic_beam_invalid_inputs():
    with pytest.raises(ValueError):
        AstigmaticGaussianBeam(
            optical_power=1.0,
            wavelength=500e-9,
            numerical_aperture_z=None,
            waist_z=None,
            numerical_aperture_y=0.12,
            waist_y=None,
        )
    with pytest.raises(ValueError):
        AstigmaticGaussianBeam(
            optical_power=1.0,
            wavelength=500e-9,
            numerical_aperture_z=0.1,
            waist_z=None,
            numerical_aperture_y=0.12,
            waist_y=10,
        )


# Additional tests for amplitude_at in AstigmaticGaussianBeam
def test_astigmatic_beam_amplitude_at_scalar():
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    NAz = 0.1 * ureg.AU
    NAy = 0.12 * ureg.AU
    beam = AstigmaticGaussianBeam(
        optical_power=P,
        wavelength=wavelength,
        numerical_aperture_z=NAz,
        numerical_aperture_y=NAy,
    )
    waist_y = wavelength / (pi * NAy)
    E0 = beam.calculate_field_amplitude_at_focus().to("volt/meter")

    # At the center (0,0)
    amp_center = beam.amplitude_at(0 * ureg.meter, 0 * ureg.meter).to("volt/meter")
    np.testing.assert_allclose(amp_center, E0, rtol=1e-6)

    # At an offset (x=100 nm, y=50 nm)
    x_val = 100 * ureg.nanometer
    y_val = 50 * ureg.nanometer
    expected_amp = E0 * np.exp(-(y_val**2 / waist_y**2))
    amp_offset = beam.amplitude_at(x_val, y_val).to("volt/meter")
    np.testing.assert_allclose(amp_offset, expected_amp, rtol=1e-6)


def test_astigmatic_beam_amplitude_at_array():
    P = 1.0 * ureg.watt
    wavelength = 500 * ureg.nanometer
    NAz = 0.1 * ureg.AU
    NAy = 0.12 * ureg.AU
    beam = AstigmaticGaussianBeam(
        optical_power=P,
        wavelength=wavelength,
        numerical_aperture_z=NAz,
        numerical_aperture_y=NAy,
    )

    waist_y = wavelength / (pi * NAy)
    E0 = beam.calculate_field_amplitude_at_focus().to("volt/meter")

    x = np.linspace(-1e-6, 1e-6, 50) * ureg.meter
    y = np.linspace(-1e-6, 1e-6, 50) * ureg.meter
    X, Y = np.meshgrid(x.magnitude, y.magnitude)
    X = X * ureg.meter
    Y = Y * ureg.meter

    expected_amp = E0 * np.exp(-(Y**2 / waist_y**2))
    computed_amp = beam.amplitude_at(X, Y).to("volt/meter")
    np.testing.assert_allclose(
        computed_amp.magnitude, expected_amp.magnitude, rtol=1e-6
    )


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
