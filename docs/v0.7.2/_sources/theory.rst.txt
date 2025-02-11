Theory
======

In flow cytometry, particles suspended in a fluid stream are illuminated by a focused laser beam. As the particles pass through the laser beam, light is scattered in various directions depending on the particle's size, shape, refractive index, and other physical properties.
The scattered light is detected by one or more photodetectors, allowing the user to derive information about the particles' characteristics.

This section explains the theoretical foundation behind the main components of the **FlowCyPy** simulation package, focusing on:

- **Mie Scattering** and its phase function
- **Gaussian Illumination Source** and beam properties
- **Detection Scheme**, including forward and side scatter, and angular dependence.

Mie Scattering Theory
---------------------

For particles that are comparable to the wavelength of light, **Mie scattering** is the most appropriate theoretical framework. Unlike **Rayleigh scattering**, which assumes that particles are much smaller than the wavelength, Mie scattering accounts for particles of arbitrary size, making it applicable to a wide range of particle sizes commonly encountered in flow cytometry.

The scattered light intensity at an angle :math:`\theta` from the incident light direction is given by the **Mie scattering phase function**. The phase function describes how light is scattered as a function of angle and can be quite complex due to the internal resonances within the particle.

The **scattering cross-section** :math:`\sigma_s` quantifies the extent to which a particle scatters light and is given by:

.. math::
    \sigma_s = \frac{2 \pi}{k^2} \sum_{n=1}^{\infty} (2n + 1) \left( |a_n|^2 + |b_n|^2 \right)

Where:
- :math:`k = \frac{2 \pi}{\lambda}` is the wavenumber,
- :math:`\lambda` is the wavelength of the incident light,
- :math:`a_n` and :math:`b_n` are the Mie scattering coefficients for the electric and magnetic fields, respectively.

The Mie scattering coefficients depend on the particle's size parameter:

.. math::
    x = \frac{2 \pi r}{\lambda}

Where:
- :math:`r` is the particle radius,
- :math:`\lambda` is the wavelength of the laser beam.

Mie theory also allows us to compute the **extinction cross-section** and **backscatter cross-section**,
which are important for measuring attenuation and detecting backscatter signals in flow cytometry.

### Phase Function

The phase function describes how light is scattered as a function of angle relative to the incident light. For spherical particles, the Mie phase function can be quite complex, but it generally shows more intense forward scattering than side or backward scattering. The intensity of scattered light at an angle :math:`\theta` is:

.. math::
    I(\theta) = \frac{I_0}{k^2 r^2} \left( |S_1(\theta)|^2 + |S_2(\theta)|^2 \right)

Where:
- :math:`I_0` is the intensity of the incident light,
- :math:`r` is the radius of the particle,
- :math:`S_1(\theta)` and :math:`S_2(\theta)` are the scattering amplitudes for perpendicular and parallel polarized components, respectively.

The **scattering amplitude functions** are derived from Mie theory and involve sums over spherical harmonics and complex exponential terms. These terms account for the interaction of light with both the surface and the interior of the particle.

Gaussian Illumination Source
----------------------------

In flow cytometry, the laser beam used to illuminate particles typically has a **Gaussian intensity profile**. This means the intensity of the beam is strongest at its center and falls off gradually towards the edges. The **Gaussian beam** can be described by its **waist radius** :math:`w_0`, which defines the size of the beam at its narrowest point (the focus):

.. math::
    I(r) = I_0 \exp \left( - \frac{2 r^2}{w_0^2} \right)

Where:
- :math:`I_0` is the peak intensity at the center of the beam,
- :math:`r` is the radial distance from the beam center,
- :math:`w_0` is the waist radius of the beam.

### Beam Waist and Numerical Aperture

The **beam waist** is determined by the focusing optics and is related to the **numerical aperture (NA)** of the system, which is defined by:

.. math::
    \text{NA} = n \sin \theta

