Internal
========


Welcome to FlowCyPy!
---------------------
This guide is designed to help you get started with **FlowCyPy**, a simulation tool we are developing for flow cytometry.
Over the next weeks, you will contribute to validating and extending the software while gaining a deep understanding of its core components.
We will focus on simulating realistic flow cytometry signals, implementing advanced algorithms, and comparing results with real-world experimental data.

Prerequisites
-------------
Before diving into the specifics of **FlowCyPy**, it’s essential to ensure you have a strong foundation in key areas such as programming, physics, and mathematics.
The sections below outline the knowledge and skills you should possess or develop to effectively work on this project.

**Programming Skills**
----------------------

A solid grasp of programming concepts and tools is crucial for contributing to the development and validation of **FlowCyPy**.
Below, we highlight the essential skills and resources to enhance your proficiency.

Python Programming
~~~~~~~~~~~~~~~~~~

Python is the backbone of **FlowCyPy**. You will need to work with advanced Python features and popular scientific libraries.
Key areas of focus include:

- Writing and understanding functions and classes, particularly within an Object-Oriented Programming (OOP) paradigm.
- Utilizing libraries such as ``numpy`` for numerical operations, ``matplotlib`` for visualization, and ``pandas`` for data manipulation.
- Debugging and troubleshooting Python scripts to identify and fix issues efficiently.

*Suggested Practice*: Enhance your skills with hands-on exercises available on `CodeChef Practice <https://www.codechef.com/practice>`_.

Git and Version Control
~~~~~~~~~~~~~~~~~~~~~~~

Version control is essential for collaborative software development.
You will use Git to manage the FlowCyPy codebase effectively. Familiarity with the following Git commands is expected:

- ``git clone``: Clone repositories to your local machine for development.
- ``git pull``: Fetch and merge changes from the remote repository.
- ``git commit``: Save changes locally with descriptive commit messages.
- ``git push``: Upload your changes to the remote repository.
- ``git branch``: Create and manage branches for new features or experimental changes.
- ``git merge``: Integrate updates from different branches.
- ``git stash``: Temporarily save changes without committing them.

*Recommended Resource*: Master Git workflows through the `Pro Git Book <https://git-scm.com/book/en/v2>`_.

**Physics and Optics**
----------------------

Understanding the principles of light scattering and flow cytometry is vital for interpreting and simulating signals in FlowCyPy.
Below are the key topics you should familiarize yourself with.

Ray Optics and Scattering
~~~~~~~~~~~~~~~~~~~~~~~~~

A strong understanding of light-particle interactions is crucial for simulating scattering phenomena accurately.
Key concepts include ray optics and Mie scattering, which describe how particles scatter light depending on their size and refractive index.

