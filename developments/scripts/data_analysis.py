import matplotlib.pyplot as plt

# Create a figure and a primary axis
fig, ax1 = plt.subplots()

# Plot data on the primary axis
x = [1, 2, 3, 4, 5]
y1 = [10, 20, 30, 40, 50]
ax1.plot(x, y1, 'b-', label="Primary Axis")
ax1.set_xlabel("X-axis")
ax1.set_ylabel("Primary Axis (y1)", color='b')

# Create a secondary axis
ax2 = ax1.twinx()

# Define the scaling factor
scale_factor = 2
ax2.set_ylabel(f"Secondary Axis (y1 * {scale_factor})", color='r')

# Function to update the secondary axis based on primary axis limits
def update_secondary_axis(ax1, ax2, scale_factor):
    """Synchronize ax2 with ax1."""
    y1_min, y1_max = ax1.get_ylim()  # Get limits from primary axis
    ax2.set_ylim(y1_min * scale_factor, y1_max * scale_factor)  # Scale limits
    ax2.figure.canvas.draw_idle()  # Redraw the figure

# Attach the update function to the primary axis limits
ax1.callbacks.connect('ylim_changed', lambda ax: update_secondary_axis(ax1, ax2, scale_factor))

# Initial sync of secondary axis
update_secondary_axis(ax1, ax2, scale_factor)

# Show the plot
plt.show()
