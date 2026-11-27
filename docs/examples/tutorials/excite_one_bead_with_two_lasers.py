"""
Excite the same bead with two lasers
====================================

Compare the green fluorescence excited by 405 nm and 488 nm lasers at a
single interrogation spot. The preset supplies a shared Gaussian beam profile.
"""

import matplotlib.pyplot as plt
from FlowCyPy.detectors.photomultipliers import pmt
from FlowCyPy.dyes import fitc
from FlowCyPy.fluorescence import Bandpass, Label
from FlowCyPy.opto_electronics import Laser
from FlowCyPy.samples.beads import microbeads
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

violet = Laser(wavelength=405 * ureg.nm, optical_power=8 * ureg.mW, rin=-145 * ureg.dB_per_Hz)
blue = Laser(wavelength=488 * ureg.nm, optical_power=20 * ureg.mW)
instrument = facs_canto(lasers=[violet, blue])

# %%
# Specify the excitation strength at each line. These fractions are
# illustrative. For quantitative use, read them from the dye absorption
# spectrum in the intended medium. Each bead carries one shared dye count.

dye = fitc(relative_absorption={violet.wavelength: 0.1, blue.wavelength: 0.8})
label = Label(fluorophore=dye, molecules_per_particle=10_000)
beads = microbeads(
    name="FITC beads",
    diameter=300 * ureg.nm,
    refractive_index=1.59,
    concentration=1e8 * ureg.particle / ureg.mL,
    labels=[label],
)
instrument.fluidics.scatterer_collection.add_population(beads)

optical_filter = Bandpass(center=530 * ureg.nm, width=30 * ureg.nm)
green = pmt(
    name="Green",
    phi_angle=90 * ureg.degree,
    numerical_aperture=0.8,
    signals=("fluorescence",),
    optical_filter=optical_filter,
)
optics = instrument.opto_electronics
optics.detectors = [*optics.detectors, green]

# %%
# Each event column below is in pW. The wavelength in brackets identifies
# the excitation laser. The green PMT records one combined voltage waveform.

record = instrument.acquire(run_time=200 * ureg.microsecond, random_state=42)
events = record.event_collection[0]
for channel in ("Green[405 nm]", "Green[488 nm]", "Green"):
    print(f"{channel}: {events.get_quantity(channel).m_as('pW')[:3]} pW")

# %%
# Compare the forward scatter, side scatter and combined green fluorescence
# voltages on the same acquisition time axis.

record.plot_analog(include_scatterer=False)
plt.show()
