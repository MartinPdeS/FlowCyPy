|logo|

FlowCyPy: Flow Cytometer Simulation Tool
========================================

.. list-table::
   :widths: 10 25 25 25
   :header-rows: 0

   * - Meta
     - |python|
     - |docs|
     -
   * - Testing
     - |ci/cd|
     - |coverage|
     -
   * - PyPi
     - |PyPi|
     - |PyPi_download|
     -
   * - Anaconda
     - |anaconda|
     - |anaconda_download|
     - |anaconda_date|

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

..  code-block:: python

    import numpy as np
    from FlowCyPy import Detector, FlowCytometer, ScattererCollection, FlowCell, units, NoiseSetting, GaussianBeam, SignalDigitizer
    from FlowCyPy.population import Exosome, Population, distribution

    NoiseSetting.include_noises = True

    source = GaussianBeam(
        numerical_aperture=0.3 * units.AU,
        wavelength=200 * units.nanometer,
        optical_power=20 * units.milliwatt
    )

    flow_cell = FlowCell(
        source=source,
        volume_flow=0.3 * units.microliter / units.second,
        flow_area=(10 * units.micrometer) ** 2,
    )

    scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

    exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

    custom_population = Population(
        name='Pop 0',
        particle_count=5e9 * units.particle / units.milliliter,
        size=distribution.RosinRammler(characteristic_size=150 * units.nanometer, spread=30),
        refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
    )

    scatterer_collection.add_population(exosome, custom_population)

    scatterer_collection.dilute(factor=4)

    scatterer_collection.plot()

    signal_digitizer = SignalDigitizer(
        bit_depth='14bit',
        saturation_levels='auto',
        sampling_freq=60 * units.megahertz,
    )

    detector_0 = Detector(
        name='forward',
        phi_angle=0 * units.degree,
        numerical_aperture=1.2 * units.AU,
        responsitivity=1 * units.ampere / units.watt,
        resistance=50 * units.ohm,
        temperature=300 * units.kelvin
    )

    detector_1 = Detector(
        name='side',
        phi_angle=90 * units.degree,
        numerical_aperture=1.2 * units.AU,
        responsitivity=1 * units.ampere / units.watt,
        resistance=50 * units.ohm,
        temperature=300 * units.kelvin,
    )

    cytometer = FlowCytometer(
        scatterer_collection=scatterer_collection,
        signal_digitizer=signal_digitizer,
        detectors=[detector_0, detector_1],
        flow_cell=flow_cell,
        background_power=0.001 * units.milliwatt
    )

    acquisition = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    acquisition.scatterer.plot(
        x='side',
        y='forward'
    )

    acquisition.analog.plot()

    triggered_acquisition = acquisition.run_triggering(
        threshold=0.2 * units.millivolt,
        trigger_detector_name='forward',
        max_triggers=35,
        pre_buffer=64,
        post_buffer=64
    )

    triggered_acquisition.analog.plot()

Explore more examples in the `FlowCyPy Examples <https://martinpdes.github.io/FlowCyPy/gallery/index.html>`_.



Code structure
--------------

Here is the architecture for a standard workflow using FlowCyPy:


|arch|



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

    pip install -e .[testing,documentation] (on linux system)
    pip install -e ".[testing,documentation]" (on macOS system)

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

.. |arch| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/architecture.png
    :align: middle
    :alt: FlowCyPy Logo

.. |python| image:: https://img.shields.io/pypi/pyversions/flowcypy.svg
    :alt: Python
    :target: https://www.python.org/

.. |docs| image:: https://github.com/martinpdes/flowcypy/actions/workflows/deploy_documentation.yml/badge.svg
    :target: https://martinpdes.github.io/FlowCyPy/
    :alt: Documentation Status

.. |PyPi| image:: https://badge.fury.io/py/FlowCyPy.svg
    :alt: PyPi version
    :target: https://badge.fury.io/py/FlowCyPy

.. |PyPi_download| image:: https://img.shields.io/pypi/dm/FlowCyPy?style=plastic&label=PyPi%20downloads&labelColor=hex&color=hex
   :alt: PyPI - Downloads
   :target: https://pypistats.org/packages/flowcypy

.. |coverage| image:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/python-coverage-comment-action-data/badge.svg
    :alt: Unittest coverage
    :target: https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html

.. |ci/cd| image:: https://github.com/martinpdes/flowcypy/actions/workflows/deploy_coverage.yml/badge.svg
    :alt: Unittest Status

.. |anaconda| image:: https://anaconda.org/martinpdes/flowcypy/badges/version.svg
   :alt: Anaconda version
   :target: https://anaconda.org/martinpdes/flowcypy

.. |anaconda_download| image:: https://anaconda.org/martinpdes/flowcypy/badges/downloads.svg
   :alt: Anaconda downloads
   :target: https://anaconda.org/martinpdes/flowcypy

.. |anaconda_date| image:: https://anaconda.org/martinpdes/flowcypy/badges/latest_release_relative_date.svg
    :alt: Latest release date
    :target: https://anaconda.org/martinpdes/flowcypy
