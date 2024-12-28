Core Components
===============

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