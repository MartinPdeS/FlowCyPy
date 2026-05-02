import numpy as np
import pytest
import matplotlib.pyplot as plt

from FlowCyPy.fluidics.event_collection import EventCollection
from FlowCyPy.fluidics.population_events import PopulationEvents
from FlowCyPy.sub_frames.events import EventDataFrame
from FlowCyPy.units import ureg


def make_population_events(name: str) -> PopulationEvents:
    dataframe = EventDataFrame()
    dataframe.set_column("Time", [0.0, 1.0], unit=ureg.second)
    dataframe.set_column("Diameter", [1000.0, 2500.0], unit=ureg.nanometer)
    dataframe.set_column("Signal", [1.0, 2.0], unit=ureg.volt)

    return PopulationEvents(
        dataframe=dataframe,
        population=object(),
        sampling_method=object(),
        name=name,
        scatterer_type="Sphere",
        metadata={"nested": {"value": 1}},
    )


def make_population_events_with_invalid_values(name: str) -> PopulationEvents:
    dataframe = EventDataFrame()
    dataframe.set_column("Time", [0.0, 1.0, 2.0], unit=ureg.second)
    dataframe.set_column("Diameter", [1000.0, np.inf, 2500.0], unit=ureg.nanometer)
    dataframe.set_column("Signal", [1.0, 2.0, 3.0], unit=ureg.volt)

    return PopulationEvents(
        dataframe=dataframe,
        population=object(),
        sampling_method=object(),
        name=name,
        scatterer_type="Sphere",
        metadata={"nested": {"value": 1}},
    )


def test_convert_units_inplace_updates_population_dataframes() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    converted = collection.convert_units(
        column_units={"Time": ureg.millisecond, "Diameter": ureg.micrometer}
    )

    assert converted is collection
    assert collection[0].dataframe.get_unit("Time") == ureg.millisecond
    assert collection[0].dataframe.get_unit("Diameter") == ureg.micrometer
    assert collection[0].dataframe.get_unit("Signal") == ureg.volt
    assert np.allclose(collection[0].get_quantity("Time").magnitude, [0.0, 1000.0])
    assert np.allclose(collection[0].get_quantity("Diameter").magnitude, [1.0, 2.5])


def test_convert_units_with_copy_leaves_original_unchanged() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    converted = collection.convert_units(
        column_units={"Diameter": ureg.micrometer},
        inplace=False,
    )

    assert converted is not collection
    assert converted[0] is not collection[0]
    assert collection[0].dataframe.get_unit("Diameter") == ureg.nanometer
    assert converted[0].dataframe.get_unit("Diameter") == ureg.micrometer
    assert np.allclose(collection[0].get_quantity("Diameter").magnitude, [1000.0, 2500.0])
    assert np.allclose(converted[0].get_quantity("Diameter").magnitude, [1.0, 2.5])
    assert converted[0].metadata is not collection[0].metadata
    assert converted[0].metadata["nested"] is not collection[0].metadata["nested"]


def test_convert_units_requires_mapping_input() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    with pytest.raises(TypeError, match="column_units must be a mapping"):
        collection.convert_units({"Diameter", "nanometer"})


def test_plot_2d_hides_all_marginal_ticks_and_labels() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_2d(x="Diameter", y="Signal")
    joint_ax, marginal_x_ax, marginal_y_ax = figure.axes

    figure.canvas.draw()

    for ax in (marginal_x_ax, marginal_y_ax):
        assert all(not tick.get_visible() for tick in ax.get_xticklabels())
        assert all(not tick.get_visible() for tick in ax.get_yticklabels())
        assert all(not tick.get_visible() for tick in ax.get_xticklines())
        assert all(not tick.get_visible() for tick in ax.get_yticklines())

    assert any(tick.get_visible() for tick in joint_ax.xaxis.get_ticklines())
    assert any(tick.get_visible() for tick in joint_ax.yaxis.get_ticklines())
    assert all(not tick.get_visible() for tick in joint_ax.xaxis.get_ticklines()[1::2])
    assert all(not tick.get_visible() for tick in joint_ax.yaxis.get_ticklines()[1::2])

    plt.close(figure)


def test_plot_2d_applies_requested_axis_scales() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_2d(
        x="Diameter",
        y="Signal",
        xscale="log",
        yscale="linear",
    )
    joint_ax, marginal_x_ax, marginal_y_ax = figure.axes

    assert joint_ax.get_xscale() == "log"
    assert joint_ax.get_yscale() == "linear"
    assert marginal_x_ax.get_xscale() == "log"
    assert marginal_y_ax.get_yscale() == "linear"

    plt.close(figure)


