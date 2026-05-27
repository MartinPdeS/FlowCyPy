import argparse

import matplotlib.pyplot as plt
import numpy as np

from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    SampleFlowRate,
    SheathFlowRate,
    distributions,
    populations,
)
from FlowCyPy.opto_electronics import Amplifier, Detector, Digitizer, OptoElectronics, source
from FlowCyPy.units import  ureg


DETECTOR_NAME = "side"


def build_flow_cytometer(sampling_method, concentration):
    flow_cell = FlowCell(
        sample_volume_flow=SampleFlowRate.MEDIUM.value,
        sheath_volume_flow=SheathFlowRate.MEDIUM.value,
        width=400 * ureg.micrometer,
        height=150 * ureg.micrometer,
    )

    scatterer_collection = ScattererCollection()
    scatterer_collection.add_population(
        populations.SpherePopulation(
            name="Delta population",
            medium_refractive_index=distributions.Delta(1.33 * ureg.RIU),
            concentration=concentration,
            diameter=distributions.Delta(200 * ureg.nanometer),
            refractive_index=distributions.Delta(1.40 * ureg.RIU),
            sampling_method=sampling_method,
        )
    )

    fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

    return FlowCytometer(fluidics=fluidics, background_power=0 * ureg.milliwatt)


def build_opto_electronics(source_name):
    source_kwargs = dict(
        waist_z=10 * ureg.micrometer,
        waist_y=60 * ureg.micrometer,
        wavelength=405 * ureg.nanometer,
        optical_power=200 * ureg.milliwatt,
        rin=-140 * ureg.dB_per_Hz,
        bandwidth=20 * ureg.megahertz,
        include_shot_noise=False,
        include_rin_noise=False,
    )

    if source_name == "gaussian":
        source_model = source.Gaussian(**source_kwargs)
    elif source_name == "flattop":
        source_model = source.FlatTop(**source_kwargs)
    else:
        raise ValueError(f"Unsupported source: {source_name}")

    detector = Detector(
        name=DETECTOR_NAME,
        phi_angle=90 * ureg.degree,
        numerical_aperture=1.1,
        responsivity=1 * ureg.ampere / ureg.watt,
        dark_current=0 * ureg.ampere,
        current_noise_density=0 * ureg.ampere / ureg.sqrt_hertz,
    )

    amplifier = Amplifier(
        gain=1 * ureg.volt / ureg.ampere,
        bandwidth=20 * ureg.megahertz,
        voltage_noise_density=0 * ureg.nanovolt / ureg.sqrt_hertz,
        current_noise_density=0 * ureg.femtoampere / ureg.sqrt_hertz,
    )

    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=14,
        use_auto_range=True,
        channel_range_mode="shared",
    )

    return OptoElectronics(
        detectors=[detector],
        source=source_model,
        amplifier=amplifier,
        digitizer=digitizer,
        analog_processing=tuple(),
    )


def run_model(label, sampling_method, concentration, run_time, source_name):
    cytometer = build_flow_cytometer(
        sampling_method=sampling_method,
        concentration=concentration,
    )
    opto_electronics = build_opto_electronics(source_name=source_name)

    run_record = cytometer.acquire(
        run_time=run_time,
        opto_electronics=opto_electronics,
    )

    population_events = next(iter(run_record.event_collection))
    analog = run_record.signal.analog

    signal = analog[DETECTOR_NAME].to("millivolt")
    time = analog["Time"].to("microsecond")

    return {
        "label": label,
        "time": time,
        "signal": signal,
        "events": population_events,
        "stats": {
            "mean": signal.mean(),
            "std": signal.std(),
            "max": signal.max(),
        },
    }


