import math

import pytest
from pint import UnitRegistry

from FlowCyPy.opto_electronics.source import Gaussian, FlatTop


ureg = UnitRegistry()


def test_asymetric_gaussian_constructor_and_properties():
    source = Gaussian(
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


def test_asymetric_flat_top_constructor_and_properties():
    source = FlatTop(
        wavelength=780e-9 * ureg.meter,
        optical_power=2e-3 * ureg.watt,
        waist_y=3.0e-6 * ureg.meter,
        waist_z=6.0e-6 * ureg.meter,
        rin=-100.0,
        polarization=0.0 * ureg.radian,
    )

    assert source.waist_y.to("meter").magnitude == pytest.approx(3.0e-6)
    assert source.waist_z.to("meter").magnitude == pytest.approx(6.0e-6)


def test_asymetric_gaussian_amplitude_matches_formula_at_focus():
    optical_power = 10e-3
    waist_y = 2e-6
    waist_z = 5e-6

    source = Gaussian(
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


def test_asymetric_gaussian_amplitude_decays_with_y_and_z():
    source = Gaussian(
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


def test_asymetric_flat_top_amplitude_is_constant_inside_support():
    source = FlatTop(
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
    source = FlatTop(
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


def test_asymetric_gaussian_set_waist_updates_both_waists_and_amplitude():
    source = Gaussian(
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


def test_asymetric_flat_top_set_waist_updates_waists_and_amplitude():
    source = FlatTop(
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


def test_particle_width_for_asymetric_source_uses_waist_z():
    source = Gaussian(
        wavelength=532e-9 * ureg.meter,
        optical_power=1e-3 * ureg.watt,
        waist_y=4e-6 * ureg.meter,
        waist_z=8e-6 * ureg.meter,
    )

    width = source.get_particle_width([2.0] * ureg.meter / ureg.second)

    assert width.to("second").magnitude == pytest.approx(2e-6)


def test_asymetric_gaussian_rejects_invalid_waists():
    with pytest.raises(RuntimeError):
        Gaussian(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=-1e-6 * ureg.meter,
            waist_z=2e-6 * ureg.meter,
        )

    with pytest.raises(RuntimeError):
        Gaussian(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=1e-6 * ureg.meter,
            waist_z=-2e-6 * ureg.meter,
        )


def test_asymetric_flat_top_rejects_invalid_waists():
    with pytest.raises(RuntimeError):
        FlatTop(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=0.0 * ureg.meter,
            waist_z=2e-6 * ureg.meter,
        )

    with pytest.raises(RuntimeError):
        FlatTop(
            wavelength=532e-9 * ureg.meter,
            optical_power=1e-3 * ureg.watt,
            waist_y=2e-6 * ureg.meter,
            waist_z=0.0 * ureg.meter,
        )


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
