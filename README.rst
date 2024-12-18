FlowCyPy: Flow Cytometer Simulation Tool
========================================

|logo|

Overview
--------

**FlowCyPy** is a cutting-edge Python library designed to simulate flow cytometer experiments. By generating realistic Forward Scatter (FSC) and Side Scatter (SSC) signals, FlowCyPy enables detailed modeling of flow cytometry setups, making it ideal for researchers and engineers working with extracellular vesicles (EVs) or other scatterers.

Key Features
------------

- **Particle Event Simulation**: Create detailed FSC/SSC signals with customizable particle size and refractive index distributions.
- **Noise and Signal Modeling**: Incorporate realistic noise sources (thermal, shot, dark current) and baseline shifts.
- **Detector Configurations**: Simulate real-world detector behaviors, including saturation and responsivity.
- **Fluorescence Modeling**: Simulate fluorescence signals for labeled particles (e.g., EV surface markers).
- **Visualization Tools**: Generate advanced plots, including density maps and signal traces.

For full documentation and examples, visit the `FlowCyPy Documentation <https://martinpdes.github.io/FlowCyPy/>`_.

Installation
------------

Install FlowCyPy via `pip` or `conda``:

.. code-block:: bash

    pip install FlowCyPy
    conda install FlowCyPy --channels MartinPdeS

**Requirements**: Python 3.10 or higher with dependencies:
`numpy`, `scipy`, `pint`, `tabulate`, `seaborn`, `MPSPlots`, `PyMieSim`, `pydantic>=2.6.3`

Quick Start
-----------

Simulate a simple flow cytometer experiment:

.. code-block:: python

    from FlowCyPy import FlowCytometer, Scatterer, FlowCell
    from FlowCyPy.units import particle, liter, nanometer, RIU

    # Define the flow cell
    flow_cell = FlowCell(
        flow_speed=1.0, flow_area=10e-6, run_time=0.01
    )

    # Define scatterer properties
    scatterer = Scatterer(medium_refractive_index=1.33 * RIU)
    scatterer.add_population(
        name='EVs',
        concentration=1e9 * particle / liter,
        size=distribution.Normal(mean=100 * nanometer, std_dev=20 * nanometer),
        refractive_index=distribution.Normal(mean=1.45 * RIU, std_dev=0.01 * RIU)
    )
    scatterer.initialize(flow_cell=flow_cell)

    # Simulate the cytometer signals
    cytometer = FlowCytometer(
        scatterer=scatterer,
        source=source,
        detectors=[detector_fsc, detector_ssc]
    )
    cytometer.simulate_pulse()
    cytometer.plot()

Explore more examples in the `FlowCyPy Examples <https://martinpdes.github.io/FlowCyPy/gallery/index.html>`_.

Development and Contribution
-----------------------------

Clone the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    git clone https://github.com/MartinPdeS/FlowCyPy.git
    cd FlowCyPy

Install Locally
~~~~~~~~~~~~~~~

Install in editable mode with testing and documentation dependencies:

.. code-block:: bash

    pip install -e .[testing,documentation]

Run Tests
~~~~~~~~~

Use `pytest` to validate functionality:

.. code-block:: bash

    pytest

Build Documentation
~~~~~~~~~~~~~~~~~~~

Build the documentation locally:

.. code-block:: bash

    cd docs
    make html

Find the documentation in `docs/_build/html`.

Additional Resources
--------------------

- **Documentation**: Full guide and API reference at `FlowCyPy Documentation <https://martinpdes.github.io/FlowCyPy/>`_
- **Examples**: Explore use cases in the `Examples Section <https://martinpdes.github.io/FlowCyPy/gallery/index.html>`_

Contributions
-------------

Contributions are welcome! If you have suggestions, issues, or would like to collaborate, visit the `GitHub repository <https://github.com/MartinPdeS/FlowCyPy>`_.

Contact
-------

For inquiries or collaboration, contact `Martin Poinsinet de Sivry-Houle <mailto:martin.poinsinet.de.sivry@gmail.com>`_.

.. |logo| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/logo.png
    :align: middle
    :alt: FlowCyPy Logo
