"""
Flow Cytometry Simulation: Scattering Intensities with One Population
======================================================================

This tutorial demonstrates how to simulate a flow cytometry experiment using the FlowCyPy library.
The simulation involves configuring a flow setup, defining a single population of particles, and
analyzing scattering signals from two detectors to produce a 2D density plot of scattering intensities.

Overview:
---------
1. Configure the flow cell and particle population.
2. Define the laser source and detector parameters.
3. Simulate the flow cytometry experiment.
4. Analyze the generated signals and visualize results.

"""

# %%
# Step 0: Import Necessary Libraries
# -----------------------------------
# Here, we import the necessary libraries and units for the simulation. The units module helps us
# define physical quantities like meters, seconds, and watts in a concise and consistent manner.

import numpy as np
from FlowCyPy import units


# %%
# Step 1: Configure Noise Settings
# ---------------------------------
# Noise settings are configured to simulate real-world imperfections. In this example, we include noise
# globally but exclude specific types, such as shot noise and thermal noise.

from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_dark_current = False

np.random.seed(3)  # Ensure reproducibility


# %%
# Step 2: Set Up the Flow Cell
# ----------------------------
# The flow cell models the movement of particles in the cytometer. For example, the volume of fluid
# passing through the cross-sectional area is calculated as:
#
# .. math::
#     \text{Flow Volume} = \text{Flow Speed} \times \text{Flow Area} \times \text{Run Time}

from FlowCyPy import FlowCell

flow_cell = FlowCell(
    flow_speed=7.56 * units.meter / units.second,  # Flow speed
    flow_area=(10 * units.micrometer) ** 2,       # Cross-sectional area
    run_time=0.1 * units.millisecond              # Simulation duration
)


# %%
# Step 3: Define Scatterer and Population
# ---------------------------------------
# The scatterer represents particles in the flow. The concentration of particles in the flow cell is
# given by:
#
# .. math::
#     \text{Concentration} = \frac{\text{Number of Particles}}{\text{Volume of Flow}}

from FlowCyPy import Scatterer
from FlowCyPy.population import Exosome

scatterer = Scatterer(medium_refractive_index=1.33 * units.RIU)

# Add an Exosome population
scatterer.add_population(
    Exosome,
    particle_count=5e9 * units.particle / units.milliliter  # Particle concentration
)

# Initialize the scatterer with the flow cell
scatterer.initialize(flow_cell=flow_cell)
scatterer.plot()  # Visualize the particle population

# %%
# Step 4: Configure the Laser Source
# ----------------------------------
# The laser source generates light that interacts with the particles. Its parameters, like numerical
# aperture and wavelength, affect how light scatters, governed by Mie theory.

from FlowCyPy import GaussianBeam

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,           # Numerical aperture
    wavelength=200 * units.nanometer,           # Wavelength
    optical_power=20 * units.milliwatt          # Optical power
)

# %%
# Step 5: Define Detectors
# ------------------------
# Detectors measure light intensity. Parameters like responsitivity define the conversion of optical
# power to electronic signals, and saturation level represents the maximum signal they can handle.

from FlowCyPy.detector import Detector

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=1.2 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    sampling_freq=60 * units.megahertz,
    saturation_level=10000 * units.microvolt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin,
    n_bins='14bit'
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=1.2 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    sampling_freq=60 * units.megahertz,
    saturation_level=10000 * units.microvolt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin,
    n_bins='14bit'
)

# %%
# Step 6: Simulate Flow Cytometry Experiment
# ------------------------------------------
# The FlowCytometer combines all components to simulate scattering. The interaction between light
# and particles follows Mie theory:
#
# .. math::
#     \sigma_s = \frac{2 \pi}{k} \sum_{n=1}^\infty (2n + 1) (\lvert a_n \rvert^2 + \lvert b_n \rvert^2)

from FlowCyPy import FlowCytometer

cytometer = FlowCytometer(
    source=source,
    detectors=[detector_0, detector_1],
    scatterer=scatterer,
    background_power=0.001 * units.milliwatt
)

cytometer.simulate_pulse()
cytometer.plot()  # Visualize signals from detectors

# %%
# Step 7: Analyze Detected Signals
# --------------------------------
# The MovingAverage algorithm detects peaks in signals by analyzing local maxima within a defined
# window size and threshold.
from FlowCyPy import EventCorrelator
from FlowCyPy import peak_locator

algorithm = peak_locator.MovingAverage(
    threshold=10 * units.microvolt,
    window_size=1 * units.microsecond,
    min_peak_distance=0.3 * units.microsecond
)

# Assign peak detection algorithm to detectors
detector_0.set_peak_locator(algorithm)
detector_1.set_peak_locator(algorithm)

# Analyze signal data
analyzer = EventCorrelator(cytometer=cytometer)
analyzer.run_analysis(compute_peak_area=False)

# %%
# Step 8: Visualize Coincidence and Density Plot
# ----------------------------------------------
# Coincidence analysis checks for simultaneous detection events across detectors, which are plotted
# as a 2D density graph to illustrate signal relationships between FSC and SSC.

analyzer.get_coincidence(margin=1e-9 * units.microsecond)  # Extract coincidences
analyzer.plot(log_plot=False)  # Generate a 2D density plot
