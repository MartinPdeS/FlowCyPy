Main Objectives
===============

This document outlines the primary objectives of the internship, emphasizing performance evaluation, simulation validation, and feature development for FlowCyPy.

------

Limit of Detection (LoD)
~~~~~~~~~~~~~~~~~~~~~~~~

**Objective**: Define, quantify, and evaluate the limit of detection in flow cytometry simulations.

- **Metric Definition**:
  - Develop a robust methodology to define the limit of detection (LoD).
  - Incorporate signal-to-noise ratio (SNR) thresholds and statistical models.

- **Noise Impact**:
  - Analyze the influence of noise sources (thermal, shot, and dark noise) on LoD.
  - Compare theoretical noise characteristics with simulated results.


.. math::

   \text{Shot Noise Variance} = 2 e I B R^2
   \\[20pt]
   \text{Thermal Noise Variance} = \frac{4 k_B T B}{R}


where:
  - :math:`e`: Elementary charge (C)
  - :math:`I`: Current (A)
  - :math:`B`: Bandwidth (Hz)
  - :math:`k_B`: Boltzmann constant (J/K)
  - :math:`T`: Temperature (K)
  - :math:`R`: Resistance (Ω)



.. admonition:: Mini Objective

  - Create plots showcasing the relationship between noise levels and LoD.
  - Assess the LoD for particles of varying sizes and refractive indices.

------

Real-Life Data Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

**Objective**: Compare simulation outputs against experimental data for validation.

- Use calibration bead datasets to benchmark the simulation.
- Validate forward and side scatter signal distributions using experimental measurements.
- Evaluate accuracy in detecting small particle populations under noisy conditions.

.. admonition:: Mini Objective

   - Simulate experimental setups using real-world parameters.
   - Quantify the deviation between simulated and experimental results.

------

Software Profiling and Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Objective**: Enhance the efficiency of FlowCyPy for large-scale simulations.

- **Profiling**:
  - Identify bottlenecks in simulation workflows using tools like `cProfile` or `line_profiler`.
  - Measure memory consumption and execution time under various conditions.

- **Optimization**:
  - Refactor core modules (e.g., `scatterer.py`, `detector.py`) for better performance.
  - Explore batch processing and parallelization techniques to handle datasets with \(10^6\) particles.

.. admonition:: Mini Objective

   - Profile a simulation with large particle counts and document runtime.
   - Implement parallel processing and compare speed improvements.

------

Feature Development
~~~~~~~~~~~~~~~~~~~

**Objective**: Expand FlowCyPy’s capabilities for advanced analyses.

- **Peak Detection**:
  - Implement and test a new algorithm for detecting peaks in low-SNR signals.
  - Compare adaptive thresholding, wavelet transforms, and other methods.

- **Particle Population Dynamics**:
  - Simulate datasets with a large number of very small particles and evaluate effects on signal characteristics.

- **Documentation**:
  - Improve the README file for clarity and usability.
  - Enhance overall documentation to include detailed examples, use cases, and API references.

.. admonition:: Mini Objective

   - Test the new peak detection algorithm on simulated low-SNR signals.
   - Simulate a bimodal distribution with very small particles and assess accuracy.

------

Expected Outcomes
~~~~~~~~~~~~~~~~~

- A clearly defined LoD metric with supporting simulations and theoretical validations.
- Robust comparisons between simulated and experimental data.
- Optimized simulation workflows capable of handling large datasets efficiently.
- A well-documented and user-friendly FlowCyPy package with enhanced features.
