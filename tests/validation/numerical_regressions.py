import numpy as np
import pytest

from FlowCyPy.fluidics import FlowCell
from FlowCyPy.opto_electronics import Digitizer
from FlowCyPy.digital_processing.discriminator import FixedWindow
from FlowCyPy.units import ureg


def make_digitizer(**overrides):
    configuration = {
        "sampling_rate": 100 * ureg.megahertz,
        "bandwidth": 20 * ureg.megahertz,
        "bit_depth": 8,
        "min_voltage": -1 * ureg.volt,
        "max_voltage": 1 * ureg.volt,
        "use_auto_range": False,
    }
    configuration.update(overrides)
    return Digitizer(**configuration)


def test_digitizer_codes_are_monotonic_and_bounded():
    digitizer = make_digitizer(bit_depth=4)
    signal = np.linspace(-2, 2, 101) * ureg.volt

    codes = digitizer.digitize_signal(signal)

    assert np.all(np.diff(codes.astype(np.int64)) >= 0)
    assert codes.min() == 0
    assert codes.max() == 2**4 - 1


def test_digitization_is_invariant_to_equivalent_voltage_units():
    digitizer = make_digitizer(bit_depth=3)
    signal_volts = np.array([-1.0, -0.25, 0.0, 0.5, 1.0]) * ureg.volt
    signal_millivolts = signal_volts.to("millivolt")

    volts_codes = digitizer.digitize_signal(signal_volts)
    millivolts_codes = digitizer.digitize_signal(signal_millivolts)

    assert np.array_equal(volts_codes, millivolts_codes)


def test_digitizer_time_axis_is_uniform_and_excludes_run_time_endpoint():
    digitizer = make_digitizer(sampling_rate=4 * ureg.hertz)

    time = digitizer.get_time_series(1 * ureg.second).to("second").magnitude

    assert np.allclose(np.diff(time), 0.25)
    assert time[0] == pytest.approx(0.0)
    assert time[-1] < 1.0


def test_fixed_window_discards_trigger_without_complete_pre_buffer():
    time = np.arange(10) * ureg.second
    signal = np.zeros(10)
    signal[1:3] = 2.0

    output = FixedWindow(
        trigger_channel="detector",
        threshold=0.5 * ureg.volt,
        pre_buffer=5,
        post_buffer=2,
        max_triggers=1,
    ).run_with_dict(
        {
            "Time": time,
            "detector": signal * ureg.volt,
        }
    )

    assert len(output["Time"]) == 0


def test_flow_cell_sample_volume_is_unit_invariant():
    flow_cell = FlowCell(
        width=10 * ureg.micrometer,
        height=10 * ureg.micrometer,
        sample_volume_flow=0.3 * ureg.microliter / ureg.second,
        sheath_volume_flow=3 * ureg.microliter / ureg.second,
        viscosity=1e-3 * ureg.pascal * ureg.second,
        N_terms=25,
        n_int=200,
    )

    volume_seconds = flow_cell.get_sample_volume(2 * ureg.second)
    volume_milliseconds = flow_cell.get_sample_volume(2000 * ureg.millisecond)

    assert volume_seconds.to("microliter").magnitude == pytest.approx(
        volume_milliseconds.to("microliter").magnitude
    )
