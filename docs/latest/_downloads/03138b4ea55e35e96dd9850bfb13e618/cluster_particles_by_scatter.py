"""
Cluster particles by forward and side scatter
=============================================

Configure a two-population acquisition on the FACSCanto preset. Extract paired peak
heights and use k-means to divide the measured events into two clusters.
The cluster labels describe similarity in scatter space.
"""

from FlowCyPy.digital_processing import classifier
from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg


# %%
# Define the particle mixture
# ---------------------------
# Specify the size, refractive index and concentration of each population.

population_0 = populations.SpherePopulation(
    name="Pop 0",
    medium_refractive_index=distributions.Delta(1.33),
    concentration=1e10 * ureg.particle / ureg.milliliter,
    diameter=distributions.RosinRammler(
        scale=150 * ureg.nanometer,
        shape=50,
        low_cutoff=50.0 * ureg.nanometer,
    ),
    refractive_index=distributions.Normal(
        mean=1.44,
        standard_deviation=0.002,
        low_cutoff=1.33,
    ),
)

population_1 = populations.SpherePopulation(
    name="Pop 1",
    medium_refractive_index=distributions.Delta(1.33),
    concentration=5e17 * ureg.particle / ureg.milliliter,
    diameter=distributions.RosinRammler(
        scale=50 * ureg.nanometer,
        shape=2,
    ),
    refractive_index=distributions.Normal(
        mean=1.44,
        standard_deviation=0.002,
        low_cutoff=1.33,
    ),
    sampling_method=populations.GammaModel(number_of_samples=1_000),
)


# %%
# Load the sample on a FACSCanto
# ------------------------------
# Use the preset's paired forward- and side-scatter detectors and peak locator.
# Dilute the particle mixture 100-fold before acquisition.

instrument = facs_canto(optical_power=200 * ureg.milliwatt, threshold="2sigma")
sample = instrument.fluidics.scatterer_collection
sample.add_population(population_0, population_1)
sample.dilute(100)


# %%
# Run the acquisition
# -------------------
# Acquire and process one millisecond of events.

run_record = instrument.run(run_time=1 * ureg.millisecond, random_state=42)


# %%
# Inspect particle sizes
# ----------------------
# Check the sampled diameter distribution before examining the detector response.

run_record.event_collection.plot(
    x="Diameter",
    yscale="log",
    title="Particle diameter distributions",
)

# %%
# Step 5: Plot Events and Raw Analog Signals
# ------------------------------------------
run_record.event_collection.plot(
    x="side",
    title="Side-scatter event distribution",
)


# %%
# Plot raw analog signals
# -----------------------
figure = run_record.plot_analog(include_scatterer=False)
window_end = (100 * ureg.microsecond).m_as(run_record.signal.analog.attrs["units"]["Time"])
figure.axes[0].set_xlim(0, window_end)


# %%
# Step 6: Plot Triggered Analog Segments
# --------------------------------------
figure = run_record.plot_digital(include_scatterer=False)
window_end = (100 * ureg.microsecond).m_as(run_record.signal.digital.attrs["units"]["Time"])
figure.axes[0].set_xlim(0, window_end)


# %%
# Step 7: Plot Peak Features
# --------------------------
run_record.plot_peaks(
    x=("forward", "Height"),
    title="Forward-scatter peak heights",
)


# %%
# Step 8: Classify Events from Peak Features
# ------------------------------------------
class_ = classifier.KmeansClassifier(number_of_clusters=2)

classification = class_.run(
    dataframe=run_record.peaks.unstack("Detector"),
    features=["Height"],
    detectors=["side", "forward"],
)

_ = classification.plot(x=("side", "Height"), y=("forward", "Height"))
