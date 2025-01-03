"""
Flow Cytometry Simulation [2 populations] Density Plot of Scattering Intensities
================================================================================

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
from FlowCyPy import Population, distribution
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz, microvolt
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Exosome, HDL

NoiseSetting.include_noises = False

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
    run_time=.2 * millisecond              # Total simulation time: 0.3 milliseconds
)

# Step 3: Create Populations (Extracellular Vesicles and Liposomes)
scatterer = ScattererCollection(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

ri_std_dev = 0.02 * RIU
size_std_dev = 30 * nanometer

population_0 = Population(
    name='Pop 0',
    # size=distribution.RosinRammler(characteristic_size=150 * nanometer, spread=4.5),
    size=distribution.Normal(mean=650 * nanometer, std_dev=size_std_dev),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=ri_std_dev)
)

population_1 = Population(
    name='Pop 1',
    # size=distribution.Delta(position=200 * nanometer),
    size=distribution.Normal(mean=400 * nanometer, std_dev=size_std_dev),
    refractive_index=distribution.Normal(mean=1.42 * RIU, std_dev=ri_std_dev)
)

population_2 = Population(
    name='Pop 2',
    # size=distribution.Delta(position=200 * nanometer),
    size=distribution.Normal(mean=500 * nanometer, std_dev=size_std_dev),
    refractive_index=distribution.Normal(mean=1.48 * RIU, std_dev=ri_std_dev)
)

# scatterer.add_population(population_0, particle_count=100 * particle)
scatterer.add_population(population_1, particle_count=100 * particle)
scatterer.add_population(population_2, particle_count=100 * particle)

# Initialize scatterer and link it to the flow cell
flow_cell.initialize(scatterer_collection=scatterer)

scatterer.plot()

# Step 5: Configure Detectors
# Side scatter detector
detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=.2 * AU,              # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=60 * megahertz,            # Sampling frequency: 60 MHz
    saturation_level=0.04 * millivolt,       # Saturation level: 2 millivolts
    # n_bins='16bit',                        # Number of bins: 14-bit resolution
    resistance=50 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)

# Forward scatter detector
detector_1 = Detector(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=0 * degree,                    # Angle: 0 degrees (Forward Scatter)
    numerical_aperture=.2 * AU,              # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=60 * megahertz,            # Sampling frequency: 60 MHz
    saturation_level=0.04 * millivolt,       # Saturation level: 2 millivolts
    # n_bins='16bit',                        # Number of bins: 14-bit resolution
    resistance=50 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)


# Step 6: Simulate Flow Cytometry Experiment
cytometer = FlowCytometer(                   # Laser source used in the experiment
    flow_cell=flow_cell,                     # Populations used in the experiment
    background_power=0.0 * milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

# Run the simulation of pulse signals
cytometer.run_coupling_analysis()

cytometer.initialize_signal()

cytometer.simulate_pulse()

cytometer.plot_coupling_density()


# import seaborn as sns
# import matplotlib.pyplot as plt

# figure, ax = plt.subplots(1, 1)

# joint_plot = sns.jointplot(
#     data=scatterer.dataframe,
#     y='detector: side',
#     x='detector: forward',
#     hue="Population",
#     alpha=0.8,
#     ax=ax
# )

# joint_plot.ax_joint.set_xscale('log')
# joint_plot.ax_joint.set_yscale('log')

# plt.show()

