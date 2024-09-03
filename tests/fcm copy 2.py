import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths
from FlowCytometry import FlowCytometer, PulseAnalyzer


# Example Usage

# Simulate flow cytometry data with added realism
flow_cytometer = FlowCytometer(
    n_events=1000,
    time_points=1000,
    noise_level=0.05,
    baseline_shift=0.01,
    saturation_level=100000
)
flow_cytometer.simulate_pulse()
flow_cytometer.plot_signals()

# Analyze FSC signal
fsc_analyzer = PulseAnalyzer(flow_cytometer.fsc_raw_signal, height_threshold=100)
fsc_analyzer.find_peaks()
fsc_analyzer.calculate_widths()
fsc_analyzer.calculate_areas()
fsc_analyzer.display_features()

# Analyze SSC signal
ssc_analyzer = PulseAnalyzer(flow_cytometer.ssc_raw_signal, height_threshold=50)
ssc_analyzer.find_peaks()
ssc_analyzer.calculate_widths()
ssc_analyzer.calculate_areas()
ssc_analyzer.display_features()
