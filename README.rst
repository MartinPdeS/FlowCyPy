FlowCyPy: Flow Cytometer Simulation Tool
========================================


|logo|

.. list-table::
   :widths: 10 25 25 25
   :header-rows: 0

   * - Meta
     - |python|
     - |docs|
     - |colab|
   * - Testing
     - |ci/cd|
     - |coverage|
     -
   * - PyPi
     - |PyPi|
     - |PyPi_download|
     -


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

    import numpy as np
    from FlowCyPy import FlowCytometer, Scatterer, Analyzer, Detector, Source, FlowCell
    from FlowCyPy import distribution
    from FlowCyPy import peak_finder
    from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter

    np.random.seed(3)

    flow_cell = FlowCell(
        flow_speed=7.56 * meter / second,
        flow_area=(10 * micrometer) ** 2,
        run_time=0.1 * millisecond
    )

    scatterer = Scatterer(medium_refractive_index=1.33 * RIU)

    scatterer.add_population(
        name='EV',
        concentration=2e+9 * particle / milliliter / 10,
        size=distribution.RosinRammler(
            characteristic_size=50 * nanometer,
            spread=10.5
        ),
        refractive_index=distribution.Normal(
            mean=1.45 * RIU,
            std_dev=0.02 * RIU
        )
    )

    scatterer.initialize(flow_cell=flow_cell)

    scatterer.print_properties()
    scatterer.plot()

    from FlowCyPy.units import milliwatt, AU
    source = Source(
        numerical_aperture=0.3 * AU,
        wavelength=800 * nanometer,
        optical_power=100 * milliwatt
    )

    source.print_properties()  # Print the laser source properties

    # Step 5: Configure Detectors
    # Side scatter detector
    from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz
    detector_0 = Detector(
        name='side',
        phi_angle=90 * degree,
        numerical_aperture=1.2 * AU,
        responsitivity=1 * ampere / watt,
        sampling_freq=60 * megahertz,
        saturation_level=1 * millivolt,
        n_bins='16bit',
        resistance=50 * ohm,
        dark_current=0.1 * milliampere,
        temperature=300 * kelvin
    )

    # Forward scatter detector
    detector_1 = Detector(
        name='forward',
        phi_angle=0 * degree,
        numerical_aperture=1.2 * AU,
        responsitivity=1 * ampere / watt,
        sampling_freq=60 * megahertz,
        saturation_level=1 * millivolt,
        n_bins='16bit',
        resistance=50 * ohm,
        dark_current=0.1 * milliampere,
        temperature=300 * kelvin
    )

    detector_1.print_properties()

    cytometer = FlowCytometer(
        coupling_mechanism='mie',
        source=source,
        scatterer=scatterer,
        detectors=[detector_0, detector_1]
    )

    cytometer.simulate_pulse()

    cytometer.plot()

The plot produced will resemble the following:

|example_3|

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

    pytest

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

|example_0|


Raw Signal as measured from the detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|example_1|

Peak finder analysis
~~~~~~~~~~~~~~~~~~~~

|example_2|


Scatter Density Plot
~~~~~~~~~~~~~~~~~~~~

|example_3|


Contributions
-------------

**FlowCyPy** is under active development, and contributions are highly encouraged! Feel free to reach out for collaboration opportunities or to provide feedback.


Contact Information
-------------------

As of 2024, the project is still under development. If you want to collaborate, it would be a pleasure! I encourage you to contact me.

FlowCell was written by `Martin Poinsinet de Sivry-Houle <https://github.com/MartinPdS>`_  .

Email:`martin.poinsinet.de.sivry@gmail.ca <mailto:martin.poinsinet.de.sivry@gmail.ca?subject=PyMieSim>`_ .

.. |logo| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/logo.png
    :align: middle
    :alt: FlowCyPy Logo

.. |example_0| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/master/docs/images/example_0.png
    :width: 80%

.. |example_1| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/master/docs/images/example_1.png
    :width: 80%

.. |example_2| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/master/docs/images/example_2.png
    :width: 80%

.. |example_3| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/master/docs/images/example_3.png
    :width: 80%

.. |python| image:: https://img.shields.io/pypi/pyversions/flowcypy.svg
   :target: https://www.python.org/
   :alt: Python version

.. |coverage| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/python-coverage-comment-action-data/badge.svg
   :target: https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html
   :alt: Unittest coverage

.. |PyPi| image:: https://badge.fury.io/py/FlowCyPy.svg
   :target: https://badge.fury.io/py/FlowCyPy
   :alt: PyPi

.. |PyPi_download| image:: https://img.shields.io/pypi/dm/FlowCyPy.svg
   :target: https://pypistats.org/packages/flowcypy
   :alt: PyPi download statistics

.. |docs| image:: https://github.com/martinpdes/flowcypy/actions/workflows/deploy_documentation.yml/badge.svg
   :target: https://martinpdes.github.io/FlowCyPy/
   :alt: Documentation Status

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
    :target: https://colab.research.google.com/github/MartinPdeS/FlowCyPy/blob/master/workflow.ipynb
    :alt: FlowCyPy on Google colab

.. |ci/cd| image:: https://github.com/martinpdes/flowcypy/actions/workflows/deploy_coverage.yml/badge.svg
   :target: https://martinpdes.github.io/FlowCyPy/actions
   :alt: Unittest Status