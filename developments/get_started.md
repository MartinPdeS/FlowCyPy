FlowCyPy: Intern Onboarding Guide
=================================


Welcome to FlowCyPy!
---------------------
This guide is designed to help you get started with **FlowCyPy**, a simulation tool we are developing for flow cytometry.
Over the next weeks, you will contribute to validating and extending the software while gaining a deep understanding of its core components.

Prerequisites
-------------
To work effectively with FlowCyPy, you should have the following foundational knowledge and skills:

**Programming Skills**
- Python Programming:

  - Proficiency in Python 3.x, including:

    - Writing and understanding functions and classes (Object-Oriented Programming).
    - Working with popular libraries such as `numpy`, `matplotlib`, and `pandas`.
    - Debugging and troubleshooting Python scripts.

  - Suggested Practice: [CodeChef Practice](https://www.codechef.com/practice)

- Git and Version Control:
  - Familiarity with Git commands, such as:
    - `git clone`: Clone repositories to your local machine.
    - `git pull`: Fetch and merge changes from a remote repository.
    - `git commit`: Save changes locally with meaningful commit messages.
    - `git push`: Upload your commits to a remote repository.
    - `git branch`: Create and manage branches for new features or experiments.
    - `git merge`: Integrate changes from one branch into another.
    - `git stash`: Temporarily save changes without committing.

  - Recommended Resource: [Pro Git Book](https://git-scm.com/book/en/v2)

**Physics and Optics**
- Ray Optics and Scattering:

  - Fundamental understanding of ray optics, Mie scattering, and the interaction of light with particles.
  - Recommended Resource:

    - [Introduction to Optics](https://www.springer.com/gp/book/9781108428262)
    - [Mie Theory Basics](https://en.wikipedia.org/wiki/Mie_scattering)

- Flow Cytometry Basics:
  - Overview of how flow cytometers work, including FSC and SSC principles.
  - Recommended Resource: [Flow Cytometry Guide by Thermo Fisher](https://www.thermofisher.com)

**Software Knowledge**
- Scientific Libraries:
  - Familiarity with `pandas`, `scipy`, and `seaborn` for data manipulation and visualization.
- Numerical Simulations:
  - Basic understanding of simulation workflows in Python.

**Mathematical Background**
- Knowledge of:
  - Signal processing (e.g., Fourier transforms, noise modeling).
  - Probability and statistics for analyzing simulated data.

Overview of FlowCyPy
---------------------
**FlowCyPy** is a Python library designed to simulate the complex behavior of flow cytometry systems. It combines state-of-the-art computational tools with a modular architecture, allowing users to model key aspects of flow cytometry experiments. At its core, **FlowCyPy** integrates **PyMieSim** to compute the scattering interactions between light and particles, enabling precise modeling of forward scatter (FSC) and side scatter (SSC) signals.

<div style="text-align: center;">
  <img src="https://github.com/MartinPdeS/PyMieSim/raw/master/docs/images/optical_setup.png" alt="Optical Scattering Process" width="600">
  <p><strong>Figure:</strong> The physical scattering process simulated by FlowCyPy.</p>
</div>

Key Features:
- **Scattering Simulation**: Leveraging **PyMieSim**, FlowCyPy models Mie scattering to simulate light-particle interactions for realistic signal generation.
- **Noise and Saturation Modeling**: Incorporates various noise sources (e.g., shot noise, thermal noise) and simulates detector saturation.
- **Flow Dynamics**: Simulates particle distributions and flow behaviors through optical setups.
- **Detectors and Signal Processing**: Models detector responses, including signal digitization and peak analysis.



<div style="text-align: center;">
  <img src="https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/flow_cytometer.png" alt="Optical Scattering Process" width="600">
  <p><strong>Figure:</strong> Diagram of a flow cytometer used in experiments.</p>
</div>

### Key Components

1. **Scatterer**:
   - Models particle distributions and their optical properties.
   - Allows adding populations with specific size and refractive index distributions.

2. **Source**:
   - Simulates laser sources with defined wavelength, power, and numerical aperture.

3. **Detector**:
   - Models the behavior of flow cytometer detectors, including noise, responsitivity, and resolution.

4. **FlowCytometer**:
   - Combines scatterers, sources, and detectors to simulate complete flow cytometry experiments.

5. **Analyzer**:
   - Tools for analyzing simulated signals, including peak detection and clustering.

Getting Started with FlowCyPy
-----------------------------
Follow these steps to set up FlowCyPy and start working on your tasks.

### Installation

Clone the repository and install dependencies:

```
  >>> git clone https://github.com/MartinPdeS/FlowCyPy.git
  >>> cd FlowCyPy
  >>> python -m pip install -e .[testing, documentation] for (windows, linux)
  >>> python -m pip install -e ".[testing, documentation]" for (macOS)
```

### Explore the Documentation

Review the online documentation for detailed guidance on using FlowCyPy's components:

- [FlowCyPy Documentation](https://martinpdes.github.io/FlowCyPy/)

### Run Example Simulations

Navigate to the `examples` folder and execute some pre-written scripts to understand the workflows:


```
  >>> cd examples
  >>> python example_simulation.py
```

### Study Core Components

Familiarize yourself with the following files in the repository:
- `scatterer.py`: Defines particle properties and distributions.
- `detector.py`: Models the detector response.
- `flow_cytometer.py`: Combines scatterers, detectors, and sources for simulations.

Tasks for the Internship
-------------------------
- Validate simulated noise sources with experimental data (thermal noise, dark current noise, shot noise).
- Simulate standard bead calibrations and compare results with real-world measurements.
- Improve peak detection algorithms for low-SNR signals.

Learning Resources
------------------
Below are additional resources to help you understand the scientific and technical concepts behind FlowCyPy:

### Tutorials

- **FlowCyPy:** [code examples](https://martinpdes.github.io/FlowCyPy/docs/v1.3.2/examples.html)
- **PyMieSim:** [code examples](https://martinpdes.github.io/PyMieSim/docs/v3.1.0.6/index.html)
- **PyMieSim:** [article](https://opg.optica.org/optcon/fulltext.cfm?uri=optcon-2-3-520&id=526697)


Feedback and Questions
----------------------
If you have questions or suggestions during your work with FlowCyPy, please reach out to me:

- **Martin Poinsinet de Sivry-Houle**
- **Email**: `martin.poinsinet.de.sivry@gmail.com <mailto:martin.poinsinet.de.sivry@gmail.com>`_
