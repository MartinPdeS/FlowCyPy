from FlowCyPy import units
from FlowCyPy.calibration import Calibration

calibration = Calibration(
    bead_diameters=[200, 600, 800, 1000, 1200, 2000]
    * units.nanometer,  # Bead diameters in nanometers,
    illumination_powers=[60, 80, 100, 120, 160, 200, 400]
    * units.milliwatt,  # Illumination powers in milliwatts,
    gain=1 * units.AU / units.photoelectron,  # Gain (a.u. per photoelectron),
    detection_efficiency=7.3e-05
    * units.photoelectron
    / units.nanometer
    ** 2,  # Base detection efficiency at 20 mW (photoelectrons per nm^2) measured at 20 mW,
    background_level=(500.0 * units.nanometer)
    ** 2,  # Background level expressed in nm² (assumed constant),
    number_of_background_events=10_000
    * units.event,  # Number of background events to simulate
    number_of_bead_events=1_000 * units.event,  # Number of bead events per condition
)

calibration.add_beads(
    wavelength=455 * units.nanometer,
    refractive_index=1.4 * units.RIU,
    medium_refractive_index=1.0 * units.RIU,
)

calibration.simulate_signals()

calibration.plot_J(bead_diameters=[200, 600, 1000] * units.nanometer)

_ = calibration.plot_K([60, 80, 100] * units.milliwatt)
