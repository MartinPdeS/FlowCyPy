# FlowCyPy: Intern Onboarding Guide

## Welcome to FlowCyPy!

This guide is designed to help you get started with **FlowCyPy**, a powerful simulation tool for flow cytometry. Over the next month, you will contribute to validating and extending the software while gaining a deep understanding of its core components.

## Prerequisites

To work effectively with FlowCyPy, you should have the following foundational knowledge and skills:

### **Programming Skills**
- **Python Programming**:
  - Familiarity with Python 3.x, including:
    - Object-Oriented Programming (OOP)
    - Working with libraries such as `numpy`, `matplotlib`, and `pandas`
  - **Recommended Resource**: [Python Official Documentation](https://docs.python.org/3/)
- **Git and Version Control**:
  - Basics of Git: cloning repositories, creating branches, and committing changes
  - **Recommended Resource**: [Pro Git Book](https://git-scm.com/book/en/v2)

### **Physics and Optics**
- **Ray Optics and Scattering**:
  - Fundamental understanding of ray optics, Mie scattering, and the interaction of light with particles.
  - **Recommended Resources**:
    - [Introduction to Optics](https://www.springer.com/gp/book/9781108428262)
    - [Mie Theory Basics](https://en.wikipedia.org/wiki/Mie_scattering)
- **Flow Cytometry Basics**:
  - Overview of how flow cytometers work, including FSC and SSC principles.
  - **Recommended Resource**: [Flow Cytometry Guide by Thermo Fisher](https://www.thermofisher.com)

### **Software Knowledge**
- **Scientific Libraries**:
  - Familiarity with `pandas`, `scipy`, and `seaborn` for data manipulation and visualization.
- **Numerical Simulations**:
  - Basic understanding of simulation workflows in Python.

### **Mathematical Background**
- Knowledge of:
  - Signal processing (e.g., Fourier transforms, noise modeling)
  - Probability and statistics for analyzing simulated data

---

## Overview of FlowCyPy

**FlowCyPy** is a Python library for simulating flow cytometry signals, including forward scatter (FSC) and side scatter (SSC) signals. It models:

- Particle interactions with light (e.g., scattering and fluorescence).
- Detector responses, including noise, saturation, and digitization.
- Flow dynamics, particle distributions, and optical system configurations.

### **Key Components**
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

---

## Getting Started with FlowCyPy

### **Installation**
Clone the repository and install dependencies:
```bash
git clone https://github.com/MartinPdeS/FlowCyPy.git
cd FlowCyPy
pip install -e .[testing,documentation]
```

### **Explore the Documentation**
Review the online documentation for detailed guidance on using FlowCyPy's components:
- [FlowCyPy Documentation](https://martinpdes.github.io/FlowCyPy/)

### **Run Example Simulations**
Navigate to the `examples` folder and execute some pre-written scripts to understand the workflows:
```bash
cd examples
python example_simulation.py
```

### **Study Core Components**
Familiarize yourself with the following files in the repository:
- **`scatterer.py`**: Defines particle properties and distributions.
- **`detector.py`**: Models the detector response.
- **`flow_cytometer.py`**: Combines scatterers, detectors, and sources for simulations.

---

## Tasks for the Internship

- Validate simulated noise with experimental data.
- Simulate standard bead calibrations and compare results with real-world measurements.
- Improve peak detection algorithms for low-SNR signals.

---

## Learning Resources

### **Tutorials**
- Python for Scientific Computing: [SciPy Tutorials](https://scipy-lectures.org/)
- Data Analysis with Pandas: [Pandas Guide](https://pandas.pydata.org/pandas-docs/stable/getting_started/overview.html)

### **Research Papers**
- *"Principles of Flow Cytometry"* - *Cytometry Part A*
- *"Mie Scattering Simulation for Flow Cytometry"* - *Journal of Biophotonics*

---

## Feedback and Questions

If you have questions or suggestions during your work with FlowCyPy, please reach out to the project maintainer:

- **Martin Poinsinet de Sivry-Houle**
- **Email**: [martin.poinsinet.de.sivry@gmail.com](mailto:martin.poinsinet.de.sivry@gmail.com)
