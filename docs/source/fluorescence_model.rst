Fluorescence from a labeled particle
====================================

FlowCyPy predicts how much optical power a labeled particle delivers to each
detector and when that power arrives. Three measurements in the output answer
different questions. The event column ``Label:<dye name>`` gives molecules per
particle. The event column named for the detector gives its prompt-equivalent
power amplitude in watts. The same channel in ``record.signal.analog`` gives
voltage versus time, including overlapping particles, lifetime, and electronics.

From molecule count to optical power
------------------------------------

For one particle, let :math:`I(t)` be the local laser irradiance in W/m²,
:math:`N` the number of molecules of one dye and :math:`\sigma_a` the
absorption cross section in m² per molecule at laser wavelength
:math:`\lambda_L`. The source sets the peak irradiance at the event's
transverse position and generates the transit pulse from its arrival time
and velocity. In the weak-excitation limit the absorbed photon rate is

.. math::

   \dot n_{\rm abs}(t) = \frac{N \sigma_a I(t)}{hc/\lambda_L}.

Quantum yield :math:`\Phi` gives the mean number of emitted photons per
absorbed photon. The dye's normalized photon weights :math:`p_j` sum to one
over emission bins with representative wavelengths :math:`\lambda_j`.
For detector :math:`d`, let :math:`f_d` be the collected fraction of solid
angle and :math:`T_d(\lambda_j)` its filter transmission. Multiplying each
bin's photon rate by its photon energy gives the prompt-equivalent power

.. math::

   P^0_{dj}(t) =
   N \sigma_a I(t)\,\Phi\, f_d\,p_j\,T_d(\lambda_j)
   \frac{\lambda_L}{\lambda_j}.

The wavelength ratio matters when predicting voltage from a spectrum. At equal
photon rates, the shorter-wavelength bin delivers more watts. For example, at
an irradiance of :math:`10^6` W/m², 20,000 molecules with a cross section of
:math:`2\times10^{-20}` m² absorb 400 pW. For excitation at 488 nm, yield 0.8,
20% geometric collection and all photons emitted and transmitted at 520 nm,
the detector receives about 60 pW. Doubling the molecule count doubles this
power. These values illustrate the calculation.

Choosing physical inputs
^^^^^^^^^^^^^^^^^^^^^^^^

* **Particle and dye.** Sphere and core-shell populations support labels with
  explicit particle sampling. A dimensionless distribution supplies one
  nonnegative count per particle and dye, rounded to the nearest integer.
  Every detector sees that same draw. Multiple dyes add independently.
* **Absorption.** Supply a molecular cross section at the configured laser
  wavelength. If a dye datasheet gives molar extinction coefficient in
  L mol⁻¹ cm⁻¹, multiply its numerical value by 0.1 ln(10) and divide by
  the Avogadro constant to obtain m² per molecule (Beer–Lambert conversion).
  The model uses one local irradiance for every label on a particle.
  It treats cross section and quantum yield as constant through the transit.
  Saturation, bleaching, energy transfer, self-quenching and internal optical
  fields would require additional physics. The linear model can overpredict
  brightness at high excitation or high labeling density.
* **Spectrum.** Supply integrated photon counts per bin as ``photon_weights``.
  For measured photon density per nm, integrate over each bin width first.
  For radiant power per nm, also divide by the photon energy before integrating.
  Use a response-corrected spectrum if detector sensitivity shaped the measurement.

Stochastic surface labeling
---------------------------

To model independent binding on a spherical particle, give a label its mean
surface density. For each particle FlowCyPy draws a molecule count once,
using the same sampled outer diameter :math:`D` used to define that particle:

.. math::

   N \mid D \sim \mathrm{Poisson}(\rho \pi D^2).

.. code-block:: python

   from FlowCyPy.dyes import fitc
   from FlowCyPy.fluorescence import Label
   from FlowCyPy.units import ureg

   coating = Label(fluorophore=fitc(), molecules_per_area=0.02 / ureg.nm**2)

