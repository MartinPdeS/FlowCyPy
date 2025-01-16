from typing import List, Tuple, Union
import numpy as np

def generate_random_signal_matrix(
    heights: Union[Tuple[float, float], float],
    positions: Union[Tuple[float, float], float],
    widths: Union[Tuple[float, float], float],
    noise: float,
    num_gaussians_range: Tuple[int, int],
    buffer: int = 128,
    n_slices: int = 10
) -> Tuple[np.ndarray, List[List[float]], List[List[float]], List[List[float]]]:
    """
    Generate a signal matrix with a random number of Gaussian peaks per column and added noise.

    Parameters
    ----------
    heights : Union[Tuple[float, float], float]
        Range for the amplitudes of the Gaussian peaks (min, max), or a single fixed value.
    positions : Union[Tuple[float, float], float]
        Range for the centers of the Gaussian peaks (min, max), or a single fixed value.
    widths : Union[Tuple[float, float], float]
        Range for the standard deviations of the Gaussian peaks (min, max), or a single fixed value.
    noise : float
        Standard deviation of the Gaussian noise to be added to the signal.
    num_gaussians_range : Tuple[int, int]
        Range for the number of Gaussian peaks per column (min, max).
    buffer : int, optional
        Number of data points per slice (rows of the matrix). Default is 128.
    n_slices : int, optional
        Number of slices (columns of the matrix). Default is 10.

    Returns
    -------
    Tuple[np.ndarray, List[List[float]], List[List[float]], List[List[float]]]
        A tuple containing:
        - A 2D array of shape (buffer, n_slices) with the generated signal matrix.
        - A list of lists containing the heights used for each column.
        - A list of lists containing the positions used for each column.
        - A list of lists containing the widths used for each column.
    """
    if num_gaussians_range[0] > num_gaussians_range[1]:
        raise ValueError("num_gaussians_range must have a valid (min, max) pair.")

    # Check if heights, positions, and widths are scalars or ranges
    fixed_height = isinstance(heights, (int, float))
    fixed_position = isinstance(positions, (int, float))
    fixed_width = isinstance(widths, (int, float))

    # Initialize the signal matrix
    signal_matrix = np.zeros((buffer, n_slices))
    all_heights = []
    all_positions = []
    all_widths = []

    # Create a linearly spaced x-axis for the buffer
    x = np.linspace(0, buffer - 1, buffer)

    # Generate each slice of the signal
    for col in range(n_slices):
        signal = np.zeros(buffer)

        # Randomly determine the number of Gaussians for this column
        num_gaussians = np.random.randint(num_gaussians_range[0], num_gaussians_range[1] + 1)

        # Store parameters for this column
        col_heights = []
        col_positions = []
        col_widths = []

        # Generate random parameters for each Gaussian
        for _ in range(num_gaussians):
            height = heights if fixed_height else np.random.uniform(*heights)
            position = positions if fixed_position else np.random.uniform(*positions)
            width = widths if fixed_width else np.random.uniform(*widths)

            # Store parameters
            col_heights.append(height)
            col_positions.append(position)
            col_widths.append(width)

            # Add the Gaussian to the signal
            signal += height * np.exp(-((x - position) ** 2) / (2 * width ** 2))

        # Add Gaussian noise
        signal += np.random.normal(0, noise, buffer)

        # Assign to the matrix
        signal_matrix[:, col] = signal

        # Append parameters for this column
        all_heights.append(col_heights)
        all_positions.append(col_positions)
        all_widths.append(col_widths)

    return signal_matrix, all_heights, all_positions, all_widths



# Parameters for signal generation
buffer = 128
n_slices = 1000  # Number of samples (signals) for training

# Generate training data
signal_matrix, heights_used, positions_used, _ = generate_random_signal_matrix(
    heights=(5, 15),
    positions=(0, buffer - 1),
    widths=(3, 10),
    noise=1.0,
    num_gaussians_range=(1, 5),
    buffer=buffer,
    n_slices=n_slices
)

# Prepare labels for training
# Each slice corresponds to a single signal, and its labels are stored in heights_used and positions_used.
labels = [
    {"num_peaks": len(heights), "heights": heights, "positions": positions}
    for heights, positions in zip(heights_used, positions_used)
]


# Normalize signal matrix to range [0, 1]
signal_matrix_normalized = (signal_matrix - signal_matrix.min()) / (signal_matrix.max() - signal_matrix.min())

# Prepare labels for regression
num_peaks = np.array([label["num_peaks"] for label in labels])
peak_positions = np.zeros((n_slices, 5))  # Assume max 5 peaks
peak_heights = np.zeros((n_slices, 5))

for i, label in enumerate(labels):
    n = label["num_peaks"]
    peak_positions[i, :n] = label["positions"]
    peak_heights[i, :n] = label["heights"]

import tensorflow as tf
from tensorflow.keras import layers, models

# Define the CNN model
def build_peak_detection_model(input_length=128, max_peaks=5):
    model = models.Sequential([
        layers.Input(shape=(input_length, 1)),  # Input shape: (buffer, 1)
        # layers.Conv1D(32, kernel_size=3, activation='relu', padding='same'),
        # layers.MaxPooling1D(pool_size=2),
        # layers.Conv1D(64, kernel_size=3, activation='relu', padding='same'),
        # layers.MaxPooling1D(pool_size=2),
        # layers.Flatten(),
        # layers.Dense(128, activation='relu'),
        # layers.Dense(max_peaks * 2, activation='linear')  # Outputs: positions and heights
    ])
    return model

# Build the model
input_length = buffer
max_peaks = 5
model = build_peak_detection_model(input_length=input_length, max_peaks=max_peaks)

# Compile the model
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Reshape input for the model
X_train = signal_matrix_normalized.T[..., np.newaxis]  # Add channel dimension

# Combine positions and heights into a single label array
y_train = np.hstack([peak_positions, peak_heights])

# Train the model
print(X_train.shape)
print(y_train.shape)
history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2)

# Generate test data
test_signals, test_heights, test_positions, _ = generate_random_signal_matrix(
    heights=(5, 15),
    positions=(0, buffer - 1),
    widths=(3, 10),
    noise=1.0,
    num_gaussians_range=(1, 5),
    buffer=buffer,
    n_slices=100
)

# Normalize test signals
test_signals_normalized = (test_signals - test_signals.min()) / (test_signals.max() - test_signals.min())

# Reshape for prediction
X_test = test_signals_normalized[..., np.newaxis]

# Predict
predictions = model.predict(X_test)

# Extract predicted positions and heights
predicted_positions = predictions[:, :max_peaks]
predicted_heights = predictions[:, max_peaks:]

# Visualize results for a single signal
import matplotlib.pyplot as plt
plt.plot(test_signals[0], label="Signal")
plt.scatter(predicted_positions[0], predicted_heights[0], color='red', label="Predicted Peaks")
plt.legend()
plt.show()
