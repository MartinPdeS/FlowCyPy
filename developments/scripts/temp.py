"""
2 populations
=============

This example simulates a flow cytometer experiment using the FlowCyPy library,
analyzes pulse signals from two detectors, and generates a 2D density plot of the scattering intensities.

Steps:
1. Set flow parameters and particle size distributions.
2. Set up the laser source and detectors.
3. Simulate the flow cytometry experiment.
4. Analyze pulse signals and generate a 2D density plot.
"""

# Import necessary libraries and modules
import numpy as np
from FlowCyPy import FlowCytometer, ScattererCollection, EventCorrelator, Detector, GaussianBeam, FlowCell
from FlowCyPy import peak_locator
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, ohm, kelvin, milliampere, megahertz, microvolt, millivolt
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Exosome, HDL

NoiseSetting.include_noises = False
NoiseSetting.include_shot_noise = False
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_RIN_noise = False

# Set random seed for reproducibility
np.random.seed(3)

# %%
# Step 1: Set up the Laser GaussianBeam
source = GaussianBeam(
    numerical_aperture=0.3 * AU,             # Numerical aperture of the laser: 0.3
    wavelength=488 * nanometer,              # Laser wavelength: 800 nanometers
    optical_power=100 * milliwatt             # Laser optical power: 10 milliwatts
)

# Step 2: Define Flow Parameters
flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * meter / second,      # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,      # Flow area: 10 x 10 micrometers
)

# Step 3: Create Populations (Extracellular Vesicles and Liposomes)
scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

exosome = Exosome(particle_count=3e8 * particle / milliliter)
hdl = HDL(particle_count=5e9 * particle / milliliter)

scatterer_collection.add_population(exosome)
# scatterer_collection.add_population(hdl)

# scatterer_collection.plot()

# %%
# Step 5: Configure Detectors
# Side scatter detector
signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz

)

detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    signal_digitizer=signal_digitizer,
    resistance=1500 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)

# Forward scatter detector
detector_1 = Detector(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=0 * degree,                    # Angle: 0 degrees (Forward Scatter)
    numerical_aperture=.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    signal_digitizer=signal_digitizer,
    resistance=1500 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)

# Step 6: Simulate Flow Cytometry Experiment
cytometer = FlowCytometer(                      # Laser source used in the experiment
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,                     # Populations used in the experiment
    background_power=0.0 * milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

# Run the simulation of pulse signals
triggered_acquisition = cytometer.get_triggered_acquisition(
    run_time=0.2 * millisecond,
    threshold=0.00001 * millivolt,
    pre_buffer=64,
    post_buffer=64,
    trigger_detector_name='forward',
    maximum_number_of_triggers=4
)


# triggered_acquisition.plot.signals()

triggered_acquisition.detect_peaks()

triggered_acquisition.plot.statistiques(
    x_detector='side',
    y_detector='forward'
)

# print(triggered_acquisition.dataframe)
# print(data.xs('forward').Signal.plot())
# Plot the results from both detectors
# experiment.plot.scatterer()


