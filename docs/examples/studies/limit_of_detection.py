"""
Limit of Detection
==================

This example simulates the detection of small nanoparticles (50-150 nm diameter)
in a flow cytometry setup using a dual-detector configuration (side and forward scatter).
The simulation includes noise models, realistic fluidics, analog amplification,
digitization, triggering, and peak detection.

The main goal is to evaluate whether such particles produce detectable and distinguishable
scatter signals in the presence of system noise and fluidic variability.
"""

from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.systems.cytek import aurora
from FlowCyPy.units import ureg

# %%
# Load five nanoparticle sizes on the 405 nm Aurora scatter preset
# ----------------------------------------------------------------
instrument = aurora(optical_power=100 * ureg.milliwatt, background_power=0.1 * ureg.nanowatt)
scatterer_collection = instrument.fluidics.scatterer_collection

for size in [150, 125, 100, 75, 50]:
    pop = populations.SpherePopulation(
        name=f"{size} nm",
        concentration=5e9 * ureg.particle / ureg.milliliter,
        diameter=distributions.Delta(value=size * ureg.nanometer),
        refractive_index=distributions.Delta(value=1.36),
        medium_refractive_index=1.33,
    )
    scatterer_collection.add_population(pop)

scatterer_collection.dilute(factor=100)

# %%
# Acquire ten milliseconds with the preset's side-scatter trigger
# ---------------------------------------------------------------
run_record = instrument.run(run_time=10 * ureg.millisecond, random_state=42)

# %%
# Plot Raw Analog Signal
# ----------------------
# Zoom to the strongest triggered window so the pulse shape remains visible
# instead of compressing the entire acquisition into a dense band.
digital_signal = run_record.signal.digital
analog_signal = run_record.signal.analog
plot_time_unit = run_record.run_time.to_compact().units
time_window = None
plot_title = "Strongest signal (no triggered windows)"

if digital_signal is not None and not digital_signal.empty:
    strongest_segment = max(
        digital_signal.groupby(level="SegmentID"),
        key=lambda segment: segment[1]["SSC"].max(),
    )[1]
    segment_time_unit = digital_signal.attrs["units"]["Time"]
    segment_start = (
        strongest_segment["Time"].iloc[0] * segment_time_unit
    ).to(plot_time_unit).magnitude
    segment_end = (
        strongest_segment["Time"].iloc[-1] * segment_time_unit
    ).to(plot_time_unit).magnitude
    padding = (5 * ureg.microsecond).to(plot_time_unit).magnitude
    run_end = run_record.run_time.to(plot_time_unit).magnitude

    time_window = (max(0.0, segment_start - padding), min(run_end, segment_end + padding))
    plot_title = "Strongest triggered event and detector noise"
else:
    strongest_sample = analog_signal["SSC"].abs().idxmax()
    signal_time_unit = analog_signal.attrs["units"]["Time"]
    peak_time = (
        analog_signal.loc[strongest_sample, "Time"] * signal_time_unit
    ).to(plot_time_unit).magnitude
    padding = (5 * ureg.microsecond).to(plot_time_unit).magnitude
    run_end = run_record.run_time.to(plot_time_unit).magnitude

    time_window = (max(0.0, peak_time - padding), min(run_end, peak_time + padding))

run_record.plot_analog(xlim=time_window, title=plot_title, include_scatterer=False)

# %%
# Plot Triggered Analog Signal Segments
# -------------------------------------
# Inspect which weak pulses survived the discriminator threshold.
if digital_signal is not None and not digital_signal.empty:
    run_record.plot_digital()
