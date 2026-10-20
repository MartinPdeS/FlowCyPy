Theory
======

In flow cytometry, particles suspended in a fluid stream are illuminated by a focused laser beam. As the particles pass through the laser beam, light is scattered in various directions depending on the particle's size, shape, refractive index, and other physical properties.
The scattered light is detected by one or more photodetectors, allowing the user to derive information about the particles' characteristics.

This section explains the theoretical foundation behind the main components of the **FlowCyPy** simulation package, focusing on:

- **Mie Scattering** and its phase function
- **Gaussian Illumination Source** and beam properties
- **Detection Scheme**, including forward and side scatter, and angular dependence
- **Acquisition**, including population sampling, waveform digitization, triggering, and event analysis.

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

Phase Function
^^^^^^^^^^^^^^

The phase function describes how light is scattered as a function of angle relative to the incident light. For spherical particles, the Mie phase function can be quite complex, but it generally shows more intense forward scattering than side or backward scattering. The intensity of scattered light at an angle :math:`\theta` is:

.. math::
    I(\theta, R) = \frac{I_0}{k^2 R^2} \left( |S_1(\theta)|^2 + |S_2(\theta)|^2 \right)

Where:
- :math:`I_0` is the intensity of the incident light,
- :math:`R` is the distance from the particle to the observation point,
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

Beam Waist and Numerical Aperture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Power Density and Spot Size
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a beam with total optical power :math:`P_0`, the power density (intensity) at the focal plane is highest at the center and decreases with radial distance :math:`r`:

.. math::
    P_{\text{density}} = \frac{2 P_0}{\pi w_0^2} \exp \left( - \frac{2 r^2}{w_0^2} \right)

Here :math:`w_0` is the beam-waist radius. At the center, the peak power density is :math:`2P_0/(\pi w_0^2)`, so focusing the same laser power into a smaller waist increases the peak intensity. The spot diameter is often quoted as the :math:`1/e^2` intensity diameter:

.. math::
    d_{1/e^2} = 2 w_0

At a radial distance :math:`r = w_0`, the intensity has fallen to :math:`e^{-2}` (about 13.5%) of its peak value. Stating the spot-size convention matters when comparing laser specifications, since some sources report a radius while others report a diameter.

Detection Scheme
----------------

In flow cytometry, detectors are placed at different angles relative to the incident laser beam to measure both **forward scatter (FSC)** and **side scatter (SSC)**. The **forward scatter** detector is typically aligned with the axis of the laser beam, while the **side scatter** detector is positioned at a 90-degree angle.

Forward Scatter (FSC)
^^^^^^^^^^^^^^^^^^^^^

**Forward scatter (FSC)** is primarily sensitive to particle size. When particles pass through the focused laser beam, light is scattered predominantly in the forward direction due to the larger phase shift and constructive interference of light waves. As a rough geometric intuition, the forward scatter signal can increase with the particle's cross-sectional area:

.. math::
    I_{\text{FSC}} \propto r^2

Where:
- :math:`r` is the radius of the particle.

Thus, larger particles often produce stronger forward scatter signals, which can help distinguish particle sizes. This is a qualitative trend rather than a universal :math:`r^2` law: the response also depends on the Mie size parameter, refractive indices, wavelength, and detector collection geometry.

Side Scatter (SSC)
^^^^^^^^^^^^^^^^^^

**Side scatter (SSC)** measures light collected at larger angles, commonly near 90 degrees. It can be sensitive to internal structure, surface features, and refractive-index contrast, but its response is not a universal measure of granularity; it also depends on particle size, wavelength, polarization, and collection geometry.

Detector Configuration
^^^^^^^^^^^^^^^^^^^^^^

The detector's numerical aperture and angular position set the collected portion of the scattered field. Responsivity converts optical power to photocurrent; dark current and amplifier noise contribute to the baseline fluctuations. The amplifier and any analog processing circuits then shape the voltage waveform before it reaches the digitizer.

