import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create figure and axis
fig, ax = plt.subplots(figsize=(4,4))

# Draw a circle for the emblem
circle = patches.Circle((0.5, 0.5), 0.4, fill=False, linewidth=4, edgecolor='black')
ax.add_patch(circle)

# Draw the stylized "I" for InstruHub
ax.plot([0.35, 0.35], [0.3, 0.7], color='black', linewidth=4)

# Draw the stylized "H" for InstruHub
ax.plot([0.55, 0.55], [0.3, 0.7], color='black', linewidth=4)
ax.plot([0.65, 0.65], [0.3, 0.7], color='black', linewidth=4)
ax.plot([0.55, 0.65], [0.5, 0.5], color='black', linewidth=4)

# Remove axes for a cleaner look
ax.set_xlim(0,1)
ax.set_ylim(0,1)
ax.axis('off')

# Add the text label below the emblem
plt.text(0.5, 0.05, 'InstruHub', fontsize=20, ha='center', fontweight='bold')

# Save the logo as an image
plt.savefig('instruhub_logo.png', dpi=300, bbox_inches='tight')
plt.show()
