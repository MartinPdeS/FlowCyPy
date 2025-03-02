from FlowCyPy.units import meter, joule, second, farad, kelvin, coulomb
import numpy as np


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


class PhysicalConstant:
    h = 6.62607015e-34 * joule * second  # Planck constant
    c = 3e8 * meter / second  # Speed of light
    epsilon_0 = 8.8541878128e-12 * farad / meter  # Permtivitty of vacuum
    pi = np.pi  # Pi, what else?
    kb = 1.380649e-23 * joule / kelvin  # Botlzmann constant
    e = 1.602176634e-19 * coulomb  # Electron charge
