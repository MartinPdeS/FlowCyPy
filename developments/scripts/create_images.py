import numpy as np
import matplotlib.pyplot as plt
from FlowCyPy import distribution
from FlowCyPy.units import nanometer, particle
from pathlib import Path
import FlowCyPy



save_path = Path(FlowCyPy.__file__).parent.parent / "docs/images/distributions"


# Set random seed for reproducibility
np.random.seed(3)

# Define the number of particles to generate
n_particles = 10000 * particle


# 1. Normal Distribution
distributions = [
    distribution.Normal(mean=100 * nanometer, std_dev=10 * nanometer),
    distribution.LogNormal(mean=100 * nanometer, std_dev=0.25 * nanometer),
    distribution.RosinRammler(characteristic_size=50 * nanometer, spread=2.0),
    distribution.Weibull(scale=100 * nanometer, shape=1.5 * nanometer),
    distribution.Delta(position=100 * nanometer),
    distribution.Uniform(lower_bound=50 * nanometer, upper_bound=150 * nanometer)
]


for dist in distributions:
    name = type(dist).__name__
    sizes = dist.generate(n_particles)
    figure, ax = plt.subplots(1, 1, figsize=(8, 4))
    ax.hist(sizes, bins=50, color='skyblue', edgecolor='black')
    ax.set_title(f'{repr(dist)} Distribution')
    ax.set_xlabel('Size (nm)')
    ax.set_ylabel('Frequency')
    plt.tight_layout()
    file_directory = save_path / f'{name}.png'
    plt.savefig(file_directory)
    # plt.show()
