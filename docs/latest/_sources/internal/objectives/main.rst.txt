Main Tasks
~~~~~~~~~~

Validation
**********

**Objective**: Ensure that simulated outputs align with theoretical expectations and experimental data.

- **Noise Validation**:

  - Simulate individual noise sources (thermal noise, dark current, shot noise).
  - Compare their statistical properties (mean, variance) with theoretical models.

.. math::

   \text{Shot Noise Variance} = 2 e I B R^2
   \\[20pt]
   \text{Thermal Noise Variance} = \frac{4 k_B T B}{R}

Where:

  - :math:`e`: Elementary charge (coulomb)
  - :math:`I`: Current (ampere)
  - :math:`B`: Bandwidth (hertz)
  - :math:`k_B`: Boltzmann constant (joule / kelvin)
  - :math:`T`: Temperature (kelvin)
  - :math:`R`: Resistance (ohm)

- **Experimental Validation**:

  - Use calibration bead data to simulate forward and side scatter signals.
  - Compare simulated scatter patterns with real-world experimental measurements.

.. admonition:: Mini Objective

  - Create plots comparing simulated and theoretical noise distributions.
  - Simulate a flow cytometer with real-world bead populations and validate signal intensities.


Feature Improvements
********************

**Objective**: Enhance and expand **FlowCyPy**'s functionality.

- **Peak Detection**:

  - Improve the performance of peak detection algorithms for low-SNR signals by experimenting with:

    - Adaptive thresholds
    - Smoothing techniques
    - Alternative detection methods (e.g., wavelet transforms)

  - Evaluate the algorithm's accuracy using simulated datasets.

- **Classification**:

  - Develop and test classification methods to distinguish particle populations based on scatter and signal data.
  - Implement feature extraction techniques (e.g., signal amplitude, pulse width) for better accuracy.

.. admonition:: Mini Objective

  - Test peak detection on low-SNR signals and compare different algorithms.
  - Simulate a bimodal population and assess the accuracy of classification methods.

---

Performance Optimization
************************

**Objective**: Optimize **FlowCyPy** for efficiency when processing large datasets.

- **Profiling**:
  - Profile the simulation workflow to identify bottlenecks using tools like `cProfile` or `line_profiler`.
  - Measure memory usage and execution time for different simulation parameters.

- **Optimization**:
  - Refactor key functions in `scatterer.py` and `detector.py` for better performance.
  - Experiment with batch processing or parallelization for large datasets.

.. admonition:: Mini Objective

  - Simulate a dataset with a large number of particles (e.g., \(10^6\)) and measure runtime.
  - Implement a parallelized simulation and compare runtime improvements.
