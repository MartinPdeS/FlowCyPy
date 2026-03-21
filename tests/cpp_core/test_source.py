import math

import pytest
from pint import UnitRegistry

from FlowCyPy.opto_electronics.source import (
    Gaussian,
    AsymetricGaussian,
    FlatTop,
    AsymetricFlatTop,
)


ureg = UnitRegistry()


def test_gaussian_constructor_and_properties():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=10e-3 * ureg.watt,
        waist=1.5e-6 * ureg.meter,
        rin=-120.0,
        polarization=0.25 * ureg.radian,
    )

    assert source.wavelength.to("meter").magnitude == pytest.approx(532e-9)
    assert source.optical_power.to("watt").magnitude == pytest.approx(10e-3)
    assert source.waist.to("meter").magnitude == pytest.approx(1.5e-6)
    assert source.rin == pytest.approx(-120.0)
    assert source.polarization.to("radian").magnitude == pytest.approx(0.25)


def test_asymetric_gaussian_constructor_and_properties():
    source = AsymetricGaussian(
        wavelength=633e-9 * ureg.meter,
        optical_power=5e-3 * ureg.watt,
        waist_y=2.0e-6 * ureg.meter,
        waist_z=4.0e-6 * ureg.meter,
        rin=-110.0,
        polarization=0.0 * ureg.radian,
    )

    assert source.wavelength.to("meter").magnitude == pytest.approx(633e-9)
    assert source.optical_power.to("watt").magnitude == pytest.approx(5e-3)
    assert source.waist_y.to("meter").magnitude == pytest.approx(2.0e-6)
    assert source.waist_z.to("meter").magnitude == pytest.approx(4.0e-6)
    assert source.rin == pytest.approx(-110.0)


def test_flat_top_constructor_and_properties():
    source = FlatTop(
        wavelength=780e-9 * ureg.meter,
        optical_power=2e-3 * ureg.watt,
        waist=3.0e-6 * ureg.meter,
        rin=-100.0,
        polarization=0.1 * ureg.radian,
    )

    assert source.wavelength.to("meter").magnitude == pytest.approx(780e-9)
    assert source.optical_power.to("watt").magnitude == pytest.approx(2e-3)
    assert source.waist.to("meter").magnitude == pytest.approx(3.0e-6)
    assert source.rin == pytest.approx(-100.0)
    assert source.polarization.to("radian").magnitude == pytest.approx(0.1)


def test_asymetric_flat_top_constructor_and_properties():
    source = AsymetricFlatTop(
        wavelength=780e-9 * ureg.meter,
        optical_power=2e-3 * ureg.watt,
        waist_y=3.0e-6 * ureg.meter,
        waist_z=6.0e-6 * ureg.meter,
        rin=-100.0,
        polarization=0.0 * ureg.radian,
    )

    assert source.waist_y.to("meter").magnitude == pytest.approx(3.0e-6)
    assert source.waist_z.to("meter").magnitude == pytest.approx(6.0e-6)


def test_frequency_matches_c_over_lambda():
    wavelength = 532e-9
    source = Gaussian(
        wavelength=wavelength * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=1e-6 * ureg.meter,
    )

    expected_frequency = 299792458.0 / wavelength

    assert source.frequency.to("hertz").magnitude == pytest.approx(
        expected_frequency, rel=1e-3
    )


def test_photon_energy_matches_h_nu():
    wavelength = 532e-9
    source = Gaussian(
        wavelength=wavelength * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=1e-6 * ureg.meter,
    )

    expected_frequency = 299792458.0 / wavelength
    expected_energy = 6.62607015e-34 * expected_frequency

    assert source.photon_energy.to("joule").magnitude == pytest.approx(expected_energy)


def test_rin_linear_conversion():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=1e-6 * ureg.meter,
        rin=-120.0,
    )

    expected = 10 ** (-120.0 / 10.0)

    assert source.rin_linear.to("1 / hertz").magnitude == pytest.approx(expected)


def test_gaussian_amplitude_matches_formula_at_focus():
    wavelength = 532e-9
    optical_power = 10e-3
    waist = 2e-6

    source = Gaussian(
        wavelength=wavelength * ureg.meter,
        optical_power=optical_power * ureg.watt,
        waist=waist * ureg.meter,
    )

    epsilon_0 = 8.8541878128e-12
    c = 299792458.0
    expected_amplitude = math.sqrt(
        4.0 * optical_power / (math.pi * epsilon_0 * c * waist * waist)
    )

    assert source.amplitude.to("volt / meter").magnitude == pytest.approx(
        expected_amplitude, rel=1e-3
    )


