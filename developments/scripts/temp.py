import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson, norm

# Mean photon count
mean_photons_low = 5   # Low mean (high skewness)
mean_photons_high = 50 # High mean (Gaussian-like)

# Simulate Poisson shot noise
photon_counts_low = poisson.rvs(mean_photons_low, size=10000)
photon_counts_high = poisson.rvs(mean_photons_high, size=10000)

# Plot histograms
plt.figure(figsize=(12, 6))
plt.hist(photon_counts_low, bins=30, density=True, alpha=0.6, label=f"Poisson (μ={mean_photons_low})")
plt.hist(photon_counts_high, bins=30, density=True, alpha=0.6, label=f"Poisson (μ={mean_photons_high})")

# Overlay Gaussian approximations
x_low = np.linspace(0, 20, 100)
x_high = np.linspace(30, 70, 100)
plt.plot(x_low, norm.pdf(x_low, loc=mean_photons_low, scale=np.sqrt(mean_photons_low)),
         'r--', label=f"Gaussian Approx (μ={mean_photons_low})")
plt.plot(x_high, norm.pdf(x_high, loc=mean_photons_high, scale=np.sqrt(mean_photons_high)),
         'g--', label=f"Gaussian Approx (μ={mean_photons_high})")

plt.title("Photon Shot Noise: Poisson vs Gaussian Approximation")
plt.xlabel("Photon Counts")
plt.ylabel("Density")
plt.legend()
plt.show()