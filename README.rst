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


.. include:: https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/master/docs/examples/tutorials/workflow.py
    :literal:

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