For a core-shell particle the outer diameter is the core diameter plus twice
the radial shell thickness. Even equal-sized beads fluctuate: at a fixed
diameter, the count variance equals its mean. Size dispersion adds variation
through the area. All channels use the stored event count, and an acquisition
seed reproduces the draws. The model assumes independent occupancy and has no
finite binding-site capacity. Use ``molecules_per_particle`` for a fixed
count or a count distribution independent of geometry.

Predefined dyes
---------------

Import a dye from ``FlowCyPy.dyes`` and call it to create a fluorophore. Set
the labeling density separately for each population.

.. code-block:: python

   from FlowCyPy.dyes import alexa_fluor_488
   from FlowCyPy.fluorescence import Label

   label = Label(fluorophore=alexa_fluor_488(), molecules_per_particle=20_000)

.. list-table:: Reference optical properties
   :header-rows: 1

   * - Preset
     - Absorption max (nm)
     - Emission max (nm)
     - Peak extinction (L mol⁻¹ cm⁻¹)
     - Quantum yield
     - Lifetime (ns)
   * - ``alexa_fluor_488``
     - 495
     - 519
     - 73,000
     - 0.92
     - 4.1
   * - ``alexa_fluor_594``
     - 590
     - 617
     - 92,000
     - 0.66
     - 3.9
   * - ``alexa_fluor_647``
     - 650
     - 668
     - 270,000
     - 0.33
     - 1.0
   * - ``fitc``
     - 494
     - 518
     - 70,000
     - 0.92
     - 4.1
   * - ``atto_647n``
     - 646
     - 664
     - 150,000
     - 0.65
     - 3.5

For the Alexa Fluor presets, the spectral maxima describe conjugates, and the extinction coefficients describe
reactive dyes at peak absorption. Yield and lifetime were measured on free
succinimidyl ester derivatives. Yield was measured in PBS at pH 7.2 and 22 °C.
The handbook reports the 647 lifetime in water at 22 °C and credits separate
measurements for 488 and 594. A different conjugate or medium can change these
values. See Thermo Fisher's `spectral properties table <https://www.thermofisher.com/us/en/home/references/molecular-probes-the-handbook/technical-notes-and-product-highlights/the-alexa-fluor-dye-series.html>`_
and `quantum yield and lifetime table <https://www.thermofisher.com/us/en/home/references/molecular-probes-the-handbook/tables/fluorescence-quantum-yields-and-lifetimes-for-alexa-fluor-dyes.html>`_.

**FITC** represents fluorescein isothiocyanate. The preset combines spectral
maxima and an extinction coefficient measured in aqueous buffer at pH 9
with a supplier-reported quantum yield and a lifetime measured in phosphate
buffer at pH 7.8. These reference values come from different preparations.
For an antibody conjugate, use measurements at the relevant labeling density
and pH when available. Sources: `Thermo Scientific FITC guide <https://documents.thermofisher.com/TFS-Assets/LSG/manuals/MAN0011646_FITC_TRITC_UG.pdf>`_,
`Tocris FITC photophysical data <https://www.rndsystems.com/products/fitc_5440>`_,
and `ISS lifetime data <https://iss.com/resources/data-sheets>`_.

**ATTO 647N** uses measurements of the carboxy derivative in PBS at pH 7.4
and 22 °C. See the `ATTO-TEC catalogue, pp. 28–29 <https://www.atto-tec.com/images/ATTO/Katalog_Preisliste/Katalog_2023_2024.pdf>`_.

**Excitation.** The default uses the peak extinction coefficient. For another
laser line, pass ``relative_absorption`` equal to the ratio of absorbance at
that line to absorbance at the maximum, taken from the same spectrum. Rebuild
the dye with the appropriate ratio when changing lasers.

**Emission.** Each preset places all photons in one bin at its emission maximum.
A hard filter therefore accepts either all or none of its emission. This
approximation is useful for lifetime demonstrations. For filter throughput or
spectral spillover, provide measured emission bins, for example with
``dataclasses.replace(dye, emission_wavelengths=wavelengths, photon_weights=counts)``.
See :doc:`gallery/tutorials/detect_labeled_beads` for a complete acquisition.

Collection, filters and spillover
---------------------------------