Where:
- :math:`n` is the refractive index of the medium (typically 1 for air),
- :math:`\theta` is the half-angle of the cone of light that can be captured or transmitted by the optical system.

The **beam waist** :math:`w_0` can be related to the numerical aperture and wavelength of the laser by:

.. math::
    w_0 = \frac{\lambda}{\pi \text{NA}}

For small numerical apertures, the beam waist is larger, and the focal spot of the laser is more diffuse. Conversely, for higher numerical apertures, the beam waist is smaller, resulting in a more tightly focused beam.

### Power Density and Spot Size

The power density of the Gaussian beam at the focal point (beam waist) is a critical parameter because it determines the amount of light that interacts with each particle. The power density is highest at the beam center and decreases exponentially with radial distance:

.. math::
    P_{\text{density}} = \frac{2 P_0}{\pi w_0^2} \exp \left( - \frac{2 r^2}{w_0^2} \right)

Where:
- :math:`P_0` is the total power of the laser.

Detection Scheme
----------------

In flow cytometry, detectors are placed at different angles relative to the incident laser beam to measure both **forward scatter (FSC)** and **side scatter (SSC)**. The **forward scatter** detector is typically aligned with the axis of the laser beam, while the **side scatter** detector is positioned at a 90-degree angle.

### Forward Scatter (FSC)

**Forward scatter (FSC)** is primarily sensitive to particle size. When particles pass through the focused laser beam, light is scattered predominantly in the forward direction due to the larger phase shift and constructive interference of light waves. The intensity of the forward scatter signal is proportional to the particle's cross-sectional area:

.. math::
    I_{\text{FSC}} \propto r^2

Where:
- :math:`r` is the radius of the particle.

Thus, larger particles produce stronger forward scatter signals, allowing for size differentiation in flow cytometry.

### Side Scatter (SSC)

**Side scatter (SSC)** is primarily sensitive to the internal complexity or granularity of the particle, such as cell granules or surface roughness. Side scatter arises from light being scattered at large angles (typically 90 degrees). The intensity of the side scatter signal depends on the **granularity** and refractive index mismatch between the particle and the surrounding medium. It can be empirically modeled as:

.. math::
    I_{\text{SSC}} \propto \text{granularity} \cdot \sin^n(\theta)

Where:
- :math:`\theta` is the scattering angle (typically 90 degrees),
- :math:`n` is an empirical parameter controlling the angular dependence,
- Granularity is a dimensionless measure of the particle's internal complexity.

### Detector Configuration

Detectors in flow cytometry are characterized by several important parameters:
- **Acquisition Frequency**: The rate at which the detector samples the scattered signal (e.g., 10,000 Hz).
- **Numerical Aperture (NA)**: The detector's ability to collect scattered light over a range of angles.
- **Responsitivity**: The efficiency with which the detector converts scattered light into an electrical signal.
- **Baseline Shift**: The baseline output of the detector when no particles are present.

In the **FlowCyPy** simulation, detectors can be configured to model realistic scattering detection schemes, including noise levels, saturation limits, and angular dependencies. This allows users to simulate complex experimental setups with multiple detectors at various angles.

Example Detector Configuration:

.. code-block:: python

    detector_0 = Detector(
        theta_angle=90,              # Side scatter detector
        numerical_aperture=0.4,      # Numerical aperture of the detector optics
        responsitivity=1,            # Responsitivity of the detector (efficiency)
        acquisition_frequency=1e4,   # Sampling frequency: 10,000 Hz
        noise_level=0.01,            # Noise level: 0.01 millivolts
    )

Simulating and Analyzing Flow Cytometry Data
--------------------------------------------

In the **FlowCyPy** library, the full flow cytometry experiment is simulated by configuring a `FlowCytometer` object that combines the laser source, particle distribution, and detectors. After running the simulation, the **PulseAnalyzer** can be used to extract pulse features such as peak height, width, and area, allowing for further analysis of the flow cytometry data.

Refer to the "Examples" section for complete examples of how to configure a flow cytometry experiment and analyze the resulting data.

