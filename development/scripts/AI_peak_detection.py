from FlowCyPy.binary.distributions import Normal, RosinRammler, LogNormal
from FlowCyPy.units import ureg
import matplotlib.pyplot as plt

dist = Normal(
    mean=10 * ureg.meter,
    standard_deviation=1000 * ureg.meter,
    # low_cutoff = 8 * ureg.meter,
    # high_cutoff = 12 * ureg.meter,
    strict_sampling=True,
)


# dist = RosinRammler(
#     scale=10 * ureg.meter,
#     shape=2 * ureg.meter,
#     low_cutoff = 8 * ureg.meter,
#     # high_cutoff = 12 * ureg.meter,
#     strict_sampling=True
# )


res = dist.sample(3000)

print(res)
# print(len(res))
plt.figure()
plt.hist(res, bins=100)
plt.show()
