
.. DO NOT EDIT.
.. THIS FILE WAS AUTOMATICALLY GENERATED BY SPHINX-GALLERY.
.. TO MAKE CHANGES, EDIT THE SOURCE PYTHON FILE:
.. "gallery/full_workflow.py"
.. LINE NUMBERS ARE GIVEN BELOW.

.. only:: html

    .. note::
        :class: sphx-glr-download-link-note

        :ref:`Go to the end <sphx_glr_download_gallery_full_workflow.py>`
        to download the full example code

.. rst-class:: sphx-glr-example-title

.. _sphx_glr_gallery_full_workflow.py:


Simulating and Analyzing Flow Cytometer Signals
===============================================

This script simulates flow cytometer signals using the `FlowCytometer` class and analyzes the results using
the `PulseAnalyzer` class from the FlowCyPy library. The signals generated (forward scatter and side scatter)
provide insights into the physical properties of particles passing through the laser beam.

Workflow:
---------
1. Define a particle size distribution using `Scatterer`.
2. Simulate flow cytometer signals using `FlowCytometer`.
3. Analyze the forward scatter signal with `PulseAnalyzer` to extract features like peak height, width, and area.
4. Visualize the generated signals and display the extracted pulse features.

.. GENERATED FROM PYTHON SOURCE LINES 18-19

Step 1: Import necessary modules from FlowCyPy

.. GENERATED FROM PYTHON SOURCE LINES 19-24

.. code-block:: python3

    from FlowCyPy import FlowCytometer, Scatterer, Detector, Source, FlowCell
    from FlowCyPy import distribution
    from FlowCyPy.population import Population
    from FlowCyPy.units import nanometer, millisecond, meter, micrometer, second, RIU, milliliter, particle, millivolt, watt, megahertz, degree, ampere, milliwatt, AU








.. GENERATED FROM PYTHON SOURCE LINES 25-28

Step 2: Define flow parameters
------------------------------
Set the flow speed to 80 micrometers per second and a flow area of 1 square micrometer, with a total simulation time of 1 second.

.. GENERATED FROM PYTHON SOURCE LINES 28-34

.. code-block:: python3

    flow_cell = FlowCell(
        flow_speed=7.56 * meter / second,        # Flow speed: 7.56 meters per second
        flow_area=(20 * micrometer) ** 2,        # Flow area: 10 x 10 micrometers
        run_time=0.5 * millisecond             # Total simulation time: 0.3 milliseconds
    )








.. GENERATED FROM PYTHON SOURCE LINES 35-39

Step 3: Define the particle size distribution
---------------------------------------------
Use a normal size distribution with a mean size of 200 nanometers and a standard deviation of 10 nanometers.
This represents the population of scatterers (particles) that will interact with the laser source.

.. GENERATED FROM PYTHON SOURCE LINES 39-63

.. code-block:: python3

    ev_size = distribution.Normal(
        mean=200 * nanometer,       # Mean particle size: 200 nanometers
        std_dev=10 * nanometer      # Standard deviation: 10 nanometers
    )

    ev_ri = distribution.Normal(
        mean=1.39 * RIU,    # Mean refractive index: 1.39
        std_dev=0.01 * RIU  # Standard deviation: 0.01
    )

    ev = Population(
        size=ev_size,               # Particle size distribution
        refractive_index=ev_ri,     # Refractive index distribution
        concentration=1.8e+9 * particle / milliliter,  # Particle concentration: 1.8 million particles per milliliter
        name='EV'                   # Name of the particle population: Extracellular Vesicles (EV)
    )

    scatterer = Scatterer(populations=[ev])

    scatterer.initialize(flow_cell=flow_cell)

    # Plot the scatterer distribution
    scatterer.plot()




.. image-sg:: /gallery/images/sphx_glr_full_workflow_001.png
   :alt: full workflow
   :srcset: /gallery/images/sphx_glr_full_workflow_001.png
   :class: sphx-glr-single-img





.. GENERATED FROM PYTHON SOURCE LINES 64-67

Step 4: Define the laser source
-------------------------------
Set up a laser source with a wavelength of 1550 nm, optical power of 200 mW, and a numerical aperture of 0.3.

.. GENERATED FROM PYTHON SOURCE LINES 67-111

.. code-block:: python3

    source = Source(
        numerical_aperture=0.3 * AU,  # Numerical aperture: 0.3
        wavelength=800 * nanometer,   # Laser wavelength: 800 nm
        optical_power=20 * milliwatt  # Optical power: 20 milliwatts
    )

    # Step 5: Define the detector
    # ---------------------------
    # The detector captures the scattered light. It is positioned at 90 degrees relative to the incident light beam
    # and configured with a numerical aperture of 0.4 and responsitivity of 1.
    detector_0 = Detector(
        phi_angle=90 * degree,              # Detector angle: 90 degrees (Side Scatter)
        numerical_aperture=0.4 * AU,        # Numerical aperture of the detector
        name='first detector',              # Detector name
        responsitivity=1 * ampere / watt,   # Responsitivity of the detector (light to signal conversion efficiency)
        sampling_freq=1 * megahertz,        # Sampling frequency: 10,000 Hz
        saturation_level=40 * millivolt,    # Saturation level: Large enough to avoid saturation
        n_bins='14bit'                      # Number of bins for signal discretization: 1024
    )

    detector_1 = Detector(
        phi_angle=0 * degree,               # Detector angle: 90 degrees (Sid e Scatter)
        numerical_aperture=0.4 * AU,        # Numerical aperture of the detector
        name='second detector',             # Detector name
        responsitivity=1 * ampere / watt,   # Responsitivity of the detector (light to signal conversion efficiency)
        sampling_freq=2 * megahertz,        # Sampling frequency: 10,000 Hz
        saturation_level=40 * millivolt,    # Saturation level: Large enough to avoid saturation
        n_bins='14bit',                     # Number of bins for signal discretization: 1024
        include_shot_noise=False
    )

    # Step 6: Simulate Flow Cytometer Signals
    # ---------------------------------------
    # Create a FlowCytometer instance to simulate the signals generated as particles pass through the laser beam.
    cytometer = FlowCytometer(
        coupling_mechanism='mie',           # Scattering model: Empirical (Rayleigh scattering for small particles)
        source=source,                      # Laser source
        scatterer=scatterer,                # Particle size distribution
        detectors=[detector_0, detector_1]  # List of detectors used in the simulation
    )

    # Simulate the pulse signals generated from the interaction between particles and the laser.
    cytometer.simulate_pulse()








