Internal
========


.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

   internal/prerequisites/index.rst
   internal/getting_started.rst
   internal/core_components.rst
   internal/tasks.rst
   internal/ressources.rst
   examples

.. contents::
   :local:
   :depth: 0

Welcome to FlowCyPy internship documentation!
---------------------------------------------

This guide is designed to help you get started with **FlowCyPy**, a simulation tool we are developing for flow cytometry.
Over the next weeks, you will contribute to validating and extending the software while gaining a deep understanding of its core components.
We will focus on simulating realistic flow cytometry signals, implementing advanced algorithms, and comparing results with real-world experimental data.


Prerequisites
-------------
Before diving into the specifics of **FlowCyPy**, it’s essential to ensure you have a strong foundation in key areas such as programming, physics, and mathematics.
The sections on the left outline the knowledge and skills you should possess or develop to effectively work on this project.


Flow Cytometry Basics
---------------------

Flow cytometry combines fluidics, optics, and electronics to analyze particles in a stream.
Understanding the basics of Forward Scatter (FSC) and Side Scatter (SSC) principles is essential for working with FlowCyPy.

*Recommended Resource*: The first chapter of the `Flow Cytometry Basics Guide <https://biotech.ufl.edu/wp-content/uploads/2021/04/flow-cytometry-basics-guide.pdf>`_ provides an excellent overview.


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



Feedback and Questions
----------------------

For assistance, feedback, or collaboration opportunities, feel free to contact me:

- **Martin Poinsinet de Sivry-Houle**
- **Email**: `martin.poinsinet.de.sivry@gmail.com <mailto:martin.poinsinet.de.sivry@gmail.com>`_
