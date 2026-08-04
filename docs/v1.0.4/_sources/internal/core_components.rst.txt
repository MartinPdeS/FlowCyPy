Core components
===============

FlowCyPy models a simulation as four cooperating layers:

* ``fluidics`` defines the flow cell, particle populations, concentrations,
  and population-resolved event blocks.
* ``opto_electronics`` converts those events into detector signals through the
  configured source, detectors, amplifier, and digitizer.
* ``digital_processing`` detects and characterizes events in the sampled
  traces.
* ``FlowCytometer`` and ``Workflow`` connect the layers into a complete run.

Particle populations are stored in a
``ScattererCollection``. Add a population with
``collection.add_population(population)`` and adjust all concentrations with
``collection.dilute(factor)``. Population constructors use the explicit
``concentration`` keyword and distribution objects for physical properties.

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

  - `fluidics`: The fluidics object defining particle distributions and flow.
  - `source`: The laser source illuminating particles.
  - `detectors`: List of detectors for signal acquisition.
  - `background_power`: Ambient light contribution.

- **Key Features**:

  - Combines the fluidics, source, and detectors for realistic simulations.
  - Computes Forward Scatter (FSC) and Side Scatter (SSC) signals.
  - Uses **PyMieSim** for accurate scattering computations.

Digital processing
------------------
The **DigitalProcessing** layer provides tools for signal analysis and
particle event detection.

- **Attributes**:

  - `discriminator`: Peak/event trigger algorithm.
  - `peak_algorithm`: Algorithm used to characterize detected peaks.

- **Key Features**:

  - Detect peaks in signals using customizable algorithms (e.g., MovingAverage).
  - Correlate detector channels through the event collection helpers.
  - Generate population distributions and signal visualizations.

For class-level details, see the :doc:`../code` API reference.
