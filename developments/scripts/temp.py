import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

# Define the theoretical distributions
x_mean, x_std = 0, 1  # Mean and Std for x
y_mean, y_std = 1, 2  # Mean and Std for y

# Create a grid of points
x = np.linspace(-4, 4, 100)
y = np.linspace(-4, 8, 100)
X, Y = np.meshgrid(x, y)

print()

# Evaluate the theoretical PDF for the bivariate distribution
Z = norm.pdf(X, loc=x_mean, scale=x_std) * norm.pdf(Y, loc=y_mean, scale=y_std)

print(X.shape, Z.shape)

# Create a JointGrid for visualization
grid = sns.JointGrid()

# Plot the KDE in the joint area
grid.ax_joint.contourf(X, Y, Z, levels=30, cmap='Blues')

# Marginal distributions (theoretical)
grid.ax_marg_x.fill_between(x, norm.pdf(x, loc=x_mean, scale=x_std), color="blue", alpha=0.3)
grid.ax_marg_y.fill_betweenx(y, norm.pdf(y, loc=y_mean, scale=y_std), color="blue", alpha=0.3)

# grid.ax_marg_y.plot(norm.pdf(y, loc=y_mean, scale=y_std), y, color='blue')

# Show the plot
plt.show()
