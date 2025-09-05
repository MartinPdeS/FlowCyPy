# -*- coding: utf-8 -*-
import numpy as np
from TypedUnit import ureg


class PhysicalConstant:
    h = 6.62607015e-34 * ureg.joule * ureg.second  # Planck constant
    c = 3e8 * ureg.meter / ureg.second  # Speed of light
    epsilon_0 = 8.8541878128e-12 * ureg.farad / ureg.meter  # Permtivitty of vacuum
    pi = np.pi  # Pi, what else?
    kb = 1.380649e-23 * ureg.joule / ureg.kelvin  # Botlzmann constant
    e = 1.602176634e-19 * ureg.coulomb  # Electron charge
