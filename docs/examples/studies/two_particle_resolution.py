"""
Resolving two overlapping particle pulses
=========================================

Two particles can arrive in the same trigger window even though the
discriminator reports only one event. This example sends two identical
Gaussian voltage pulses through the dynamic-window discriminator and varies
their separation. The noiseless signal isolates the role of pulse overlap.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from FlowCyPy import EventCollection
from FlowCyPy.digital_processing.discriminator import DynamicWindow
from FlowCyPy.fluidics.population_events import PopulationEvents
from FlowCyPy.run_record import RunRecord, SignalRecord
from FlowCyPy.sub_frames.events import EventDataFrame
from FlowCyPy.units import ureg


sample_times = np.linspace(0, 20, 1001)  # microseconds
pulse_width = 1.0  # Gaussian standard deviation in microseconds
pulse_height = 1.0  # millivolts
threshold = 0.4  # millivolts
discriminator = DynamicWindow(
    trigger_channel="side",
    threshold=threshold * ureg.millivolt,
    pre_buffer=0,
    post_buffer=0,
)


def simulate_pair(*, separation: float) -> tuple[np.ndarray, dict]:
    """Trigger on the sum of two Gaussian pulses with known arrival times.

    Parameters
    ----------
    separation : float
        Time between pulse centers in microseconds.

    Returns
    -------
    signal : ndarray
        Voltage in millivolts at each sample time.
    statistics : dict
        Counts of trigger windows by the number of assigned arrivals.
    """
    arrival_times = np.array([10 - separation / 2, 10 + separation / 2])
    offsets = sample_times[:, None] - arrival_times
    voltage = pulse_height * np.exp(-0.5 * (offsets / pulse_width) ** 2).sum(axis=1)
    triggered = discriminator.run_with_dict(
        {"Time": sample_times * ureg.microsecond, "side": voltage * ureg.millivolt}
    )
    trigger_times = triggered["Time"].to("microsecond")
    digital = pd.DataFrame(
        {"Time": trigger_times.magnitude},
        index=pd.Index(triggered["segment_id"], name="SegmentID"),
    )
    digital.attrs["units"] = {"Time": trigger_times.units}

    events = EventDataFrame()
    events.set_column("Time", arrival_times, unit=ureg.microsecond)
    population = PopulationEvents(
        dataframe=events,
        population=None,
        sampling_method=None,
        name="Identical particles",
        scatterer_type="Sphere",
        metadata={},
    )
    record = RunRecord(
        run_time=sample_times[-1] * ureg.microsecond,
        event_collection=EventCollection(events_list=[population]),
        signal=SignalRecord(digital=digital),
    )
    return voltage, record.coincidence_statistics()


# %%
# When the voltage stays above the threshold between pulses, both arrivals
# share one window. Once the voltage falls below the threshold between the
# pulses, each arrival gets its own window. The transition depends on the pulse
# shape, sampling rate, and trigger threshold. A single-event window contains
# one known arrival. Peak localization is a separate measurement.
figure, axes = plt.subplots(1, 3, figsize=(11, 3.3), layout="constrained")
for axis, separation in zip(axes[:2], (2.0, 5.0)):
    voltage, statistics = simulate_pair(separation=separation)
    axis.plot(sample_times, voltage)
    axis.axhline(threshold, color="0.4", linestyle="--", label="Threshold")
    axis.set(
        title=f'{separation:g} µs apart\nTrigger windows = {statistics["TotalTriggerSegments"]}',
        xlabel="Time (µs)",
        xlim=(5, 15),
        ylim=(0, 1.35),
    )
axes[0].set_ylabel("Voltage (mV)")
axes[0].legend()

separations = np.linspace(0, 7, 29)
sweep = pd.DataFrame(
    [simulate_pair(separation=separation)[1] for separation in separations]
)
axes[2].step(
    separations, sweep["SingleEventSegments"], where="mid", label="One arrival"
)
axes[2].step(
    separations, sweep["CoincidentSegments"], where="mid", label="Two arrivals"
)
axes[2].set(
    xlabel="Pulse separation (µs)", ylabel="Trigger windows", yticks=(0, 1, 2)
)
axes[2].legend()
plt.show()
