FlowCytometer Simulation Tool
=============================

|python|

Overview
--------

The **FlowCytometer Simulation Tool** is a Python-based simulation framework designed to replicate the operation of a flow cytometer. It generates realistic raw signals for Forward Scatter (FSC) and Side Scatter (SSC) channels, incorporating noise, baseline shifts, signal saturation, and signal discretization into a specified number of bins. This tool is highly configurable, allowing users to simulate a wide range of scenarios and analyze the resulting signals.

Features
--------

- **Simulate Particle Events**: Generate realistic FSC and SSC signals based on user-defined particle event parameters.
- **Noise and Baseline Shift**: Introduce Gaussian noise and sinusoidal baseline shifts to simulate real-world conditions.
- **Signal Saturation**: Apply saturation effects to replicate detector limits.
- **Signal Discretization**: Discretize the continuous signal into a specified number of bins for quantized signal analysis.
- **Flexible Plotting**: Visualize the simulated signals with customizable options for plotting specific channels or both together.

Installation
------------

To install the `FlowCytometer` simulation tool, you can clone the repository and install the required dependencies:

.. code-block:: bash

    git clone https://github.com/yourusername/flowcytometry.git
    cd FlowCytometry
    pip install .[testing]

Dependencies
------------

- `numpy`: For numerical operations and signal generation.
- `matplotlib`: For plotting the simulated signals.
- `scipy`: A module to generate Gaussian pulses (part of this package or an external dependency).

Getting Started
---------------

Below is a quick guide on how to get started with the `FlowCytometer` simulation tool.


.. code-block:: python

    from FlowCytometry import FlowCytometer

    cytometer = FlowCytometer(
        n_events=30,
        time_points=1000,
        noise_level=30,
        baseline_shift=0.01,
        saturation_level=10_000,
        n_bins=40,
    )

    # Simulate the flow cytometer signals
    cytometer.simulate_pulse()

    # Plot the generated signals
    cytometer.plot()

This produce the following figure:
|example_fcm|

.. |python| image:: https://img.shields.io/pypi/pyversions/pyoptik.svg
   :target: https://www.python.org/

.. |example_fcm| image:: https://github.com/MartinPdeS/FlowCytometry/blob/master/docs/images/example_signal_FCM.png

.. |coverage| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCytometry/python-coverage-comment-action-data/badge.svg
   :alt: Unittest coverage
   :target: https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCytometry/blob/python-coverage-comment-action-data/htmlcov/index.html