def test_plot_2d_filters_non_finite_values_for_log_scale() -> None:
    collection = EventCollection(
        events_list=[make_population_events_with_invalid_values(name="A")]
    )

    figure = collection.plot_2d(
        x="Diameter",
        y="Signal",
        xscale="log",
    )
    joint_ax = figure.axes[0]

    figure.canvas.draw()

    assert joint_ax.get_xscale() == "log"

    plt.close(figure)


def test_plot_2d_applies_optional_layout_arguments() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_2d(
        x="Diameter",
        y="Signal",
        figure_size=(7, 5),
        title="Custom Title",
        xlabel="Custom X",
        ylabel="Custom Y",
        xlim=(900, 3000),
        ylim=(0.5, 3.0),
    )
    joint_ax = figure.axes[0]

    assert tuple(figure.get_size_inches()) == pytest.approx((7.0, 5.0))
    assert figure._suptitle.get_text() == "Custom Title"
    assert joint_ax.get_xlabel() == "Custom X"
    assert joint_ax.get_ylabel() == "Custom Y"
    assert joint_ax.get_xlim() == pytest.approx((900.0, 3000.0))
    assert joint_ax.get_ylim() == pytest.approx((0.5, 3.0))

    plt.close(figure)


def test_plot_2d_applies_requested_marginal_bin_count() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_2d(
        x="Diameter",
        y="Signal",
        marginal_nbins=5,
    )
    _, marginal_x_ax, marginal_y_ax = figure.axes

    assert len(marginal_x_ax.patches) == 5
    assert len(marginal_y_ax.patches) == 5

    plt.close(figure)


def test_plot_2d_marginals_have_visible_bar_edges() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_2d(
        x="Diameter",
        y="Signal",
    )
    _, marginal_x_ax, marginal_y_ax = figure.axes

    assert all(patch.get_linewidth() > 0 for patch in marginal_x_ax.patches)
    assert all(patch.get_linewidth() > 0 for patch in marginal_y_ax.patches)

    plt.close(figure)


def test_plot_2d_can_save_figure(tmp_path) -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])
    output_path = tmp_path / "event_collection_plot.png"

    figure = collection.plot_2d(
        x="Diameter",
        y="Signal",
        save_as=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    plt.close(figure)


def test_plot_hist_applies_requested_axis_scales() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_hist(
        x="Diameter",
        xscale="log",
        yscale="linear",
    )
    ax = figure.axes[0]

    assert ax.get_xscale() == "log"
    assert ax.get_yscale() == "linear"

    plt.close(figure)


def test_plot_hist_applies_optional_layout_arguments() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_hist(
        x="Diameter",
        figure_size=(7, 5),
        title="Custom Hist Title",
        xlabel="Custom Hist X",
        ylabel="Custom Hist Y",
        xlim=(900, 3000),
        ylim=(0.5, 3.0),
    )
    ax = figure.axes[0]

    assert tuple(figure.get_size_inches()) == pytest.approx((7.0, 5.0))
    assert ax.get_title() == "Custom Hist Title"
    assert ax.get_xlabel() == "Custom Hist X"
    assert ax.get_ylabel() == "Custom Hist Y"
    assert ax.get_xlim() == pytest.approx((900.0, 3000.0))
    assert ax.get_ylim() == pytest.approx((0.5, 3.0))

    plt.close(figure)


def test_plot_hist_filters_non_finite_values_for_log_scale() -> None:
    collection = EventCollection(
        events_list=[make_population_events_with_invalid_values(name="A")]
    )

    figure = collection.plot_hist(
        x="Diameter",
        xscale="log",
    )
    ax = figure.axes[0]

    figure.canvas.draw()

    assert ax.get_xscale() == "log"

    plt.close(figure)


def test_plot_hist_has_visible_bar_edges() -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])

    figure = collection.plot_hist(x="Diameter")
    ax = figure.axes[0]

    assert all(patch.get_linewidth() > 0 for patch in ax.patches)

    plt.close(figure)


def test_plot_hist_can_save_figure(tmp_path) -> None:
    collection = EventCollection(events_list=[make_population_events(name="A")])
    output_path = tmp_path / "event_collection_hist.png"

    figure = collection.plot_hist(
        x="Diameter",
        save_as=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    plt.close(figure)