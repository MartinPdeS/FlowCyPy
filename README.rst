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
     - |colab|
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

For full documentation and examples, visit the `FlowCyPy Documentation <https://martinpdes.github.io/FlowCyPy/docs/latest/index.html>`_.

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

    from TypedUnit import ureg
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # %%
    # Step 1: Define Flow Cell and Fluidics
    # -------------------------------------
    from FlowCyPy.flow_cell import FlowCell
    from FlowCyPy.fluidics import Fluidics, ScattererCollection, distribution, population

    flow_cell = FlowCell(
        sample_volume_flow=80 * ureg.microliter / ureg.minute,
        sheath_volume_flow=1 * ureg.milliliter / ureg.minute,
        width=200 * ureg.micrometer,
        height=100 * ureg.micrometer,
    )

    scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * ureg.RIU)

    population_0 = population.Sphere(
        name="Pop 0",
        particle_count=5e9 * ureg.particle / ureg.milliliter,
        diameter=distribution.RosinRammler(150 * ureg.nanometer, spread=30),
        refractive_index=distribution.Normal(1.44 * ureg.RIU, std_dev=0.002 * ureg.RIU),
    )

    population_1 = population.Sphere(
        name="Pop 1",
        particle_count=5e9 * ureg.particle / ureg.milliliter,
        diameter=distribution.RosinRammler(200 * ureg.nanometer, spread=30),
        refractive_index=distribution.Normal(1.44 * ureg.RIU, std_dev=0.002 * ureg.RIU),
    )

    scatterer_collection.add_population(population_0, population_1)

    scatterer_collection.dilute(factor=30)

    fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

    # %%
    # Step 2: Define Optical Subsystem
    # --------------------------------
    from FlowCyPy.opto_electronics import (
        Detector,
        OptoElectronics,
        TransimpedanceAmplifier,
        source,
    )

    source = source.GaussianBeam(
        numerical_aperture=0.1 * ureg.AU,
        wavelength=450 * ureg.nanometer,
        optical_power=200 * ureg.milliwatt,
        RIN=-140,
    )

    detectors = [
        Detector(
            name="forward",
            phi_angle=0 * ureg.degree,
            numerical_aperture=0.3 * ureg.AU,
            responsivity=1 * ureg.ampere / ureg.watt,
        ),
        Detector(
            name="side",
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.3 * ureg.AU,
            responsivity=1 * ureg.ampere / ureg.watt,
        ),
    ]

    amplifier = TransimpedanceAmplifier(
        gain=10 * ureg.volt / ureg.ampere,
        bandwidth=10 * ureg.megahertz,
        voltage_noise_density=0.1 * ureg.nanovolt / ureg.sqrt_hertz,
        current_noise_density=0.2 * ureg.femtoampere / ureg.sqrt_hertz,
    )

    opto_electronics = OptoElectronics(
        detectors=detectors, source=source, amplifier=amplifier
    )


    # %%
    # Step 3: Signal Processing Configuration
    # ---------------------------------------
    from FlowCyPy.signal_processing import (
        Digitizer,
        SignalProcessing,
        circuits,
        peak_locator,
        triggering_system,
    )

    digitizer = Digitizer(
        bit_depth="14bit", saturation_levels="auto", sampling_rate=60 * ureg.megahertz
    )

    analog_processing = [
        circuits.BaselineRestorator(window_size=10 * ureg.microsecond),
        circuits.BesselLowPass(cutoff=2 * ureg.megahertz, order=4, gain=2),
    ]

    triggering = triggering_system.DynamicWindow(
        trigger_detector_name="forward",
        threshold=10 * ureg.microvolt,
        pre_buffer=20,
        post_buffer=20,
        max_triggers=-1,
    )

    peak_algo = peak_locator.GlobalPeakLocator(compute_width=False)

    signal_processing = SignalProcessing(
        digitizer=digitizer,
        analog_processing=analog_processing,
        triggering_system=triggering,
        peak_algorithm=peak_algo,
    )

    # %%
    # Step 4: Run Simulation
    # ----------------------
    from FlowCyPy import FlowCytometer

    cytometer = FlowCytometer(
        opto_electronics=opto_electronics,
        fluidics=fluidics,
        signal_processing=signal_processing,
        background_power=0.001 * ureg.milliwatt,
    )

    run_record = cytometer.run(run_time=1.5 * ureg.millisecond)

    # %%
    # Step 5: Plot Events and Raw Analog Signals
    # ------------------------------------------
    _ = run_record.events.plot(
        x="Diameter",
        y="RefractiveIndex",
        show=False,
        save_as=f"{dir_path}/../images/readme_events.png",
    )

|readme_events|


..  code-block:: python

    # %%
    # Plot raw analog signals
    # -----------------------
    _ = run_record.plot_analog(
        figure_size=(12, 8),
        show=False,
        save_as=f"{dir_path}/../images/readme_analog.png",
    )

|readme_analog|


..  code-block:: python

    # %%
    # Step 6: Plot Triggered Analog Segments
    # --------------------------------------
    _ = run_record.plot_digital(
        figure_size=(12, 8),
        show=False,
        save_as=f"{dir_path}/../images/readme_digital.png",
    )

|readme_digital|

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

    - **Documentation**: Full guide and API reference at `FlowCyPy Documentation <https://martinpdes.github.io/FlowCyPy/docs/latest/index.html>`_
    - **Examples**: Explore use cases in the `Examples Section <https://martinpdes.github.io/FlowCyPy/gallery/index.html>`_
    - **GitHub Repository**: Access the source code and contribute at `FlowCyPy GitHub <https://martinpdes.github.io/FlowCyPy/>`_

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

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
    :alt: Google Colab
    :target: https://colab.research.google.com/github/MartinPdeS/FlowCyPy/blob/master/notebook.ipynb

.. |readme_events| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/readme_events.png
    :width: 600px
    :align: middle
    :alt: Readme Events

.. |readme_analog| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/readme_analog.png
    :width: 600px
    :align: middle
    :alt: Readme Analog

.. |readme_digital| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/readme_digital.png
    :width: 600px
    :align: middle
    :alt: Readme Digitalç
