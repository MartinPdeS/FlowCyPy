from TypedUnit import ureg
from TypedUnit import (
    Dimensionless,
    RefractiveIndex,
    Angle,
    Length,
    ElectricField,
    Power,
    Angle,
    FlowRate,
    Viscosity,
)  # noqa: E501


from FlowCyPy.binary import interface_pint

interface_pint.set_ureg(ureg)
