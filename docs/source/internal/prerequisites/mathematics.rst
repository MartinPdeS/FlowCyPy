Mathematical Background
-----------------------

A strong mathematical foundation is essential for working effectively with **FlowCyPy**, particularly in the areas of signal processing, noise analysis, and data interpretation. This section highlights key concepts and provides a deeper dive into their application within the context of flow cytometry simulations.

Signal Processing
~~~~~~~~~~~~~~~~~~

Fourier Transforms
******************

Fourier analysis is critical for understanding the frequency components of signals generated by flow cytometry detectors. For example, a signal :math:`f(t)` in the time domain can be transformed into the frequency domain using the Fourier transform:

.. math::

   F(\omega) = \int_{-\infty}^{\infty} f(t) e^{-j\omega t} \, dt

In **FlowCyPy**, Fourier transforms can be used to analyze noise characteristics and filter unwanted frequency components. Understanding the spectral content of signals allows us to optimize detectors and reduce the impact of high-frequency noise.

Noise Modeling
**************

Noise in flow cytometry signals can originate from various sources, including:

- **Shot Noise**: Arises from the discrete nature of photon arrival. Its standard deviation is proportional to the square root of the signal mean:

  .. math::

     \sigma_{\text{shot}} = \sqrt{2 e I B}

  where:

  - :math:`e` is the elementary charge,
  - :math:`I` is the photocurrent,
  - :math:`B` is the bandwidth.

- **Thermal Noise**: Also known as Johnson-Nyquist noise, is given by:

  .. math::

     \sigma_{\text{thermal}} = \sqrt{\frac{4 k_B T R}{B}}

  where:

  - :math:`k_B` is Boltzmann's constant,
  - :math:`T` is the temperature,
  - :math:`R` is the resistance,
  - :math:`B` is the bandwidth.

Application in FlowCyPy
***********************

These noise models are integrated into **FlowCyPy** to simulate realistic detector signals, enabling users to understand the effects of noise and optimize experimental setups.

Probability and Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Statistical Moments
*******************

Statistical moments are key metrics for describing the properties of distributions, such as particle sizes or detected signal intensities. In **FlowCyPy**, we frequently use the first four moments:

1. **Mean (:math:`\mu`)**:

   .. math::

      \mu = \frac{1}{N} \sum_{i=1}^{N} x_i

   Represents the central value of a dataset (e.g., average particle size).

2. **Variance (:math:`\sigma^2`)**:

   .. math::

      \sigma^2 = \frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^2

   Measures the spread of data around the mean.

3. **Skewness (:math:`\gamma^2`)**:

   .. math::

      \gamma_1 = \frac{\frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^3}{\sigma^3}

   Indicates the asymmetry of the distribution.


Example Application
*******************

Consider a distribution of particle sizes simulated in **FlowCyPy**. By computing the statistical moments:

- The **mean** provides insight into the typical particle size.
- The **variance** quantifies size variability.
- The **skewness** helps identify whether smaller or larger particles dominate.

This analysis can inform experimental design and detector sensitivity requirements.

Practical Objectives
~~~~~~~~~~~~~~~~~~~~~

1. **Signal-to-Noise Ratio (SNR)**

   Compute and analyze the SNR for a detector signal:

   .. math::

      \text{SNR} = \frac{\mu_{\text{signal}}}{\sigma_{\text{noise}}}

   A high SNR indicates good signal quality, while a low SNR suggests that noise dominates.

2. **Noise Analysis**

   Simulate a detector with high thermal noise and compare it to a low-noise detector. Analyze how noise affects the quality of detected peaks in the signal.

3. **Histogram Analysis**

   Generate histograms of simulated particle sizes or signal intensities and compute their moments. Use this information to evaluate the detector’s ability to distinguish between different particle populations.

By mastering these mathematical principles, you will be equipped to simulate, analyze, and interpret flow cytometry data effectively, ensuring meaningful contributions to the **FlowCyPy** project.
