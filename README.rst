FlowCyPy: Flow Cytometer Simulation Tool
========================================

|logo|

|python| |coverage| |PyPi| |PyPi_download| |docs|

Overview
--------

**FlowCyPy** is a robust Python package designed to simulate the behavior of a flow cytometer. By simulating realistic Forward Scatter (FSC) and Side Scatter (SSC) signals—complete with noise, baseline shifts, and signal saturation—FlowCyPy provides a detailed model of flow cytometry experiments. Ideal for researchers and engineers, it offers an intuitive and configurable platform for studying scattering phenomena and detector responses in flow cytometry setups.

Features
--------

- **Particle Event Simulation**: Generate realistic FSC and SSC signals with configurable parameters.
- **Noise & Baseline Shift Modeling**: Add Gaussian noise and baseline shifts to simulate real-world experimental conditions.
- **Signal Saturation**: Simulate detector saturation to reflect real-life limitations.
- **Signal Digitization**: Discretize continuous signals into specified bins for deeper analysis.
- **Advanced Plotting**: Customize signal visualization with multi-channel plot support.
- **Fully Configurable**: Customize particle size distributions, flow parameters, and detector setups.

Installation
------------

You can easily install **FlowCyPy** via `pip`:

.. code-block:: bash

    pip install FlowCyPy

Requirements
------------

**FlowCyPy** requires Python 3.10 or higher and the following dependencies:

- `numpy`
- `scipy`
- `pint`
- `tabulate`
- `seaborn`
- `MPSPlots`
- `PyMieSim`
- `pydantic>=2.6.3`

Quick Start Example
-------------------

Below is an example of how to simulate particle events and generate flow cytometry signals using **FlowCyPy**:

.. code-block:: python

    from FlowCyPy import FlowCytometer, ScattererDistribution, Flow, Detector, Source

    # Set flow parameters
    flow = Flow(
        flow_speed=80e-6,       # Flow speed of 80 micrometers/second
        flow_area=1e-6,         # Cross-sectional area of 1 square micrometer
        total_time=8.0,         # Total time of 8 seconds
        scatterer_density=1e11  # Particle density of 1e11 particles/m^3
    )

    # Define particle distribution
    scatterer_distribution = ScattererDistribution(
        flow=flow,
        refractive_index=1.5,
        distributions=[NormalDistribution(mean=10e-6, std_dev=1e-7)]  # Particle size distribution
    )

    # Define a laser source
    source = Source(
        numerical_aperture=0.3,
        wavelength=1550e-9,     # 1550 nm laser wavelength
        optical_power=200e-3    # 200 mW optical power
    )

    # Add detectors to the flow cytometer
    detector_0 = Detector(theta_angle=90, numerical_aperture=0.4, acquisition_frequency=1e4)
    detector_1 = Detector(theta_angle=0, numerical_aperture=0.4, acquisition_frequency=1e4)

    # Create and simulate the flow cytometer
    cytometer = FlowCytometer(
        coupling_mechanism='mie',
        source=source,
        scatterer_distribution=scatterer_distribution,
        detectors=[detector_0, detector_1]
    )
    cytometer.simulate_pulse()
    cytometer.plot()

The plot produced will resemble the following:

.. image:: https://github.com/MartinPdeS/FlowCyPy/blob/master/docs/images/example_signal_FCM.png
   :alt: Example Flow Cytometry Signal

Developer Guide
---------------

For developers or contributors who want to work on **FlowCyPy**, follow the steps below to install the package locally, run tests, and build the documentation.

### 1. Clone the Repository

First, clone the repository:

.. code-block:: bash

    git clone https://github.com/MartinPdeS/FlowCyPy.git
    cd FlowCyPy

### 2. Install Locally

Install the package in editable mode along with the testing and documentation dependencies:

.. code-block:: bash

    pip install -e .[testing,documentation]

### 3. Running Tests

To run the tests, use `pytest` with coverage:

.. code-block:: bash

    pytest --cov=FlowCyPy --cov-report=html

This will generate a coverage report in `htmlcov/index.html`.

### 4. Building Documentation

To build the documentation locally using `Sphinx`, follow these steps:

.. code-block:: bash

    cd docs
    make html

Once completed, the HTML documentation will be available in the `docs/_build/html` directory.

Additional Examples
-------------------

Explore a variety of use cases and configurations in the `Examples <https://FlowCytometry.readthedocs.io/en/master/gallery/index.html>`_ section of the documentation, including:

Density Plots for Large and Small Scatterers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|example_0| |example_1|

Two-Population Scatter Density Plot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|example_2|


Three-Population Scatter Density Plot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|example_3|


Contributions
-------------

**FlowCyPy** is under active development, and contributions are highly encouraged! Feel free to reach out for collaboration opportunities or to provide feedback.


Contact Information
-------------------

As of 2024, the project is still under development. If you want to collaborate, it would be a pleasure! I encourage you to contact me.

PyMieSim was written by `Martin Poinsinet de Sivry-Houle <https://github.com/MartinPdS>`_  .

Email:`martin.poinsinet.de.sivry@gmail.ca <mailto:martin.poinsinet.de.sivry@gmail.ca?subject=PyMieSim>`_ .

.. |logo| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/logo.png
   :alt: FlowCyPy Logo
   :align: middle

.. |example_0| image:: https://github.com/MartinPdeS/FlowCyPy/blob/master/docs/images/example_density_plot.png
    :width: 45%

.. |example_1| image:: https://github.com/MartinPdeS/FlowCyPy/blob/master/docs/images/example_density_plot_small.png
    :width: 45%

.. |example_2| image:: https://github.com/MartinPdeS/FlowCyPy/blob/master/docs/images/example_density_plot_2pop.png
    :width: 100%

.. |example_3| image:: https://github.com/MartinPdeS/FlowCyPy/blob/master/docs/images/example_density_plot_3pop.png
    :width: 100%

.. |python| image:: https://img.shields.io/pypi/pyversions/flowcypy.svg
   :target: https://www.python.org/

.. |coverage| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/python-coverage-comment-action-data/badge.svg
   :alt: Coverage Badge
   :target: https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html

.. |PyPi| image:: https://badge.fury.io/py/FlowCyPy.svg
   :target: https://badge.fury.io/py/FlowCyPy

.. |PyPi_download| image:: https://img.shields.io/pypi/dm/FlowCyPy.svg
   :target: https://pypistats.org/packages/flowcypy

.. |docs| image:: https://readthedocs.org/projects/flowcytometry/badge/?version=latest
   :target: https://flowcytometry.readthedocs.io/en/latest/