*Recommended Resources*:
- [Introduction to Optics](https://www.springer.com/gp/book/9781108428262): A comprehensive introduction to optics.
- [Mie Theory Basics](https://en.wikipedia.org/wiki/Mie_scattering): A concise overview of Mie scattering principles.

Flow Cytometry Basics
~~~~~~~~~~~~~~~~~~~~~

Flow cytometry combines fluidics, optics, and electronics to analyze particles in a stream.
Understanding the basics of Forward Scatter (FSC) and Side Scatter (SSC) principles is essential for working with FlowCyPy.

*Recommended Resource*: The first chapter of the [Flow Cytometry Basics Guide](https://biotech.ufl.edu/wp-content/uploads/2021/04/flow-cytometry-basics-guide.pdf) provides an excellent overview.

**Mathematical Background**
---------------------------

A solid foundation in mathematical concepts is critical for signal processing and data analysis within FlowCyPy.
You should be familiar with:

- Signal processing techniques, such as Fourier transforms and noise modeling, which are used to analyze and manipulate signal data.
- Probability and statistics, particularly statistical moments, for quantifying and interpreting simulated data.

By mastering these prerequisites, you will be well-prepared to dive into FlowCyPy and contribute meaningfully to its development and validation.


Overview of FlowCyPy
---------------------
**FlowCyPy** is a Python library designed to simulate the complex behavior of flow cytometry systems.
It combines advanced computational tools with a modular architecture, allowing users to model key aspects of flow cytometry experiments.
At its core, **FlowCyPy** integrates **PyMieSim** (another library we developed) to compute the scattering interactions between light and particles, enabling precise modeling of forward scatter (FSC) and side scatter (SSC) signals.


.. figure:: https://github.com/MartinPdeS/PyMieSim/raw/master/docs/images/optical_setup.png
    :alt: Optical Scattering Process
    :width: 600
    :align: center

    Optical Scattering Process


Key Features:
  - **Scattering Simulation**: Leveraging **PyMieSim**, FlowCyPy models Mie scattering to simulate light-particle interactions for realistic signal generation.
  - **Noise and Saturation Modeling**: Incorporates various noise sources (e.g., shot noise, thermal noise) and simulates detector saturation.
  - **Flow Dynamics**: Simulates particle distributions and flow behaviors through optical setups.
  - **Detectors and Signal Processing**: Models detector responses, including signal digitization and peak analysis.


.. figure:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/flow_cytometer.png
    :alt: Flow Cytometer Diagram
    :width: 600
    :align: center

    Flow Cytometer Diagram


Core Components and Getting Started
===================================

Key Components
~~~~~~~~~~~~~~

1. **Scatterer**:
   - Represents particle distributions and their optical properties.
   - Enables adding populations with defined size and refractive index distributions.
   - Simulates dynamic particle interactions within the flow cytometer.

2. **Source**:
   - Models laser sources with parameters like wavelength, optical power, and numerical aperture.
   - Simulates the illumination profile for scattering and fluorescence experiments.

3. **Detector**:
   - Emulates the response of flow cytometer detectors, including:
   - Responsitivity and resolution.
   - Noise modeling (thermal, shot noise, and dark current).
   - Signal saturation and digitization.

4. **FlowCytometer**:
   - Integrates scatterers, sources, and detectors to simulate a complete flow cytometry experiment.
   - Computes realistic Forward Scatter (FSC) and Side Scatter (SSC) signals.
   - Models optical coupling using **PyMieSim** for scattering calculations.

5. **Analyzer**:
   - Provides tools for analyzing simulated data:
   - Peak detection for particle events.
   - Signal clustering and classification.

Getting Started with FlowCyPy
-----------------------------
This section will guide you through setting up **FlowCyPy** and running simulations.

Installation
~~~~~~~~~~~~

Follow these steps to clone the repository and install dependencies:

.. code-block:: bash

  git clone https://github.com/MartinPdeS/FlowCyPy.git
  cd FlowCyPy
  python -m pip install -e .[testing, documentation] for (Windows, Linux)
  python -m pip install -e ".[testing, documentation]" for (macOS)
  python -m pytest .  # Run tests to validate the installation

Explore the Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~

Dive into the **FlowCyPy** documentation for a comprehensive guide on using its features and components:

- [FlowCyPy Documentation](https://martinpdes.github.io/FlowCyPy/)

Run Example Simulations
~~~~~~~~~~~~~~~~~~~~~~~

Explore pre-written scripts in the `examples` folder to understand the workflows.

.. code-block:: bash

  cd examples
  python example_simulation.py

Study Core Components
~~~~~~~~~~~~~~~~~~~~~

Familiarize yourself with these essential files in the repository:
- `scatterer.py`: Manages particle distributions and optical properties.
- `source.py`: Defines laser characteristics.
- `detector.py`: Handles detector configurations and signal processing.
- `flow_cytometer.py`: Combines all components to simulate flow cytometry experiments.

Internship Tasks
-----------------
As part of your internship, you will focus on the following:

1. **Validation**:
   - Compare simulated noise sources (thermal, dark current, shot noise) against theoretical models and experimental data.
   - Perform simulations using standard calibration beads and validate results with real-world measurements.

2. **Feature Improvements**:
   - Enhance peak detection algorithms for low-SNR signals.
   - Implement classification features to identify particle populations.

3. **Performance Optimization**:
   - Profile simulation performance and improve runtime for large datasets.

Learning Resources
------------------

- **FlowCyPy**: [Code Examples](https://martinpdes.github.io/FlowCyPy/docs/v1.3.2/examples.html)
- **PyMieSim**: [Code Examples](https://martinpdes.github.io/PyMieSim/docs/v3.1.0.6/index.html)
- **PyMieSim**: [Research Article](https://opg.optica.org/optcon/fulltext.cfm?uri=optcon-2-3-520&id=526697)

Feedback and Questions
----------------------

For assistance, feedback, or collaboration opportunities, feel free to contact me:

- **Martin Poinsinet de Sivry-Houle**
- **Email**: `martin.poinsinet.de.sivry@gmail.com <mailto:martin.poinsinet.de.sivry@gmail.com>`_