def test_asymetric_gaussian_amplitude_matches_formula_at_focus():
    optical_power = 10e-3
    waist_y = 2e-6
    waist_z = 5e-6

    source = AsymetricGaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=optical_power * ureg.watt,
        waist_y=waist_y * ureg.meter,
        waist_z=waist_z * ureg.meter,
    )

    epsilon_0 = 8.8541878128e-12
    c = 299792458.0
    expected_amplitude = math.sqrt(
        4.0 * optical_power / (math.pi * epsilon_0 * c * waist_y * waist_z)
    )

    assert source.amplitude.to("volt / meter").magnitude == pytest.approx(
        expected_amplitude, rel=1e-3
    )


def test_gaussian_amplitude_at_center_equals_focus_amplitude():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
    )

    amplitude_at_center = source.amplitude_at(
        x=0.0 * ureg.meter,
        y=0.0 * ureg.meter,
        z=0.0 * ureg.meter,
    )

    assert amplitude_at_center.to("volt / meter").magnitude == pytest.approx(
        source.amplitude.to("volt / meter").magnitude
    )


def test_gaussian_amplitude_decays_off_axis():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
    )

    center = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=0.0 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    off_axis = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=2e-6 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    assert off_axis < center


def test_asymetric_gaussian_amplitude_decays_with_y_and_z():
    source = AsymetricGaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=2e-6 * ureg.meter,
        waist_z=4e-6 * ureg.meter,
    )

    center = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=0.0 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    off_y = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=2e-6 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    off_z = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=0.0 * ureg.meter,
            z=4e-6 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    assert off_y < center
    assert off_z < center


def test_flat_top_amplitude_is_constant_inside_support():
    source = FlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=3e-6 * ureg.meter,
    )

    center = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=0.0 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    inside = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=1e-6 * ureg.meter,
            z=1e-6 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    assert inside == pytest.approx(center)


def test_flat_top_amplitude_is_zero_outside_support():
    source = FlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=3e-6 * ureg.meter,
    )

    outside = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=4e-6 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    assert outside == pytest.approx(0.0)


def test_asymetric_flat_top_amplitude_is_constant_inside_support():
    source = AsymetricFlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=2e-6 * ureg.meter,
        waist_z=4e-6 * ureg.meter,
    )

    center = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=0.0 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    inside = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=1e-6 * ureg.meter,
            z=1e-6 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    assert inside == pytest.approx(center)


def test_asymetric_flat_top_amplitude_is_zero_outside_support():
    source = AsymetricFlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=2e-6 * ureg.meter,
        waist_z=4e-6 * ureg.meter,
    )

    outside = (
        source.amplitude_at(
            x=0.0 * ureg.meter,
            y=3e-6 * ureg.meter,
            z=0.0 * ureg.meter,
        )
        .to("volt / meter")
        .magnitude
    )

    assert outside == pytest.approx(0.0)


def test_gaussian_set_waist_updates_waist_and_amplitude():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=1e-6 * ureg.meter,
    )

    original_amplitude = source.amplitude.to("volt / meter").magnitude

    source.set_waist(2e-6 * ureg.meter)

    updated_amplitude = source.amplitude.to("volt / meter").magnitude

    assert source.waist.to("meter").magnitude == pytest.approx(2e-6)
    assert updated_amplitude < original_amplitude


def test_asymetric_gaussian_set_waist_updates_both_waists_and_amplitude():
    source = AsymetricGaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=1e-6 * ureg.meter,
        waist_z=2e-6 * ureg.meter,
    )

    original_amplitude = source.amplitude.to("volt / meter").magnitude

    source.set_waist(2e-6 * ureg.meter, 4e-6 * ureg.meter)

    updated_amplitude = source.amplitude.to("volt / meter").magnitude

    assert source.waist_y.to("meter").magnitude == pytest.approx(2e-6)
    assert source.waist_z.to("meter").magnitude == pytest.approx(4e-6)
    assert updated_amplitude < original_amplitude


def test_flat_top_set_waist_updates_waist_and_amplitude():
    source = FlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=1e-6 * ureg.meter,
    )

    original_amplitude = source.amplitude.to("volt / meter").magnitude

    source.set_waist(2e-6 * ureg.meter)

    updated_amplitude = source.amplitude.to("volt / meter").magnitude

    assert source.waist.to("meter").magnitude == pytest.approx(2e-6)
    assert updated_amplitude < original_amplitude


def test_asymetric_flat_top_set_waist_updates_waists_and_amplitude():
    source = AsymetricFlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=1e-6 * ureg.meter,
        waist_z=2e-6 * ureg.meter,
    )

    original_amplitude = source.amplitude.to("volt / meter").magnitude

    source.set_waist(2e-6 * ureg.meter, 4e-6 * ureg.meter)

    updated_amplitude = source.amplitude.to("volt / meter").magnitude

    assert source.waist_y.to("meter").magnitude == pytest.approx(2e-6)
    assert source.waist_z.to("meter").magnitude == pytest.approx(4e-6)
    assert updated_amplitude < original_amplitude