.. code-block:: python

   from FlowCyPy.units import ureg
   from FlowCyPy.opto_electronics import Detector, Digitizer

   side_detector = Detector(
       name="side",
       phi_angle=90 * ureg.degree,
       numerical_aperture=0.2,
       responsivity=1 * ureg.ampere / ureg.watt,
       dark_current=0.1 * ureg.nanoampere,
   )

   digitizer = Digitizer(
       sampling_rate=60 * ureg.megahertz,
       bit_depth=14,
       use_auto_range=True,
   )

Particle Sampling and Waveform Sampling
---------------------------------------

The word *sampling* refers to two different stages in a simulation. A population's sampling method decides how particle events are represented; the digitizer's sampling rate decides how often the resulting voltage waveform is measured in time.

The default ``ExplicitModel`` estimates the number of particles passing through the sample during a run from their effective concentration, the sample flow, and the run duration. It then samples each event's particle properties, flow position, velocity, and arrival time. This is useful when individual event times and pulses matter.

For large particle counts, ``GammaModel(number_of_samples=...)`` instead draws a finite set of representative particle properties and estimates the expected occupancy of each time bin. In the current model, the expected particles per bin are:

.. math::

   \lambda_{\mathrm{bin}} =
   C_{\mathrm{eff}} \frac{\bar{v} A_{\mathrm{sample}}}{f_s}

where :math:`C_{\mathrm{eff}}` is the concentration after dilution, :math:`\bar{v}` is mean flow velocity, :math:`A_{\mathrm{sample}}` is the sample-channel cross-sectional area, and :math:`f_s` is the digitizer sampling rate. This occupancy-based model is a computationally efficient approximation; it does not represent every particle as a separate arrival-time pulse.

For a digitizer sampling rate :math:`f_s`, the time between adjacent waveform samples is:

.. math::

   \Delta t = \frac{1}{f_s}

The sampling rate should exceed twice the highest frequency retained by the analog front end (the Nyquist limit), with practical margin to preserve pulse shape. Analog filtering limits out-of-band noise and helps prevent aliasing. The digitizer's bit depth determines the number of available amplitude codes (:math:`2^b` for :math:`b` bits); its voltage range trades quantization resolution against clipping. Automatic range selection can use more of the available codes, while a fixed range is useful when comparing runs on a consistent scale.

Triggering and Event Segmentation
---------------------------------

A discriminator watches a selected detector channel for a trigger condition. For a numeric threshold, a rising crossing starts an event. A symbolic threshold such as ``"4sigma"`` is estimated from the trigger-channel trace using its median and a robust median-absolute-deviation estimate of noise:

.. math::

   V_{\mathrm{threshold}} =
   \operatorname{median}(V) +
   N \frac{\operatorname{median}(|V-\operatorname{median}(V)|)}{0.6745}

The factor :math:`0.6745` makes the median absolute deviation a robust estimate of the standard deviation for approximately Gaussian noise. In a ``FixedWindow`` discriminator, ``pre_buffer`` and ``post_buffer`` specify how many samples to keep before and after a crossing. The same time window is extracted from every detector channel, even though only the configured trigger channel decides when it starts. Dynamic-window and double-threshold discriminators provide alternatives when pulse duration or separate start/stop levels need to be modeled.

A lower threshold can capture weaker pulses but also admit more noise triggers; a higher threshold suppresses noise events but can miss faint particles. The threshold is therefore a detection-policy choice, not a universal property of the particle.

Peak Analysis and Limit of Detection
------------------------------------

Triggering isolates candidate windows; it does not by itself prove that a particle was detected. A peak locator then measures features within each digitized segment, such as peak height or position. These features can be compared across detector channels, particle sizes, and blank runs.

A formal limit of detection depends on both the signal distribution and the noise-only distribution, together with an explicit false-positive rate and detection-probability criterion. A single run at one concentration illustrates signal visibility and threshold behavior, but does not by itself establish a general limit of detection. In practice, evaluate replicate blanks and a dilution series, and report the trigger settings and sampling configuration used.

In FlowCyPy, the resulting run record keeps the analog traces, triggered digital segments, and extracted peak data together. The **Limit of Detection** example shows this sequence with a side-scatter trigger and a global peak locator.
