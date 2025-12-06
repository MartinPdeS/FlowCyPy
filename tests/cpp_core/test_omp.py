import pytest
import numpy as np
from FlowCyPy.binary.signal_generator import SIGNALGENERATOR

N_ELEMENTS = 5000
TIME_ARRAY = np.linspace(0.0, 1.0, N_ELEMENTS)


def test_omp_parallel_multiply():
    signal_generator = SIGNALGENERATOR(N_ELEMENTS)
    signal_generator._cpp_add_signal("Time", TIME_ARRAY)
    signal_generator.create_zero_signal(signal_name="Signal")

    signal_generator._cpp_multiply(3.0)


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