Emission is isotropic. In the air collection geometry,
:math:`0 \leq \mathrm{NA}_{\rm inner} \leq \mathrm{NA}_{\rm outer} \leq 1`.
The central obscuration excludes the inner cone. Integrating over the remaining
annulus gives the fraction of all emitted photons reaching the channel

.. math::

   f_d = \frac{\sqrt{1-\mathrm{NA}_{\rm inner}^2}
                  -\sqrt{1-\mathrm{NA}_{\rm outer}^2}}{2}.

An unobscured NA of 0.8 collects 20%. Rotating that cone leaves its fluorescence
fraction unchanged. Elastic scatter has its own angular dependence. Detectors
default to scatter only. Select fluorescence only or both contributions using
``signals``. A mixed channel applies its filter at the laser wavelength for
scatter and at each emission wavelength for fluorescence.

A ``Bandpass(center=530 * ureg.nm, width=30 * ureg.nm)`` transmits unity from
515 through 545 nm inclusive and zero elsewhere. Omitting the filter accepts
all wavelengths for the selected contributions. The entire weight of a bin is
assigned to its representative wavelength. Split bins near a filter edge and
repeat the calculation to check convergence. Real filter slopes, finite
stopband leakage and other wavelength-dependent optical losses are outside
this idealization. Spectral spillover still occurs whenever two dyes emit in
the same passband. See :doc:`gallery/tutorials/define_custom_dye_spectra`.

Lifetime, transit and sampling
------------------------------

Each dye can have its own lifetime :math:`\tau`. Zero or omitted lifetime gives
prompt emission. For positive lifetime, the emitted power :math:`P_{dj}` obeys

.. math::

   \tau \frac{dP_{dj}}{dt} + P_{dj} = P^0_{dj}(t).

This is a single exponential relaxation with unit integrated response. A
finite lifetime shifts light into later bins. The area under a complete optical
pulse is conserved, while the peak height and the energy inside a short trigger
window can change. For an instantaneous excitation, the fraction collected in a
gate of duration :math:`T` starting at excitation is
:math:`1-\exp(-T/\tau)`. A laser that stays on throughout the gate gives a
different result because molecules continue to be excited inside the gate.

The digitizer sets the time grid, :math:`\Delta t=1/f_s`. FlowCyPy holds
excitation constant within each bin and calculates the exact mean emitted power
over that bin for the assumed excitation. Resolve the fastest change in the
**excitation** and refine the grid to check your gate fraction or pulse shape.
The solution starts in periodic steady state. A tail near the end of the
acquisition continues at the start. To approximate an isolated pulse, leave
enough dark time for its tail to decay before the next period.

The amplifier and analog circuits also shape the measured voltage. A faster
digitizer can sample a bandwidth-limited waveform more densely, while its
measured delay still includes the electronics. The worked example isolates
the dye using a known excitation and idealized electronics. For an experimental
comparison using scatter and fluorescence pulse delays, see
`Cao et al. (2014) <https://doi.org/10.1002/cyto.a.22574>`_.
See :doc:`gallery/studies/measure_fluorescence_gate_loss`.

Noise and comparison with measurements
--------------------------------------

When enabled, laser relative intensity noise supplies a common excitation
fluctuation across channels. Lifetime acts on this fluctuating excitation.
Photon shot noise is then drawn using the energy of each wavelength component.
For mean counts below 100 photons per bin the sampler uses a Poisson draw.
At higher counts it uses a nonnegative Gaussian approximation with the same
nominal mean and variance. Configured in-channel background uses the laser
photon energy for this calculation.

Each detector sums optical powers and applies one responsivity in A/W across
its entire band. Detector current noise and amplification follow. Run processing
can then apply analog circuits, triggering, digitization and peak measurement.
For an instrument comparison, match the laser irradiance, collection geometry,
bandpass, responsivity, gain and bandwidth. Unlabeled controls establish the
baseline and single-color controls reveal how much of each dye enters the
other channels. Absolute intensity alone constrains a product of label count,
absorption, yield and detection efficiency. Independent calibration is needed
to infer molecule counts from voltage.

Follow :doc:`gallery/tutorials/detect_labeled_beads` to compare the event
record, analog waveform and green-triggered segments for the same sample.
