"""
FACSCanto simulation
====================

This tutorial demonstrates how to set up and run a flow cytometry simulation using the FacsCanto instance from the FlowCyPy library.
It includes defining a particle population, configuring the flow cytometer, running the simulation, and visualizing the results.
"""

# %%
# Step 0: Global Settings and Imports
# -----------------------------------
from FlowCyPy.units import ureg
from FlowCyPy.presets.flow_cytometer import FacsCanto, SampleFlowRate, SheathFlowRate
from FlowCyPy.fluidics import populations, distributions



# %%
# Define the sample
# -----------------
# Use a narrow particle-size distribution to inspect the preset instrument response.

diameter = distributions.RosinRammler(
    scale=60 * ureg.nanometer,
    shape=150,
)

medium_refractive_index = 1.33

refractive_index = distributions.Normal(mean=1.44, standard_deviation=0.002)

population_0 = populations.SpherePopulation(
    name="Pop 0",
    concentration=5e9 * ureg.particle / ureg.milliliter,
    diameter=diameter,
    medium_refractive_index=medium_refractive_index,
    refractive_index=refractive_index,
)


# %%
# Configure the instrument
# ------------------------
# Choose flow rates, laser power, noise sources and the trigger threshold.

facs_canto = FacsCanto(
    sample_volume_flow=SampleFlowRate.MEDIUM.value,
    sheath_volume_flow=SheathFlowRate.DEFAULT.value,
    optical_power=200 * ureg.milliwatt,
    threshold="3sigma",
    include_shot_noise=True,
    include_rin_noise=True,
    background_power=0.01 * ureg.nanowatt,
)

facs_canto.add_population(population_0)

facs_canto.dilute_sample(factor=100)


# %%
# Acquire the sample
# ------------------
# Dilute the population and simulate a short acquisition.

run_record = facs_canto.run(run_time=0.2 * ureg.millisecond)


# %%
# Inspect the analog signal
# -------------------------
# Look for individual pulses and the noise baseline in each detector channel.

figure = run_record.plot_analog(
    figure_size=(12, 6),
    include_scatterer=False,
)
analog_signal = run_record.signal.analog
time_unit = analog_signal.attrs["units"]["Time"]
detector_names = [column for column in analog_signal.columns if column != "Time"]

for axis, detector_name in zip(figure.axes, detector_names):
    detector_label = {"side": "SSC", "forward": "FSC"}.get(
        detector_name, detector_name
    )
    voltage_unit = format(analog_signal.attrs["units"][detector_name], "~")
    axis.set_ylabel(f"{detector_label} [{voltage_unit}]", fontsize=11)
    axis.yaxis.set_label_position("left")
    axis.yaxis.set_ticks_position("left")
    axis.tick_params(labelsize=9)
    axis.grid(True, alpha=0.2)

legend_axis = next(
    (axis for axis in figure.axes if axis.get_legend() is not None),
    None,
)
if legend_axis is not None:
    legend = legend_axis.get_legend()
    handles, labels = legend_axis.get_legend_handles_labels()
    legend.remove()
    figure.legend(
        handles,
        [
            "Analog signal" if "analog" in label.lower() else "Trigger threshold"
            for label in labels
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=len(handles),
        frameon=False,
        fontsize=9,
    )

figure.suptitle("FACSCanto analog detector signals", fontsize=13)
figure.axes[-1].set_xlabel(f"Time [{format(time_unit, '~')}]", fontsize=11)
figure.tight_layout(rect=(0, 0, 1, 0.88))
