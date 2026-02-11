import pytest
import numpy as np
from FlowCyPy.binary.signal_generator import SignalGenerator
from FlowCyPy.units import ureg

N_ELEMENTS = 5000
TIME_ARRAY = np.linspace(0.0, 1.0, N_ELEMENTS)


def test_omp_parallel_multiply():
    signal_generator = SignalGenerator(N_ELEMENTS)
    signal_generator.add_time(TIME_ARRAY * ureg.second)
    signal_generator.create_zero_signal(channel="Signal")

    signal_generator.multiply(3.0)


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