def plot_comparison(explicit_result, gamma_result, concentration, run_time, source_name):
    figure, axes = plt.subplots(2, 1, figsize=(11, 8), constrained_layout=True)

    for result in (explicit_result, gamma_result):
        axes[0].plot(
            result["time"].magnitude,
            result["signal"].magnitude,
            label=(
                f"{result['label']} | mean={result['stats']['mean'].magnitude:.3g} "
                f"{result['signal'].units:~P} | std={result['stats']['std'].magnitude:.3g}"
            ),
            linewidth=1.4,
        )

    combined_signal = np.concatenate(
        [explicit_result["signal"].magnitude, gamma_result["signal"].magnitude]
    )
    histogram_bins = np.linspace(combined_signal.min(), combined_signal.max(), 120)

    for result in (explicit_result, gamma_result):
        axes[1].hist(
            result["signal"].magnitude,
            bins=histogram_bins,
            histtype="step",
            linewidth=1.6,
            density=False,
            label=result["label"],
        )

    axes[0].set_title(
        "Explicit vs Gamma analog trace comparison\n"
        f"source={source_name}, concentration={concentration:~P}, run_time={run_time:~P}"
    )
    axes[0].set_ylabel(f"{DETECTOR_NAME} [{explicit_result['signal'].units:~P}]")
    axes[0].legend()

    axes[1].set_xlabel(f"{DETECTOR_NAME} [{explicit_result['signal'].units:~P}]")
    axes[1].set_ylabel("Count")
    axes[1].set_yscale("log")
    axes[1].legend()

    event_count = explicit_result["events"].metadata.get("NumberOfEvents", 0)
    expected_particles = gamma_result["events"].metadata.get(
        "ExpectedNumberOfParticles", 0
    )
    axes[1].set_title(
        "Trace histogram\n"
        f"explicit events={event_count}, gamma expected particles/bin={expected_particles:.3g}"
    )

    return figure


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Compare detector traces from ExplicitModel and GammaModel for a single "
            "delta-valued population."
        )
    )
    parser.add_argument(
        "--concentration",
        type=float,
        default=5e11,
        help="Population concentration in particle / milliliter.",
    )
    parser.add_argument(
        "--run-time-us",
        type=float,
        default=20.0,
        help="Acquisition duration in microsecond.",
    )
    parser.add_argument(
        "--gamma-samples",
        type=int,
        default=10000,
        help="Number of support samples used by GammaModel.",
    )
    parser.add_argument(
        "--source",
        choices=("gaussian", "flattop"),
        default="gaussian",
        help="Source profile used by both simulations.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional path to save the figure instead of showing it.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    concentration = args.concentration * ureg.particle / ureg.milliliter
    run_time = args.run_time_us * ureg.microsecond

    explicit_result = run_model(
        label="ExplicitModel",
        sampling_method=populations.ExplicitModel(),
        concentration=concentration,
        run_time=run_time,
        source_name=args.source,
    )
    gamma_result = run_model(
        label="GammaModel",
        sampling_method=populations.GammaModel(number_of_samples=args.gamma_samples),
        concentration=concentration,
        run_time=run_time,
        source_name=args.source,
    )

    print(
        "ExplicitModel:",
        f"events={explicit_result['events'].metadata.get('NumberOfEvents', 0)}",
        f"mean={explicit_result['stats']['mean']:~P}",
        f"std={explicit_result['stats']['std']:~P}",
        f"max={explicit_result['stats']['max']:~P}",
    )
    print(
        "GammaModel:",
        f"expected_particles_per_bin={gamma_result['events'].metadata.get('ExpectedNumberOfParticles', 0):.6g}",
        f"mean={gamma_result['stats']['mean']:~P}",
        f"std={gamma_result['stats']['std']:~P}",
        f"max={gamma_result['stats']['max']:~P}",
    )

    figure = plot_comparison(
        explicit_result=explicit_result,
        gamma_result=gamma_result,
        concentration=concentration,
        run_time=run_time,
        source_name=args.source,
    )

    if args.output:
        figure.savefig(args.output, dpi=200)
        print(f"Saved figure to {args.output}")
        return

    plt.show()


if __name__ == "__main__":
    main()