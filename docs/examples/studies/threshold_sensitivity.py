"""
Threshold sensitivity
=====================

This tutorial investigates how discriminator threshold affects event recovery
for weak signals close to baseline noise.
"""

import pandas as pd
from FlowCyPy.digital_processing import DigitalProcessing, discriminator, peak_locator
from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.systems.cytek import aurora
from FlowCyPy.units import ureg

# %%
# Load the weakly scattering sample
# ---------------------------------
instrument = aurora(optical_power=25 * ureg.milliwatt)
scatterer_collection = instrument.fluidics.scatterer_collection
medium_refractive_index = distributions.Delta(1.33)
diameter_distribution = distributions.RosinRammler(
    scale=100 * ureg.nanometer,
    shape=12,
)
refractive_index_distribution = distributions.Normal(
    mean=1.40,
    standard_deviation=0.002,
    low_cutoff=1.33,
)
sampling_method = populations.ExplicitModel()
population = populations.SpherePopulation(
    name="Near-threshold population",
    medium_refractive_index=medium_refractive_index,
    concentration=1e10 * ureg.particle / ureg.milliliter,
    diameter=diameter_distribution,
    refractive_index=refractive_index_distribution,
    sampling_method=sampling_method,
)

scatterer_collection.add_population(population)

scatterer_collection.dilute(100)

# %%
# Step 2: Sweep discriminator threshold
# -------------------------------------
# Acquire the particles and analog noise once so each threshold sees the same
# waveform. Event IDs below are row positions in this shared acquisition.
acquisition = instrument.acquire(
    run_time=1 * ureg.millisecond,
    random_state=42,
)
threshold_values = ["2sigma", "3sigma", "4sigma", "5sigma"]
run_records = []
event_capture = pd.DataFrame()
window_counts = []

for threshold_value in threshold_values:
    trigger_window = discriminator.DynamicWindow(
        trigger_channel="SSC",
        threshold=threshold_value,
        pre_buffer=40,
        post_buffer=40,
        max_triggers=-1,
    )
    peak_algorithm = peak_locator.GlobalPeakLocator()
    digital_processing = DigitalProcessing(
        discriminator=trigger_window,
        peak_locator=peak_algorithm,
    )

    run_record = acquisition.process(digital_processing=digital_processing)

    run_records.append((threshold_value, run_record))
    events = run_record.annotate_detected_events()
    event_capture[threshold_value] = events["Detected"].to_numpy()
    occupancy = run_record.coincidence_statistics()
    window_counts.append({
        "Threshold": threshold_value,
        "Captured arrivals": occupancy["DetectedEvents"],
        "Empty windows": occupancy["EmptySegments"],
        "Total windows": occupancy["TotalTriggerSegments"],
    })

event_capture.index.name = "Event ID"
print(event_capture.to_string())
print(pd.DataFrame(window_counts).set_index("Threshold").to_string())


def plot_analog_window(run_record, threshold_value):
    figure = run_record.plot_analog(include_scatterer=False, title=f"Analog signal at {threshold_value} threshold")
    window_end = (100 * ureg.microsecond).m_as(run_record.signal.analog.attrs["units"]["Time"])
    figure.axes[0].set_xlim(0, window_end)
    return figure


def plot_digital_window(run_record, threshold_value):
    if run_record.signal.digital is None:
        return None
    figure = run_record.plot_digital(include_scatterer=False, title=f"Triggered segments at {threshold_value}")
    window_end = (100 * ureg.microsecond).m_as(run_record.signal.digital.attrs["units"]["Time"])
    figure.axes[0].set_xlim(0, window_end)
    return figure


def plot_peak_heights(run_record, threshold_value):
    if run_record.peaks is None:
        return None
    return run_record.plot_peaks(
        x=("SSC", "Height"),
        title=f"Side-scatter peak heights at {threshold_value}",
    )


# %%
# Analog signal at 2sigma
# -----------------------
# Inspect the signal and baseline before reviewing the recovered events.
threshold_value, run_record = run_records[0]
_ = plot_analog_window(run_record, threshold_value)

# %%
# Triggered segments at 2sigma
# ----------------------------
# Inspect the first 0.1 milliseconds of triggered signal segments.
_ = plot_digital_window(run_record, threshold_value)

# %%
# Peak heights at 2sigma
# ----------------------
# Compare the recovered weak-event distribution as the threshold rises.
_ = plot_peak_heights(run_record, threshold_value)

# %%
# Analog signal at 3sigma
# -----------------------
# Inspect the signal and baseline before reviewing the recovered events.
threshold_value, run_record = run_records[1]
_ = plot_analog_window(run_record, threshold_value)

# %%
# Triggered segments at 3sigma
# ----------------------------
# Inspect the first 0.1 milliseconds of triggered signal segments.
_ = plot_digital_window(run_record, threshold_value)

# %%
# Peak heights at 3sigma
# ----------------------
# Compare the recovered weak-event distribution as the threshold rises.
_ = plot_peak_heights(run_record, threshold_value)

# %%
# Analog signal at 4sigma
# -----------------------
# Inspect the signal and baseline before reviewing the recovered events.
threshold_value, run_record = run_records[2]
_ = plot_analog_window(run_record, threshold_value)

# %%
# Triggered segments at 4sigma
# ----------------------------
# Inspect the first 0.1 milliseconds of triggered signal segments.
_ = plot_digital_window(run_record, threshold_value)

# %%
# Peak heights at 4sigma
# ----------------------
# Compare the recovered weak-event distribution as the threshold rises.
_ = plot_peak_heights(run_record, threshold_value)

# %%
# Analog signal at 5sigma
# -----------------------
# Inspect the signal and baseline before reviewing the recovered events.
threshold_value, run_record = run_records[3]
_ = plot_analog_window(run_record, threshold_value)

# %%
# Triggered segments at 5sigma
# ----------------------------
# Inspect the first 0.1 milliseconds of triggered signal segments.
_ = plot_digital_window(run_record, threshold_value)

# %%
# Peak heights at 5sigma
# ----------------------
# Compare the recovered weak-event distribution as the threshold rises.
_ = plot_peak_heights(run_record, threshold_value)
