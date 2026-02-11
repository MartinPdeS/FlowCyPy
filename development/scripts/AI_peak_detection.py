from FlowCyPy.binary.distributions import Normal, RosinRammler, LogNormal
from FlowCyPy.units import ureg
import matplotlib.pyplot as plt


dist = RosinRammler(
    scale=120 * ureg.nanometer,
    shape=1.3 * ureg.nanometer,
    high_cutoff=250 * ureg.nanometer,
)


# dist = Normal(
#     mean=1.0 * ureg.micrometer,
#     standard_deviation=100.0 * ureg.nanometer,
#     # low_cutoff=0.9 * ureg.micrometer,
#     high_cutoff=1.1 * ureg.micrometer,
# )


res = dist.sample(30_000)

print(res)
plt.figure()
plt.hist(res, bins=200)
plt.title(f"len: {len(res)}")
plt.show()
