"""
Flow Cytometry Simulation: Full System Example
==============================================

This tutorial demonstrates a complete flow cytometry simulation using the FlowCyPy library.
It models fluidics, optics, signal processing, and classification of multiple particle populations.

Steps Covered:
--------------
1. Configure simulation parameters and noise models
2. Define laser source, flow cell geometry, and fluidics
3. Add synthetic particle populations
4. Set up detectors, amplifier, and digitizer
5. Simulate analog and digital signal acquisition
6. Apply triggering and peak detection
7. Classify particle events based on peak features
"""

from FlowCyPy.instances.flow_cytometer import FacsCanto, SampleFlowRate, SheathFlowRate
from FlowCyPy.fluidics import distribution, population
from TypedUnit import ureg


population_0 = population.Sphere(
    name="Pop 0",
    particle_count=5e9 * ureg.particle / ureg.milliliter,
    diameter=distribution.RosinRammler(150 * ureg.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * ureg.RIU, std_dev=0.002 * ureg.RIU),
)

facs_canto = FacsCanto(
    sample_volume_flow=SampleFlowRate.MEDIUM,
    sheath_volume_flow=SheathFlowRate.DEFAULT,
    optical_power=20 * ureg.milliwatt,
    background_power=1 * ureg.nanowatt,
)

facs_canto.add_population(population_0)

facs_canto.dilute_sample(factor=100)

run_record = facs_canto.run(run_time=1.8 * ureg.millisecond)

run_record.triggered_analog.plot()

# _ = run_record.events.plot(x="side", y="forward", z="RefractiveIndex")
