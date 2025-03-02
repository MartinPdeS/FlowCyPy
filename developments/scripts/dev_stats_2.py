import numpy as np
import matplotlib.pyplot as plt

# Generate Poisson data for different means
mean_values = [1, 5, 20, 50]
poisson_data = [np.random.poisson(lam=mean, size=10000) for mean in mean_values]

# Plot histograms
plt.figure(figsize=(12, 6))
for i, data in enumerate(poisson_data):
    plt.hist(data, bins=50, alpha=0.7, label=f"λ = {mean_values[i]}", density=True)

plt.legend()
plt.title("Histograms of Poisson Distributions")
plt.xlabel("Value")
plt.ylabel("Density")
plt.show()
