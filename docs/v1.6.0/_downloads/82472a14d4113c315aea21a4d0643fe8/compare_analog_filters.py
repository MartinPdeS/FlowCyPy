"""
Compare baseline restoration and low-pass filtering
===================================================

Acquire one forward-scatter waveform on the FACSCanto preset and apply two
analog filters to it. Using the same waveform keeps particle arrivals and
detector noise identical across the comparison.
"""

import matplotlib.pyplot as plt
from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.opto_electronics import circuits
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

instrument = facs_canto(optical_power=100 * ureg.milliwatt, background_power=2 * ureg.microwatt)
diameter_distribution = distributions.Delta(value=150 * ureg.nanometer)
refractive_index_distribution = distributions.Delta(value=1.39)
population = populations.SpherePopulation(
    name="Population",
    concentration=5e9 * ureg.particle / ureg.milliliter,
    diameter=diameter_distribution,
    refractive_index=refractive_index_distribution,
    medium_refractive_index=1.33,
)
instrument.fluidics.scatterer_collection.add_population(population)

# %%
# Compare the three analog processing chains
# ------------------------------------------
record = instrument.acquire(run_time=100 * ureg.microsecond, random_state=42)
signal = record.signal.analog["forward"].to("volt")
time = record.signal.analog["Time"].m_as("microsecond")
sampling_rate = instrument.opto_electronics.digitizer.sampling_rate

figure, axis = plt.subplots()
axis.plot(time, signal.m_as("millivolt"), label="Raw signal")
baseline_restoration = circuits.BaselineRestorationServo(time_constant=10 * ureg.microsecond)
low_pass_filter = circuits.BesselLowPass(cutoff_frequency=3 * ureg.megahertz, order=4, gain=2)
for label, circuit in [
    ("Baseline restored", baseline_restoration),
    ("Bessel low-pass", low_pass_filter),
]:
    filtered = circuit.process(signal=signal.copy(), sampling_rate=sampling_rate)
    axis.plot(time, filtered.m_as("millivolt"), label=label)
axis.set(xlabel="Time [µs]", ylabel="Forward-scatter voltage [mV]")
axis.legend()
plt.show()
