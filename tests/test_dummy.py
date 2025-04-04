import pytest

def test_before_hand():
    import numpy
    from FlowCyPy.binary.interface_core import FlowCyPySim

    a = numpy.linspace(0, 1)

    FlowCyPySim(a, a, a, a, 2)


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