def test_particle_width_for_gaussian():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=4e-6 * ureg.meter,
    )

    width = source.get_particle_width(2.0 * ureg.meter / ureg.second)

    assert width.to("meter").magnitude == pytest.approx(1e-6)


def test_particle_width_for_asymetric_source_uses_waist_z():
    source = AsymetricGaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=4e-6 * ureg.meter,
        waist_z=8e-6 * ureg.meter,
    )

    width = source.get_particle_width(2.0 * ureg.meter / ureg.second)

    assert width.to("meter").magnitude == pytest.approx(2e-6)


def test_get_amplitude_signal_without_noise_matches_pointwise_amplitude():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
        rin=-120.0,
    )

    x = [0.0, 0.0, 0.0]
    y = [0.0, 1e-6, 2e-6]
    z = [0.0, 0.0, 0.0]

    amplitudes = source.get_amplitude_signal(
        x=x,
        y=y,
        z=z,
        bandwidth=1e6 * ureg.hertz,
        include_source_noise=False,
    )

    expected = [
        source.amplitude_at(0.0 * ureg.meter, yi * ureg.meter, 0.0 * ureg.meter)
        .to("volt / meter")
        .magnitude
        for yi in y
    ]

    assert amplitudes == pytest.approx(expected)


def test_add_rin_to_signal_preserves_length():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
        rin=-120.0,
    )

    amplitudes = [1.0, 2.0, 3.0, 4.0]

    noisy = source.add_rin_to_signal(amplitudes, 1e6 * ureg.hertz)

    assert len(noisy) == len(amplitudes)


def test_get_amplitude_signal_preserves_length():
    source = FlatTop(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
        rin=-120.0,
    )

    x = [0.0, 0.0, 0.0, 0.0]
    y = [0.0, 1e-6, 3e-6, 0.0]
    z = [0.0, 0.0, 0.0, 1e-6]

    amplitudes = source.get_amplitude_signal(
        x=x,
        y=y,
        z=z,
        bandwidth=1e6 * ureg.hertz,
        include_source_noise=False,
    )

    assert len(amplitudes) == 4


@pytest.mark.parametrize(
    "constructor_kwargs",
    [
        {
            "wavelength": -532e-9 * ureg.meter,
            "optical_power": 1e-3 * ureg.watt,
            "waist": 2e-6 * ureg.meter,
        },
        {
            "wavelength": 532e-9 * ureg.meter,
            "optical_power": -1e-3 * ureg.watt,
            "waist": 2e-6 * ureg.meter,
        },
        {
            "wavelength": 532e-9 * ureg.meter,
            "optical_power": 1e-3 * ureg.watt,
            "waist": -2e-6 * ureg.meter,
        },
    ],
)
def test_gaussian_rejects_invalid_inputs(constructor_kwargs):
    with pytest.raises(RuntimeError):
        Gaussian(**constructor_kwargs)


def test_asymetric_gaussian_rejects_invalid_waists():
    with pytest.raises(RuntimeError):
        AsymetricGaussian(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=-1e-6 * ureg.meter,
            waist_z=2e-6 * ureg.meter,
        )

    with pytest.raises(RuntimeError):
        AsymetricGaussian(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=1e-6 * ureg.meter,
            waist_z=-2e-6 * ureg.meter,
        )


def test_flat_top_rejects_invalid_waist():
    with pytest.raises(RuntimeError):
        FlatTop(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist=0.0 * ureg.meter,
        )


def test_asymetric_flat_top_rejects_invalid_waists():
    with pytest.raises(RuntimeError):
        AsymetricFlatTop(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=0.0 * ureg.meter,
            waist_z=2e-6 * ureg.meter,
        )

    with pytest.raises(RuntimeError):
        AsymetricFlatTop(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=2e-6 * ureg.meter,
            waist_z=0.0 * ureg.meter,
        )


def test_reject_negative_velocity_in_particle_width():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
    )

    with pytest.raises(RuntimeError):
        source.get_particle_width(-1.0 * ureg.meter / ureg.second)


def test_reject_negative_bandwidth_in_add_rin_to_signal():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
    )

    with pytest.raises(RuntimeError):
        source.add_rin_to_signal([1.0, 2.0], -1.0 * ureg.hertz)


def test_reject_mismatched_position_vector_sizes():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist=2e-6 * ureg.meter,
    )

    with pytest.raises(RuntimeError):
        source.get_amplitude_signal(
            x=[0.0, 0.0],
            y=[0.0],
            z=[0.0, 0.0],
            bandwidth=1e6 * ureg.hertz,
            include_source_noise=False,
        )


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