.. GENERATED FROM PYTHON SOURCE LINES 112-115

Step 7: Analyze and Visualize Results
-------------------------------------
Display the properties of the simulated cytometer setup, including flow speed and laser power.

.. GENERATED FROM PYTHON SOURCE LINES 115-126

.. code-block:: python3

    cytometer.print_properties()

    # Plot the simulated signals for the detector.
    cytometer.plot()

    """
    Summary:
    --------
    This script simulates flow cytometer signals, processes them to detect peaks in the forward scatter channel,
    and extracts important features. The process is visualized through signal plots, and key properties are displayed.
    """



.. image-sg:: /gallery/images/sphx_glr_full_workflow_002.png
   :alt: full workflow
   :srcset: /gallery/images/sphx_glr_full_workflow_002.png
   :class: sphx-glr-single-img


.. rst-class:: sphx-glr-script-out

 .. code-block:: none


    Scatterer [] Properties
    +-----------------------------+----------+
    | Property                    | Value    |
    +=============================+==========+
    | coupling factor             | mie      |
    +-----------------------------+----------+
    | medium refractive index     | 1.0 RIU  |
    +-----------------------------+----------+
    | minimum time between events | 29.6 ps  |
    +-----------------------------+----------+
    | average time between events | 188.5 ns |
    +-----------------------------+----------+

    Population [EV] Properties
    +------------------+-------------------------------+
    | Property         | Value                         |
    +==================+===============================+
    | Name             | EV                            |
    +------------------+-------------------------------+
    | Refractive Index | Normal(1.390 RIU, 0.010 RIU)  |
    +------------------+-------------------------------+
    | Size             | Normal(200.000 nm, 10.000 nm) |
    +------------------+-------------------------------+
    | Concentration    | 3.0 nmol/m³                   |
    +------------------+-------------------------------+
    | N events         | 2.7 kparticle                 |
    +------------------+-------------------------------+

    FlowCytometer Properties

    Source [] Properties
    +------------+---------+
    | Property   | Value   |
    +============+=========+
    +------------+---------+

    Detector [first detector] Properties
    +--------------------+----------+
    | Property           | Value    |
    +====================+==========+
    | Sampling frequency | 1.0 MHz  |
    +--------------------+----------+
    | Phi angle          | 90.0 deg |
    +--------------------+----------+
    | Gamma angle        | 0.0 deg  |
    +--------------------+----------+
    | Numerical aperture | 0.4      |
    +--------------------+----------+
    | Responsitivity     | 1.0 A/W  |
    +--------------------+----------+
    | Saturation Level   | 40.0 mV  |
    +--------------------+----------+
    | Dark Current       | 0.0 A    |
    +--------------------+----------+
    | Resistance         | 50.0 Ω   |
    +--------------------+----------+
    | Temperature        | 0.0 K    |
    +--------------------+----------+
    | N Bins             | 16384    |
    +--------------------+----------+

    Detector [second detector] Properties
    +--------------------+---------+
    | Property           | Value   |
    +====================+=========+
    | Sampling frequency | 2.0 MHz |
    +--------------------+---------+
    | Phi angle          | 0.0 deg |
    +--------------------+---------+
    | Gamma angle        | 0.0 deg |
    +--------------------+---------+
    | Numerical aperture | 0.4     |
    +--------------------+---------+
    | Responsitivity     | 1.0 A/W |
    +--------------------+---------+
    | Saturation Level   | 40.0 mV |
    +--------------------+---------+
    | Dark Current       | 0.0 A   |
    +--------------------+---------+
    | Resistance         | 50.0 Ω  |
    +--------------------+---------+
    | Temperature        | 0.0 K   |
    +--------------------+---------+
    | N Bins             | 16384   |
    +--------------------+---------+

    '\nSummary:\n--------\nThis script simulates flow cytometer signals, processes them to detect peaks in the forward scatter channel,\nand extracts important features. The process is visualized through signal plots, and key properties are displayed.\n'




.. rst-class:: sphx-glr-timing

   **Total running time of the script:** (0 minutes 5.804 seconds)


.. _sphx_glr_download_gallery_full_workflow.py:

.. only:: html

  .. container:: sphx-glr-footer sphx-glr-footer-example




    .. container:: sphx-glr-download sphx-glr-download-python

      :download:`Download Python source code: full_workflow.py <full_workflow.py>`

    .. container:: sphx-glr-download sphx-glr-download-jupyter

      :download:`Download Jupyter notebook: full_workflow.ipynb <full_workflow.ipynb>`


.. only:: html

 .. rst-class:: sphx-glr-signature

    `Gallery generated by Sphinx-Gallery <https://sphinx-gallery.github.io>`_
