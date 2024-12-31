Core Components
===============

**FlowCyPy** provides a modular framework to simulate key elements of a flow cytometry system. Below are its core components, their attributes, and functionalities. For more details, refer to the `API Reference <https://martinpdes.github.io/FlowCyPy/docs/latest/code.html>`_.

Scatterer
---------
The **Scatterer** represents particle distributions and their interactions with light.

- **Attributes**:

  - `populations`: List of particle populations, each with size and refractive index distributions.
  - `medium_refractive_index`: Refractive index of the surrounding medium (e.g., water).
  - `dataframe`: Contains particle data, including size, refractive index, and time of arrival.

- **Key Features**:

  - Add populations with `add_population(name, size, refractive_index, concentration)`.
  - Initialize the scatterer using `initialize(flow_cell)`.
  - Visualize particle distributions with `plot()`.

Source
------
The **Source** models the laser used for illumination in flow cytometry.

- **Attributes**:

  - `wavelength`: Wavelength of the laser (e.g., 800 nm).
  - `optical_power`: Power of the laser beam (e.g., 20 mW).
  - `numerical_aperture`: Numerical aperture defining the beam's focus.

- **Key Features**:

  - Simulates the laser profile for scattering calculations.
  - Models coherent light sources using Gaussian beam theory.

Detector
--------
The **Detector** emulates the response of flow cytometer detectors.

- **Attributes**:

  - `phi_angle`: Angle of detection relative to the beam (e.g., forward or side scatter).
  - `responsitivity`: Sensitivity of the detector (e.g., current per unit power).
  - `saturation_level`: Maximum signal level the detector can handle.
  - `noise_levels`: Configurable noise types (thermal, shot, dark current).
  - `dataframe`: Stores raw and processed signal data.

- **Key Features**:

  - Add various noise models using `NoiseSetting`.
  - Simulate digitization with configurable bit-depth (e.g., 12-bit, 14-bit).
  - Visualize signal data using `plot()`.

FlowCytometer
-------------
The **FlowCytometer** integrates all components to simulate a complete flow cytometry experiment.

- **Attributes**:

  - `scatterer`: The scatterer object defining particle distributions.
  - `source`: The laser source illuminating particles.
  - `detectors`: List of detectors for signal acquisition.
  - `background_power`: Ambient light contribution.

- **Key Features**:

  - Combines the scatterer, source, and detectors for realistic simulations.
  - Computes Forward Scatter (FSC) and Side Scatter (SSC) signals.
  - Uses **PyMieSim** for accurate scattering computations.

EventCorrelator
---------------
The **EventCorrelator** (previously called Analyzer) provides tools for signal analysis and particle event detection.

- **Attributes**:

  - `cytometer`: The associated FlowCytometer object.
  - `coincidence_dataframe`: Stores data for coinciding signals across detectors.
  - `algorithm`: Peak detection algorithm for identifying particle events.

- **Key Features**:

  - Detect peaks in signals using customizable algorithms (e.g., MovingAverage).
  - Correlate events between detectors to identify coincidences.
  - Generate 2D density plots of Forward Scatter (FSC) and Side Scatter (SSC) signals.

Example Use Cases
-----------------

- Simulate a scatterer with two distinct populations to analyze overlapping signals.
- Configure detectors with high noise to study the effect on signal clarity.
- Use EventCorrelator to investigate coincidence events in a multi-detector setup.

For further details on classes and methods, visit the `API Reference <https://martinpdes.github.io/FlowCyPy/docs/latest/code.html>`_.
