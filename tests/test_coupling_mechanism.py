import pytest
import numpy as np
from FlowCyPy import ScattererCollection, Detector
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import distribution
from FlowCyPy.coupling_mechanism import rayleigh
from FlowCyPy.population import Sphere
from FlowCyPy.source import GaussianBeam
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import units

@pytest.fixture
def normal_size_distribution():
    """Fixture for creating a distribution.Normal."""
    return distribution.Normal(
        mean=1.0 * units.micrometer,
        std_dev=0.1 * units.micrometer,
    )


@pytest.fixture
def normal_ri_distribution():
    """Fixture for creating a distribution.Normal."""
    return distribution.Normal(
        mean=1.5 * units.RIU,
        std_dev=0.1 * units.RIU,
    )


@pytest.fixture
def normal_population(normal_size_distribution, normal_ri_distribution):
    """Fixture for creating a Population."""
    return Sphere(
        particle_count=1e+10 * units.particle / units.milliliter,
        diameter=normal_size_distribution,
        refractive_index=normal_ri_distribution,
        name="Default population"
    )


@pytest.fixture
def default_flow_cell():
    return FlowCell(
        sample_volume_flow=1 * units.microliter / units.second,
        sheath_volume_flow=6 * units.microliter / units.second,
        width=20 * units.micrometer,
        height=10 * units.micrometer,
    )

@pytest.fixture
def signal_digitizer():
    return SignalDigitizer(
        sampling_rate=1e4 * units.hertz,           # Sampling frequency: 10,000 Hz
        bit_depth=1024,
        saturation_levels=1e30 * units.volt
    )

@pytest.fixture
def detector():
    return Detector(
        phi_angle=90 * units.degree,
        numerical_aperture=0.1 * units.AU,
        name='first detector',
        responsivity=1.0 * units.ampere / units.watt,  # Responsitivity of the detector
    )


@pytest.fixture
def scatterer_collection(normal_population):
    scatterer = ScattererCollection(medium_refractive_index=1.33 * units.RIU)
    scatterer.add_population(normal_population)
    return scatterer


@pytest.fixture
def source():
    return GaussianBeam(
        numerical_aperture=0.2 * units.AU,
        wavelength=1550 * units.nanometer,    # Wavelength of the laser source: 1550 nm
        optical_power=200 * units.milliwatt,   # Optical power of the laser source: 200 milliwatt
    )


def test_generate_scatterer_size(scatterer_collection, default_flow_cell):
    """
    Test if the sizes are generated correctly in the ScattererCollection.
    """
    scatterer_dataframe = default_flow_cell._generate_event_dataframe(
        scatterer_collection.populations,
        run_time=0.001 * units.second
    )

    scatterer_collection.fill_dataframe_with_sampling(scatterer_dataframe)

    diameters = scatterer_dataframe['Diameter']

    assert diameters is not None, "ScattererCollection sizes should be generated."
    assert len(diameters) > 0, f"Expected 10 scatterer sizes, but got {len(diameters)}."
    assert diameters.values.numpy_data.min() > 0, f"Expected all sizes to be positive, but got a minimum size of {diameters.magnitude.min()}."

def test_rayleigh_mechanism_output(detector, scatterer_collection, source, default_flow_cell):
    """
    Test the detected power output of the Rayleigh scattering mechanism.
    """
    scatterer_dataframe = default_flow_cell._generate_event_dataframe(
        scatterer_collection.populations,
        run_time=0.001 * units.second
    )

    scatterer_collection.fill_dataframe_with_sampling(scatterer_dataframe)

    detected_power = rayleigh.compute_detected_signal(
        source=source,
        detector=detector,
        scatterer_dataframe=scatterer_dataframe,
        medium_refractive_index=1.33 * units.RIU
    )

    assert detected_power is not None, "Detected power should not be None."
    assert np.all(detected_power > 0), f"Expected detected power to be positive, but got {detected_power}."

def test_digitizer_properties(signal_digitizer):
    """
    Test the detector's properties and ensure they are correctly initialized.
    """
    assert signal_digitizer.sampling_rate == 1e4 * units.hertz, f"Expected acquisition frequency to be 10,000 Hz, but got {detector.acquisition_frequency}."
    assert signal_digitizer.saturation_levels == 1e30 * units.volt, f"Expected saturation level to be 1e30, but got {detector.saturation_level}."
    assert signal_digitizer.bit_depth == 1024, f"Expected 1024 bins, but got {detector.signal_digitizer.bit_depth}."



def test_detector_properties(detector):
    """
    Test the detector's properties and ensure they are correctly initialized.
    """
    assert detector.numerical_aperture == 0.1 * units.AU, f"Expected detector numerical aperture to be 0.1, but got {detector.numerical_aperture}."
    assert detector.responsivity == 1.0 * units.ampere / units.watt, f"Expected detector responsivity to be 1.0, but got {detector.responsivity}."


def test_source_properties(source):
    """
    Test the properties of the light source to ensure they are correctly set.
    """
    assert source.numerical_aperture == 0.2 * units.AU, f"Expected source numerical aperture to be 0.2, but got {source.numerical_aperture}."
    assert source.wavelength == 1550 * units.nanometer, f"Expected source wavelength to be 1550 nm (1.55e-6 m), but got {source.wavelength}."
    assert source.optical_power == 200e-3 * units.watt, f"Expected source optical power to be 200 mW, but got {source.optical_power}."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
