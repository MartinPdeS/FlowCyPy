"""
Flow Cytometry Simulation and 2D Density Plot of Scattering Intensities
=======================================================================

This example demonstrates how to simulate a flow cytometer using the FlowCyPy library, analyze the pulse
signals from two detectors, and plot a 2D density plot of the scattering intensities.

Flow cytometry is a technique used to analyze the physical and chemical properties of particles as they flow
through a laser beam. This script simulates the behavior of particles in a flow, models the light scattering
detected by two detectors, and visualizes the scattering intensity data in a 2D hexbin plot.

Steps in the Script:
--------------------
1. Define the flow parameters (e.g., speed, area, scatterer density).
2. Create a particle size distribution.
3. Set up a laser source and detectors.
4. Simulate the flow cytometry experiment.
5. Analyze the pulse signals from both detectors.
6. Plot a 2D density plot of the scattering intensities from the two detectors.
"""

# Import necessary libraries and modules
from FlowCyPy import FlowCytometer, ScattererDistribution, Analyzer, Detector, Source, FlowCell, Plotter
from FlowCyPy.distribution import NormalDistribution
from FlowCyPy.peak_detector import BasicPeakDetector

# Step 1: Define the Flow Parameters
flow = FlowCell(
    flow_speed=8e-6,         # 80 micrometers per second
    flow_area=1e-6,          # 1 square micrometer
    total_time=180.0,        # Total simulation time of 40 seconds
    scatterer_density=1e11   # Scatterer density of 1e11 particles per cubic meter
)

size_distribution = NormalDistribution(
    mean=10e-6,         # Mean particle size: 10 µm
    std_dev=0.8e-8,     # Standard deviation of particle size: 0.8 µm
)


refractive_index_distribution = NormalDistribution(
    mean=1.4,         # Mean particle size: 10 µm
    std_dev=0.1,     # Standard deviation of particle size: 0.8 µm
)

# %%
# Step 2: Define the Scatterer Distribution (Normal Distribution of Particle Sizes)
scatterer_distribution = ScattererDistribution(
    flow=flow,
    refractive_index=[refractive_index_distribution],  # Refractive index of the particles
    size=[size_distribution]   # Normal distribution for particle sizes
)

scatterer_distribution.plot()

# Step 3: Set up the Laser Source
source = Source(
    NA=0.3,                      # Numerical aperture of the focusing optics
    wavelength=1550e-9,          # Wavelength of the laser source: 1550 nm
    optical_power=200e-3,        # Optical power of the laser source: 200 milliwatt
)

# Step 4: Set up Detectors
detector_0 = Detector(
    phi_angle=90,              # Angle of the detector relative to the incident light beam
    NA=0.4,                      # Numerical aperture of the detector optics
    name='Side',                  # Name or identifier for this detector
    responsitivity=1,            # Responsitivity of the detector (efficiency)
    acquisition_frequency=1e4,   # Sampling frequency: 10,000 Hz
    noise_level=0e-2,            # Signal noise level: 1 millivolt
    baseline_shift=0.00,         # Baseline shift of the detector output
    saturation_level=1e30,       # Saturation level of the detector signal
    n_bins=1024                  # Discretization bins for digitizing the signal
)

detector_1 = Detector(
    phi_angle=0,               # Angle of the detector relative to the incident light beam
    NA=0.4,                      # Numerical aperture of the detector optics
    name='Front',                # Name or identifier for this detector
    responsitivity=1,            # Responsitivity of the detector (efficiency)
    acquisition_frequency=1e4,   # Sampling frequency: 10,000 Hz
    noise_level=0e-2,            # Signal noise level: 1 millivolt
    baseline_shift=0.00,         # Baseline shift of the detector output
    saturation_level=1e30,       # Saturation level of the detector signal
    n_bins=1024                  # Discretization bins for digitizing the signal
)

# Step 5: Simulate the Flow Cytometry Experiment
cytometer = FlowCytometer(
    coupling_mechanism='mie',                 # Use Mie scattering for particles
    source=source,                            # Laser source defined above
    scatterer_distribution=scatterer_distribution,  # Particle size distribution
    detectors=[detector_0, detector_1]        # List of detectors
)


# Run the simulation to generate the scattering signals
cytometer.simulate_pulse()

cytometer.plot()

# %%
# Step 6: Analyze the Pulse Signals
analyzer = Analyzer(detector_0, detector_1, algorithm=BasicPeakDetector())


# Analyze and extract data from both detectors
analyzer.run_analysis(compute_peak_area=False)

datasets = analyzer.get_coincidence_dataset(coincidence_margin=0.1)

# %%
analyzer.plot()

# Step 7: Plot the 2D Density of Scattering Intensities
plotter = Plotter(
    dataset_0=datasets[0],  # Processed data from the first detector
    dataset_1=datasets[1],  # Processed data from the second detector
)

# %%
# Plot the 2D density plot
plotter.plot()
