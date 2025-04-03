import pytest

def test_before_hand():
    from FlowCyPy.binary.interface_core import create_array

    create_array()


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
