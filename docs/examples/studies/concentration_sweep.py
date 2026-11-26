"""
Concentration and coincidence
=============================

This tutorial studies how increasing particle concentration changes the detector
signal and the extracted event statistics.

Using the same optical, electronic, and digital processing configuration, we run
a series of simulations at progressively higher concentrations and compare the
resulting analog traces, trigger counts, and peak distributions.

Questions addressed
-------------------
1. When do individual particle pulses begin to overlap?
2. How does concentration affect the number of detected events?
3. How do peak height and area distributions change as coincidence increases?
4. When does the measured signal cease to reflect single-particle behavior?
"""

from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.systems.cytek import aurora
from FlowCyPy.units import ureg

# %%
# Sweep concentration on the Aurora preset
# ----------------------------------------
# Each acquisition uses the same side-scatter trigger and a fresh sample.

medium_refractive_index = distributions.Delta(1.33)
diameter_distribution = distributions.RosinRammler(
    scale=120 * ureg.nanometer,
    shape=8,
)
refractive_index_distribution = distributions.Normal(
    mean=1.44,
    standard_deviation=0.002,
    low_cutoff=1.33,
)

concentration_values = [
    1e8,
    5e8,
    1e9,
    5e9,
]

run_records = []

for concentration_value in concentration_values:
    instrument = aurora(optical_power=100 * ureg.milliwatt)

    population = populations.SpherePopulation(
        name=f"{concentration_value:.0e} particles_per_mL",
        medium_refractive_index=medium_refractive_index,
        concentration=concentration_value * ureg.particle / ureg.milliliter,
        diameter=diameter_distribution,
        refractive_index=refractive_index_distribution,
        sampling_method=populations.ExplicitModel(),
    )

    instrument.fluidics.scatterer_collection.add_population(population)
    run_record = instrument.run(run_time=1 * ureg.millisecond, random_state=42)
    run_records.append(run_record)
    print(f"{concentration_value:.0e} particles/mL: {run_record.number_of_triggers or 0} trigger windows")


def plot_analog_window(run_record, title):
    figure = run_record.plot_analog(include_scatterer=False, title=title)
    window_end = (100 * ureg.microsecond).m_as(run_record.signal.analog.attrs["units"]["Time"])
    figure.axes[0].set_xlim(0, window_end)
    return figure


def plot_peak_heights(run_record, concentration_value):
    if run_record.peaks is None:
        print(f"No peaks detected at {concentration_value:.0e} particles/mL.")
        return
    return run_record.plot_peaks(
        x=("SSC", "Height"),
        title=f"Side-scatter peak heights at {concentration_value:.0e} particles/mL",
    )


# %%
# Analog trace at 1e8 particles/mL
# --------------------------------
# Inspect pulse overlap as concentration increases.
_ = plot_analog_window(
    run_records[0], "Side-scatter signal at 1e8 particles/mL"
)

# %%
# Peak heights at 1e8 particles/mL
# --------------------------------
# Compare the recovered side-scatter peak distribution with the corresponding trace.
_ = plot_peak_heights(run_records[0], concentration_values[0])

# %%
# Analog trace at 5e8 particles/mL
# --------------------------------
# Inspect pulse overlap as concentration increases.
_ = plot_analog_window(
    run_records[1], "Side-scatter signal at 5e8 particles/mL"
)

# %%
# Peak heights at 5e8 particles/mL
# --------------------------------
# Compare the recovered side-scatter peak distribution with the corresponding trace.
_ = plot_peak_heights(run_records[1], concentration_values[1])

# %%
# Analog trace at 1e9 particles/mL
# --------------------------------
# Inspect pulse overlap as concentration increases.
_ = plot_analog_window(
    run_records[2], "Side-scatter signal at 1e9 particles/mL"
)

# %%
# Peak heights at 1e9 particles/mL
# --------------------------------
# Compare the recovered side-scatter peak distribution with the corresponding trace.
_ = plot_peak_heights(run_records[2], concentration_values[2])

# %%
# Analog trace at 5e9 particles/mL
# --------------------------------
# Inspect pulse overlap as concentration increases.
_ = plot_analog_window(
    run_records[3], "Side-scatter signal at 5e9 particles/mL"
)

# %%
# Peak heights at 5e9 particles/mL
# --------------------------------
# Compare the recovered side-scatter peak distribution with the corresponding trace.
_ = plot_peak_heights(run_records[3], concentration_values[3])
