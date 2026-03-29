from FlowCyPy.binary.distributions import Normal
from TypedUnit import ureg

mean = 50 * ureg.meter
standard_deviation = 1 * ureg.meter
cutoff = 2 * ureg.meter

distribution = Normal(
    mean=mean,
    standard_deviation=standard_deviation,
    # cutoff=None
)

res = distribution.sample(30)
print(res)
