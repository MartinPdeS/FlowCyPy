# -*- coding: utf-8 -*-
"""
Compare simulated and experimental flow cytometry bead distributions
====================================================================

This example compares simulated and experimental flow cytometry measurements
for Rosetta bead populations. The simulated data are generated with FlowCyPy,
processed with a dynamic discriminator and a global peak locator, then compared
against an experimental Cytek dataset in the FSC-H versus SSC-H feature space.

The two distributions are displayed side by side using log scaled two
dimensional density plots.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from matplotlib.colors import LogNorm
from MPSPlots.styles import scientific

from TypedUnit import ureg

from FlowCyPy import FlowCytometer
from FlowCyPy import directories
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    SampleFlowRate,
    ScattererCollection,
    SheathFlowRate,
    distributions,
    populations,
)
from FlowCyPy.opto_electronics import (
    Amplifier,
    Detector,
    Digitizer,
    OptoElectronics,
    circuits,
    source,
)
from FlowCyPy.digital_processing import (
    DigitalProcessing,
    discriminator,
    peak_locator,
)


def filter_positive_log_data(
    dataframe,
    *,
    x_column_name,
    y_column_name,
    quantile_limits,
):
    """
    Keep strictly positive data and remove extreme values by quantile filtering.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Input dataframe containing the selected columns.

    x_column_name : str
        Name of the dataframe column used for the x axis.

    y_column_name : str
        Name of the dataframe column used for the y axis.

    quantile_limits : tuple of float
        Lower and upper quantiles used for filtering.

    Returns
    -------
    pandas.DataFrame
        Filtered dataframe containing only the selected columns.
    """
    lower_quantile, upper_quantile = quantile_limits

    positive_dataframe = dataframe.loc[
        (dataframe[x_column_name] > 0)
        & (dataframe[y_column_name] > 0),
        [x_column_name, y_column_name],
    ].copy()

    if positive_dataframe.empty:
        raise ValueError("No strictly positive data available for log scale plotting.")

    x_lower_bound, x_upper_bound = positive_dataframe[x_column_name].quantile(
        [lower_quantile, upper_quantile]
    )
    y_lower_bound, y_upper_bound = positive_dataframe[y_column_name].quantile(
        [lower_quantile, upper_quantile]
    )

    filtered_dataframe = positive_dataframe.loc[
        positive_dataframe[x_column_name].between(x_lower_bound, x_upper_bound)
        & positive_dataframe[y_column_name].between(y_lower_bound, y_upper_bound)
    ].copy()

    if filtered_dataframe.empty:
        raise ValueError("No data remains after quantile filtering.")

    return filtered_dataframe


def validate_log_axis_limits(axis_limits, *, axis_name):
    """
    Validate that axis limits are compatible with logarithmic plotting.

    Parameters
    ----------
    axis_limits : tuple of float or None
        Axis limits to validate.

    axis_name : str
        Name of the axis. Used only for the error message.
    """
    if axis_limits is None:
        return

    if axis_limits[0] <= 0 or axis_limits[1] <= 0:
        raise ValueError(
            f"{axis_name} values must be strictly positive for log scale."
        )


def make_logarithmic_bins(
    dataframe,
    *,
    column_name,
    number_of_bins,
    axis_limits=None,
):
    """
    Create logarithmically spaced bins for a dataframe column.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Input dataframe.

    column_name : str
        Name of the dataframe column used to determine the bin range.

    number_of_bins : int
        Number of logarithmic bin edges.

    axis_limits : tuple of float or None
        Optional explicit axis limits.

    Returns
    -------
    numpy.ndarray
        Logarithmically spaced bin edges.
    """
    bin_minimum = axis_limits[0] if axis_limits is not None else dataframe[column_name].min()
    bin_maximum = axis_limits[1] if axis_limits is not None else dataframe[column_name].max()

    return np.logspace(
        np.log10(bin_minimum),
        np.log10(bin_maximum),
        number_of_bins,
    )


def plot_log_density(
    dataframe,
    *,
    axis,
    x_column_name,
    y_column_name,
    title,
    quantile_limits=(0.001, 0.999),
    number_of_bins=250,
    x_limits=None,
    y_limits=None,
    density_colormap="turbo",
    density_minimum_count=1,
):
    """
    Plot a log scaled two dimensional density map.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Input dataframe containing the two selected channels.

    axis : matplotlib.axes.Axes
        Axis on which the density map is drawn.

    x_column_name : str
        Name of the dataframe column used for the x axis.

    y_column_name : str
        Name of the dataframe column used for the y axis.

    title : str
        Axis title.

    quantile_limits : tuple of float
        Lower and upper quantiles used to reject extreme values.

    number_of_bins : int
        Number of logarithmic bin edges used along each axis.

    x_limits : tuple of float or None
        Optional x axis limits. Values must be strictly positive.

    y_limits : tuple of float or None
        Optional y axis limits. Values must be strictly positive.

    density_colormap : str
        Matplotlib colormap used for the density map.

    density_minimum_count : int
        Minimum count shown in the density map. Lower counts are masked.

    Returns
    -------
    matplotlib.collections.QuadMesh
        Density mesh returned by ``Axes.pcolormesh``.
    """
    validate_log_axis_limits(x_limits, axis_name="x_limits")
    validate_log_axis_limits(y_limits, axis_name="y_limits")

    filtered_dataframe = filter_positive_log_data(
        dataframe,
        x_column_name=x_column_name,
        y_column_name=y_column_name,
        quantile_limits=quantile_limits,
    )

    x_bins = make_logarithmic_bins(
        filtered_dataframe,
        column_name=x_column_name,
        number_of_bins=number_of_bins,
        axis_limits=x_limits,
    )
    y_bins = make_logarithmic_bins(
        filtered_dataframe,
        column_name=y_column_name,
        number_of_bins=number_of_bins,
        axis_limits=y_limits,
    )

    density_counts, _, _ = np.histogram2d(
        filtered_dataframe[x_column_name].to_numpy(),
        filtered_dataframe[y_column_name].to_numpy(),
        bins=[x_bins, y_bins],
    )

    masked_density_counts = np.ma.masked_less(
        density_counts.T,
        density_minimum_count,
    )

    density_mesh = axis.pcolormesh(
        x_bins,
        y_bins,
        masked_density_counts,
        cmap=density_colormap,
        norm=LogNorm(),
        shading="auto",
    )

    axis.set_xscale("log")
    axis.set_yscale("log")

    if x_limits is not None:
        axis.set_xlim(x_limits)

    if y_limits is not None:
        axis.set_ylim(y_limits)

    axis.set_title(title)
    axis.set_xlabel(x_column_name)
    axis.set_ylabel(y_column_name)

    return density_mesh


def plot_simulation_experiment_comparison(
    *,
    simulation_dataframe,
    experimental_dataframe,
    x_column_name="FSC-H",
    y_column_name="SSC-H",
    number_of_bins=250,
    quantile_limits=(0, 1),
    x_limits=(1e1, 5e6),
    y_limits=(1e3, 5e6),
):
    """
    Plot simulated and experimental flow cytometry distributions side by side.

    Parameters
    ----------
    simulation_dataframe : pandas.DataFrame
        Simulated peak feature dataframe.

    experimental_dataframe : pandas.DataFrame
        Experimental peak feature dataframe.

    x_column_name : str
        Name of the dataframe column used for the x axis.

    y_column_name : str
        Name of the dataframe column used for the y axis.

    number_of_bins : int
        Number of logarithmic bin edges used along each axis.

    quantile_limits : tuple of float
        Lower and upper quantiles used for filtering.

    x_limits : tuple of float
        Shared x axis limits.

    y_limits : tuple of float
        Shared y axis limits.

    Returns
    -------
    matplotlib.figure.Figure
        Created figure.
    """
    figure, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(12, 5),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )

    plot_log_density(
        simulation_dataframe,
        axis=axes[0],
        x_column_name=x_column_name,
        y_column_name=y_column_name,
        title="Simulation",
        number_of_bins=number_of_bins,
        quantile_limits=quantile_limits,
        x_limits=x_limits,
        y_limits=y_limits,
    )

    density_mesh = plot_log_density(
        experimental_dataframe,
        axis=axes[1],
        x_column_name=x_column_name,
        y_column_name=y_column_name,
        title="Experiment",
        number_of_bins=number_of_bins,
        quantile_limits=quantile_limits,
        x_limits=x_limits,
        y_limits=y_limits,
    )

    axes[1].set_ylabel("")

    figure.colorbar(
        density_mesh,
        ax=axes,
        label="Counts",
        shrink=0.85,
    )

    return figure


def make_scatterer_collection(
    *,
    diameters,
    concentrations,
    refractive_index,
    medium_refractive_index,
    diameter_standard_deviation_fraction,
):
    """
    Create a scatterer collection from bead diameters and concentrations.

    Parameters
    ----------
    diameters : pint.Quantity
        Particle diameters.

    concentrations : pint.Quantity
        Particle concentrations.

    refractive_index : float
        Particle refractive index.

    medium_refractive_index : float
        Refractive index of the suspending medium.

    diameter_standard_deviation_fraction : float
        Relative standard deviation of each bead diameter distribution.

    Returns
    -------
    FlowCyPy.fluidics.ScattererCollection
        Scatterer collection containing all bead populations.
    """
    scatterer_collection = ScattererCollection()

    for diameter, concentration in zip(diameters, concentrations):
        diameter_distribution = distributions.Normal(
            mean=diameter,
            standard_deviation=diameter * diameter_standard_deviation_fraction,
        )

        sphere_population = populations.SpherePopulation(
            name=f"{diameter:~P}",
            diameter=diameter_distribution,
            refractive_index=refractive_index,
            concentration=concentration,
            medium_refractive_index=medium_refractive_index,
        )

        scatterer_collection.add_population(sphere_population)

    return scatterer_collection


def make_fluidics(
    *,
    scatterer_collection,
):
    """
    Create the fluidics model used for the Rosetta bead simulation.

    Parameters
    ----------
    scatterer_collection : FlowCyPy.fluidics.ScattererCollection
        Scatterer collection containing the bead populations.

    Returns
    -------
    FlowCyPy.fluidics.Fluidics
        Configured fluidics model.
    """
    flow_cell = FlowCell(
        sample_volume_flow=SampleFlowRate.LOW.value,
        sheath_volume_flow=SheathFlowRate.LOW.value,
        width=177 * ureg.micrometer,
        height=433 * ureg.micrometer,
        perfectly_aligned=True,
    )

    return Fluidics(
        scatterer_collection=scatterer_collection,
        flow_cell=flow_cell,
    )


def make_opto_electronics(
    *,
    wavelength,
    bit_depth,
    forward_voltage_range,
    side_voltage_range,
    forward_responsivity,
    side_responsivity,
    forward_current_noise_density,
    side_current_noise_density,
    voltage_noise_density,
    current_noise_density,
    cutoff_frequency,
    time_constant,
    include_shot_noise,
):
    """
    Create the optical, analog, and digitizer model.

    Parameters
    ----------
    wavelength : pint.Quantity
        Excitation wavelength.

    bit_depth : int
        Digitizer bit depth.

    forward_voltage_range : tuple of pint.Quantity
        Minimum and maximum voltage for the FSC channel.

    side_voltage_range : tuple of pint.Quantity
        Minimum and maximum voltage for the SSC channel.

    forward_responsivity : pint.Quantity
        FSC detector responsivity.

    side_responsivity : pint.Quantity
        SSC detector responsivity.

    forward_current_noise_density : pint.Quantity
        FSC detector current noise density.

    side_current_noise_density : pint.Quantity
        SSC detector current noise density.

    voltage_noise_density : pint.Quantity
        Amplifier voltage noise density.

    current_noise_density : pint.Quantity
        Amplifier current noise density.

    cutoff_frequency : pint.Quantity or None
        Optional analog low pass filter cutoff frequency.

    time_constant : pint.Quantity
        Baseline restoration servo time constant.

    include_shot_noise : bool
        Whether source shot noise is included.

    Returns
    -------
    FlowCyPy.opto_electronics.OptoElectronics
        Configured opto electronics model.
    """
    light_source = source.Gaussian(
        waist_z=10e-6 * ureg.meter,
        waist_y=60e-6 * ureg.meter,
        wavelength=wavelength,
        optical_power=200 * ureg.milliwatt,
        bandwidth=10 * ureg.megahertz,
        include_shot_noise=include_shot_noise,
    )

    detectors = [
        Detector(
            name="SSC",
            phi_angle=90 * ureg.degree,
            numerical_aperture=1.1,
            responsivity=side_responsivity,
            bandwidth=10 * ureg.megahertz,
            current_noise_density=side_current_noise_density,
        ),
        Detector(
            name="FSC",
            phi_angle=0 * ureg.degree,
            numerical_aperture=0.1,
            cache_numerical_aperture=0.04,
            responsivity=forward_responsivity,
            bandwidth=10 * ureg.megahertz,
            current_noise_density=forward_current_noise_density,
        ),
    ]

    amplifier = Amplifier(
        gain=1 * ureg.volt / ureg.ampere,
        bandwidth=2 * ureg.megahertz,
        voltage_noise_density=voltage_noise_density,
        current_noise_density=current_noise_density,
    )

    digitizer = Digitizer(
        sampling_rate=10 * ureg.megahertz,
        bit_depth=bit_depth,
        use_auto_range=False,
        output_signed_codes=True,
        channel_range_mode="shared",
    )

    digitizer.set_channel_voltage_range(
        channel_name="FSC",
        minimum_voltage=forward_voltage_range[0],
        maximum_voltage=forward_voltage_range[1],
    )
    digitizer.set_channel_voltage_range(
        channel_name="SSC",
        minimum_voltage=side_voltage_range[0],
        maximum_voltage=side_voltage_range[1],
    )

    analog_processing = []

    if cutoff_frequency is not None:
        analog_processing.append(
            circuits.BesselLowPass(
                cutoff_frequency=cutoff_frequency,
                order=2,
                gain=2,
            )
        )

    analog_processing.append(
        circuits.BaselineRestorationServo(
            time_constant=time_constant,
            initialize_with_first_sample=False,
        )
    )

    return OptoElectronics(
        source=light_source,
        detectors=detectors,
        amplifier=amplifier,
        digitizer=digitizer,
        analog_processing=analog_processing,
    )


def make_digital_processing(
    *,
    threshold,
    pre_buffer,
    post_buffer,
):
    """
    Create the digital processing model used to extract event features.

    Parameters
    ----------
    threshold : str or float
        Dynamic discriminator threshold.

    pre_buffer : int
        Number of samples retained before trigger.

    post_buffer : int
        Number of samples retained after trigger.

    Returns
    -------
    FlowCyPy.digital_processing.DigitalProcessing
        Configured digital processing model.
    """
    dynamic_discriminator = discriminator.DynamicWindow(
        trigger_channel="SSC",
        threshold=threshold,
        pre_buffer=pre_buffer,
        post_buffer=post_buffer,
        max_triggers=-1,
    )

    global_peak_locator = peak_locator.GlobalPeakLocator(
        compute_width=False,
        compute_area=True,
        allow_negative_area=True,
        support=peak_locator.FullWindowSupport(),
        polarity="positive",
        height_mode="peak_to_baseline",
        baseline_mode="edge_mean",
    )

    return DigitalProcessing(
        discriminator=dynamic_discriminator,
        peak_algorithm=global_peak_locator,
    )


def simulate_rosetta_beads(
    *,
    diameters,
    concentrations,
    refractive_index,
    medium_refractive_index,
    diameter_standard_deviation_fraction,
    wavelength,
    bit_depth,
    forward_voltage_range,
    side_voltage_range,
    forward_responsivity,
    side_responsivity,
    forward_current_noise_density,
    side_current_noise_density,
    voltage_noise_density,
    current_noise_density,
    background_power,
    cutoff_frequency,
    time_constant,
    pre_buffer,
    post_buffer,
    threshold,
    run_time,
    include_shot_noise,
):
    """
    Simulate and process a flow cytometry acquisition for Rosetta bead populations.

    Parameters
    ----------
    diameters : pint.Quantity
        Particle diameters.

    concentrations : pint.Quantity
        Particle concentrations.

    refractive_index : float
        Particle refractive index.

    medium_refractive_index : float
        Refractive index of the suspending medium.

    diameter_standard_deviation_fraction : float
        Relative standard deviation of the bead diameter distribution.

    wavelength : pint.Quantity
        Excitation wavelength.

    bit_depth : int
        Digitizer bit depth.

    forward_voltage_range : tuple of pint.Quantity
        Minimum and maximum voltage for the FSC channel.

    side_voltage_range : tuple of pint.Quantity
        Minimum and maximum voltage for the SSC channel.

    forward_responsivity : pint.Quantity
        FSC detector responsivity.

    side_responsivity : pint.Quantity
        SSC detector responsivity.

    forward_current_noise_density : pint.Quantity
        FSC detector current noise density.

    side_current_noise_density : pint.Quantity
        SSC detector current noise density.

    voltage_noise_density : pint.Quantity
        Amplifier voltage noise density.

    current_noise_density : pint.Quantity
        Amplifier current noise density.

    background_power : pint.Quantity
        Background optical power.

    cutoff_frequency : pint.Quantity or None
        Optional analog low pass filter cutoff frequency.

    time_constant : pint.Quantity
        Baseline restoration servo time constant.

    pre_buffer : int
        Number of samples retained before trigger.

    post_buffer : int
        Number of samples retained after trigger.

    threshold : str or float
        Dynamic discriminator threshold.

    run_time : pint.Quantity
        Acquisition duration.

    include_shot_noise : bool
        Whether source shot noise is included.

    Returns
    -------
    FlowCyPy acquisition record
        Processed run record containing peak features.
    """
    scatterer_collection = make_scatterer_collection(
        diameters=diameters,
        concentrations=concentrations,
        refractive_index=refractive_index,
        medium_refractive_index=medium_refractive_index,
        diameter_standard_deviation_fraction=diameter_standard_deviation_fraction,
    )

    fluidics = make_fluidics(
        scatterer_collection=scatterer_collection,
    )

    opto_electronics = make_opto_electronics(
        wavelength=wavelength,
        bit_depth=bit_depth,
        forward_voltage_range=forward_voltage_range,
        side_voltage_range=side_voltage_range,
        forward_responsivity=forward_responsivity,
        side_responsivity=side_responsivity,
        forward_current_noise_density=forward_current_noise_density,
        side_current_noise_density=side_current_noise_density,
        voltage_noise_density=voltage_noise_density,
        current_noise_density=current_noise_density,
        cutoff_frequency=cutoff_frequency,
        time_constant=time_constant,
        include_shot_noise=include_shot_noise,
    )

    cytometer = FlowCytometer(
        fluidics=fluidics,
        background_power=background_power,
    )

    run_record = cytometer.acquire(
        run_time=run_time,
        opto_electronics=opto_electronics,
    )

    digital_processing = make_digital_processing(
        threshold=threshold,
        pre_buffer=pre_buffer,
        post_buffer=post_buffer,
    )

    return cytometer.process_run(
        run_record=run_record,
        digital_processing=digital_processing,
    )


# %%
# Run the simulation
# ------------------
#
# The simulated bead mixture contains six populations with diameters from
# 70 nm to 293 nm. The resulting event features are extracted from the detected
# peaks and converted to a pandas dataframe.

run_record = simulate_rosetta_beads(
    diameters=np.asarray([70, 100, 125, 147, 203, 293]) * ureg.nanometer,
    concentrations=(
        np.asarray([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        * 2
        * 1e6
        * ureg.particle
        / ureg.milliliter
    ),
    refractive_index=1.80,
    medium_refractive_index=1.33,
    diameter_standard_deviation_fraction=0.02,
    wavelength=488 * ureg.nanometer,
    bit_depth=22,
    forward_voltage_range=(
        -3_000_000 * ureg.picovolt,
        3_000_000 * ureg.picovolt,
    ),
    side_voltage_range=(
        -16_000_000 * ureg.picovolt,
        16_000_000 * ureg.picovolt,
    ),
    forward_responsivity=(1 / 6) * ureg.ampere / ureg.watt,
    side_responsivity=1 * ureg.ampere / ureg.watt,
    forward_current_noise_density=1500 * ureg.femtoampere / ureg.sqrt_hertz,
    side_current_noise_density=225 * ureg.femtoampere / ureg.sqrt_hertz,
    voltage_noise_density=0 * ureg.femtovolt / ureg.sqrt_hertz,
    current_noise_density=0 * ureg.femtoampere / ureg.sqrt_hertz,
    background_power=0 * ureg.nanowatt,
    cutoff_frequency=2.3 * ureg.megahertz,
    time_constant=20 * ureg.microsecond,
    pre_buffer=1,
    post_buffer=1,
    threshold="2.8sigma",
    run_time=100 * ureg.millisecond,
    include_shot_noise=True,
)

simulation_dataframe = pd.DataFrame(
    run_record.peaks.get_flattened_dataframe()
)


# %%
# Load the experimental data
# --------------------------
#
# The experimental Cytek Rosetta bead data are loaded from the documentation
# data directory.

example_file_path = Path(__file__).resolve()
documentation_directory = example_file_path.parents[2]

experimental_data_path = (
    documentation_directory
    / "data"
    / "cytek_rosetta_beads.csv"
)

experimental_dataframe = pd.read_csv(experimental_data_path)


# %%
# Compare simulated and experimental distributions
# ------------------------------------------------
#
# The two datasets are shown with identical FSC-H and SSC-H limits so that the
# visual comparison reflects the same feature space.

with plt.style.context(scientific):
    plot_simulation_experiment_comparison(
        simulation_dataframe=simulation_dataframe,
        experimental_dataframe=experimental_dataframe,
        x_column_name="FSC-H",
        y_column_name="SSC-H",
        number_of_bins=250,
        quantile_limits=(0, 1),
        x_limits=(1e1, 5e6),
        y_limits=(2e2, 5e6),
    )

plt.show()