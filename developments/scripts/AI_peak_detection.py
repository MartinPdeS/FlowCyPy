import numpy as np
from sklearn.model_selection import train_test_split
from FlowCyPy.ai_dev import generate_random_signal_matrix, plot_comparison, build_model

# Define constants
MAX_NUMBER_OF_PEAKS = 2
BUFFER_SIZE = 128
TOTAL_SLICES = 1100  # Total samples (training + testing)
TEST_SIZE = 0.1  # 10% of the data for testing

# Parameters for signal generation
signal_kwargs = {
    "buffer": BUFFER_SIZE,
    "widths": 3,
    "heights": 10,
    "noise": 0.0,
    "positions": (30, BUFFER_SIZE - 30),
    "num_gaussians_range": (MAX_NUMBER_OF_PEAKS, MAX_NUMBER_OF_PEAKS),
}

# Generate the full dataset
full_data = generate_random_signal_matrix(**signal_kwargs, normalize=True, n_slices=TOTAL_SLICES)

# Extract signals, positions, and heights
X = full_data["signals"]
positions = full_data["positions"]
heights = full_data["heights"]

# Split the dataset into training and testing sets
X_train, X_test, y_train_positions, y_test_positions, y_train_heights, y_test_heights = train_test_split(
    X, positions, heights, test_size=TEST_SIZE, random_state=42
)

# Reshape signals for the model (add channel dimension)
X_train = X_train[..., np.newaxis]
X_test = X_test[..., np.newaxis]

# Compile and train the model
model = build_model(input_length=BUFFER_SIZE, max_peaks=MAX_NUMBER_OF_PEAKS)

# Split the dataset
X_train, X_test, y_train_heights, y_test_heights = train_test_split(
    X, heights, test_size=TEST_SIZE, random_state=42
)

# Reshape signals for the model
X_train = X_train[..., np.newaxis]
X_test = X_test[..., np.newaxis]

# Compile the model
model.compile(
    optimizer='adam',
    loss={
        'peak_heights': 'mse',  # Mean squared error for heights
        'peak_positions': 'mae'  # Mean absolute error for positions
    },
    metrics={
        'peak_heights': ['mae'],  # Add metrics for peak heights
        'peak_positions': ['mse']  # Add metrics for peak positions
    }
)

# Train the model
history = model.fit(
    X_train,
    {'peak_heights': y_train_heights, 'peak_positions': y_train_positions},
    epochs=20,
    batch_size=32,
    validation_split=0.2,
)

# Predict positions and heights on the test set
predictions = model.predict(X_test)

# Extract predictions
predicted_positions, predicted_heights = predictions

# Plot comparison for a few test signals
plot_comparison(
    test_signal=X_test.squeeze(-1),  # Remove the channel dimension for plotting
    true_positions=y_test_positions,
    predicted_positions=predicted_positions,
    predicted_heights=predicted_heights,
    slice_idx=[0, 8],
)
