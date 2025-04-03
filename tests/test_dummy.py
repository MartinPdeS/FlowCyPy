from PyMieSim import experiment
import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, TransimpedanceAmplifier
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import distribution
from FlowCyPy.population import Sphere
from FlowCyPy import units
from FlowCyPy import peak_locator
from FlowCyPy import circuits

# ----------------- FIXTURES -----------------


@pytest.fixture
def amplifier():
    return TransimpedanceAmplifier(
        gain=100 * units.volt / units.ampere,
        bandwidth=10 * units.megahertz
    )

@pytest.fixture
def default_digitizer():
    """Fixture for creating a default signal digitizer."""
    return SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=5e6 * units.hertz,
    )

@pytest.fixture
def detector_0():
    """Fixture for creating the first default detector."""
    return Detector(
        name='default',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def detector_1():
    """Fixture for creating the second default detector."""
    return Detector(
        name='default_bis',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def source():
    return GaussianBeam(
        numerical_aperture=0.1 * units.AU,
        wavelength=1550 * units.nanometer,
        optical_power=100e-3 * units.watt,
    )

@pytest.fixture
def flow_cell():
    """Fixture for creating a default flow cell."""

    return FlowCell(
        sample_volume_flow=1 * units.microliter / units.second,
        sheath_volume_flow=6 * units.microliter / units.second,
        width=10 * units.micrometer,
        height=6 * units.micrometer,
    )

@pytest.fixture
def diameter_distribution():
    """Fixture for creating a normal size distribution."""
    return distribution.Normal(
        mean=1.0 * units.micrometer,
        std_dev=0.1 * units.micrometer
    )

@pytest.fixture
def ri_distribution():
    """Fixture for creating a normal refractive index distribution."""
    return distribution.Normal(
        mean=1.5 * units.RIU,
        std_dev=0.1 * units.RIU
    )

@pytest.fixture
def population(diameter_distribution, ri_distribution):
    """Fixture for creating a default population."""
    return Sphere(
        particle_count=110 * units.particle,
        diameter=diameter_distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

@pytest.fixture
def scatterer_collection(population):
    """Fixture for creating a scatterer collection with a default population."""
    scatterer = ScattererCollection()
    scatterer.add_population(population)
    return scatterer

@pytest.fixture
def flow_cytometer(detector_0, detector_1, scatterer_collection, flow_cell, source, amplifier, default_digitizer):
    """Fixture for creating a default Flow Cytometer."""
    return FlowCytometer(
        source=source,
        transimpedance_amplifier=amplifier,
        signal_digitizer=default_digitizer,
        scatterer_collection=scatterer_collection,
        detectors=[detector_0, detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

# ----------------- UNIT TESTS -----------------


def test_before_hand_1():
    SIZE = 4
    source = experiment.source.PlaneWave.build_sequential(
        total_size=SIZE,
        polarization=0 * units.degree,
        amplitude = 1 * units.volt / units.meter,
        wavelength=500 * units.nanometer
    )

    sphere = experiment.scatterer.Sphere.build_sequential(
        total_size=SIZE,
        source=source,
        diameter=[100, 200, 300, 400] * units.nanometer,
        property=1.44 * units.RIU,
        medium_property=1.1 * units.RIU
    )

    detector = experiment.detector.Photodiode(
        NA=[0.2, 0.2, 0.2, 0.2] * units.AU,
        phi_offset=[0, 0, 0, 0] * units.degree,
        gamma_offset=[0, 0, 0, 0] * units.degree,
        cache_NA=[0, 0, 0, 0] * units.AU,
        sampling=[100, 100, 100, 100] * units.AU,
        mode_number=['NC00', 'NC00', 'NC00', 'NC00'],
        polarization_filter=[np.nan, np.nan, np.nan, np.nan] * units.degree,
        rotation=[0, 0, 0, 0] * units.degree
    )

    setup = experiment.Setup(
        source=source,
        scatterer=sphere,
        detector=detector
    )

    setup.get_sequential('coupling')


def test_flag(flow_cytometer, flow_cell, scatterer_collection):
    from FlowCyPy.coupling_mechanism import mie
    run_time = 0.2 * units.millisecond

    scatterer_dataframe = flow_cell._generate_event_dataframe(
        scatterer_collection.populations,
        run_time=run_time
    )

    scatterer_collection.fill_dataframe_with_sampling(scatterer_dataframe)

    res = mie.compute_detected_signal(
        source=flow_cytometer.source,
        detector=flow_cytometer.detectors[0],
        scatterer_dataframe=scatterer_dataframe,
        medium_refractive_index=1.0 * units.RIU
    )

    print(res )


def test_flow_cytometer_acquisition(flow_cytometer):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    flow_cytometer.prepare_acquisition(run_time=0.2 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()

    # signal = acquisition.analog['Signal']

    # assert not np.all(signal == 0 * units.volt), "Acquisition signal is all zeros."
    # assert np.std(signal) > 0 * units.volt, "Acquisition signal variance is zero, indicating no noise added."



if __name__ == '__main__':
    pytest.main(["-W error", __file__])
