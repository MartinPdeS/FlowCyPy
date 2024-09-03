import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Set random seed for reproducibility
np.random.seed(42)

# Number of events to simulate
n_events = 10000

# Simulate Forward Scatter (FSC-A) and Side Scatter (SSC-A) for different populations
def generate_population(n, fsc_mean, fsc_std, ssc_mean, ssc_std, fl1_mean, fl1_std, fl2_mean, fl2_std):
    fsc = np.random.normal(fsc_mean, fsc_std, n)
    ssc = np.random.normal(ssc_mean, ssc_std, n)
    fl1 = np.random.normal(fl1_mean, fl1_std, n)
    fl2 = np.random.normal(fl2_mean, fl2_std, n)
    return fsc, ssc, fl1, fl2

# Population 1: Small cells with low fluorescence
fsc1, ssc1, fl1_1, fl2_1 = generate_population(int(n_events * 0.4), fsc_mean=200, fsc_std=50,
                                               ssc_mean=100, ssc_std=30, fl1_mean=100, fl1_std=20,
                                               fl2_mean=150, fl2_std=30)

# Population 2: Medium cells with moderate fluorescence
fsc2, ssc2, fl1_2, fl2_2 = generate_population(int(n_events * 0.4), fsc_mean=500, fsc_std=80,
                                               ssc_mean=300, ssc_std=50, fl1_mean=300, fl1_std=50,
                                               fl2_mean=400, fl2_std=60)

# Population 3: Large cells with high fluorescence
fsc3, ssc3, fl1_3, fl2_3 = generate_population(
    int(n_events * 0.2), fsc_mean=800, fsc_std=100,
    ssc_mean=600, ssc_std=70, fl1_mean=700, fl1_std=80,
    fl2_mean=800, fl2_std=90)

# Combine all populations
fsc = np.concatenate([fsc1, fsc2, fsc3])
ssc = np.concatenate([ssc1, ssc2, ssc3])
fl1 = np.concatenate([fl1_1, fl1_2, fl1_3])
fl2 = np.concatenate([fl2_1, fl2_2, fl2_3])

# Create a DataFrame to store the simulated data
data = pd.DataFrame({
    'FSC-A': fsc,
    'SSC-A': ssc,
    'FL1-A': fl1,
    'FL2-A': fl2
})

# Save the simulated dataset to a CSV file
data.to_csv('simulated_flow_cytometry_data.csv', index=False)

# Display the first few rows of the dataset
print(data.head())

# Visualize the simulated dataset
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.scatter(data['FSC-A'], data['SSC-A'], s=1, alpha=0.5)
plt.title('FSC-A vs SSC-A')
plt.xlabel('FSC-A')
plt.ylabel('SSC-A')

plt.subplot(1, 2, 2)
plt.scatter(data['FL1-A'], data['FL2-A'], s=1, alpha=0.5, color='green')
plt.title('FL1-A vs FL2-A')
plt.xlabel('FL1-A')
plt.ylabel('FL2-A')

plt.tight_layout()
plt.show()
