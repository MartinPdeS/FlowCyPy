Internship Tasks
-----------------

The following tasks outline your internship objectives, ensuring a systematic and practical approach to developing and validating **FlowCyPy**.

Before diving into the main tasks, you'll complete **pre-tasks** to verify your setup and understanding of the tools.

Pre-Tasks
~~~~~~~~~

1. **Environment Check**:

   - Verify that **FlowCyPy** is installed correctly by running the test suite:

     .. code-block:: bash

        python -m pytest .

     If tests fail, identify the issues, debug, and ensure all functionalities are working.

   - Run a basic example script from the `examples` folder:

     .. code-block:: bash

        cd docs/examples/tutorials
        python workflow.py

     Confirm the script executes without errors and produces expected visualizations.

2. **Familiarization**:

   - Read through the `scatterer.py`, `source.py`, and `detector.py` files to understand their roles in **FlowCyPy**.
   - Modify a simple example to:

     - Change detector noise levels and observe the signal differences.
     - Adjust laser parameters (e.g., wavelength or power) and analyze the effect on scatter signals.

   - Explore the **Examples** section in the documentation and try running at least one example.

----


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

**Mini Objectives**:

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

**Mini Objectives**:

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

**Mini Objectives**:

- Simulate a dataset with a large number of particles (e.g., \(10^6\)) and measure runtime.
- Implement a parallelized simulation and compare runtime improvements.

Stretch Goals
~~~~~~~~~~~~~

- Simulate complex particle distributions (e.g., a mixture of populations with varying refractive indices and sizes).
- Combine multiple noise sources to analyze their combined impact on detector signals.
- Extend **FlowCyPy** to simulate new detector configurations or optical setups.
- Design a new example showcasing advanced features, such as coincidence detection or real-time event analysis.

**Note**: These tasks aim to deepen your understanding of digital twins, simulation techniques, and flow cytometry, while contributing to the advancement of **FlowCyPy**.
