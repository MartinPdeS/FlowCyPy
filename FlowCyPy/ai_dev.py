from typing import List, Tuple, Union
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras import layers, models

def generate_random_signal_matrix(
    heights: Union[Tuple[float, float], float],
    positions: Union[Tuple[float, float], float],
    widths: Union[Tuple[float, float], float],
    noise: float,
    num_gaussians_range: Tuple[int, int],
    buffer: int = 128,
    n_slices: int = 10,
    normalize: bool = True
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
    min_number_of_gaussian, max_number_of_gaussian = num_gaussians_range

    if min_number_of_gaussian > max_number_of_gaussian:
        raise ValueError("num_gaussians_range must have a valid (min, max) pair.")

    # Check if heights, positions, and widths are scalars or ranges
    fixed_height = isinstance(heights, (int, float))
    fixed_position = isinstance(positions, (int, float))
    fixed_width = isinstance(widths, (int, float))

    # Initialize the signal matrix
    signal_matrix = np.zeros((buffer, n_slices))

    height_array = np.zeros((n_slices, max_number_of_gaussian))
    width_array = np.zeros((n_slices, max_number_of_gaussian))
    position_array = np.zeros((n_slices, max_number_of_gaussian))

    # Create a linearly spaced x-axis for the buffer
    x = np.linspace(0, buffer - 1, buffer)

    # Generate each slice of the signal
    for col in range(n_slices):
        signal = np.zeros(buffer)

        # Randomly determine the number of Gaussians for this column
        num_gaussians = np.random.randint(min_number_of_gaussian, max_number_of_gaussian + 1)

        # Generate random parameters for each Gaussian
        for idx in range(num_gaussians):
            height = heights if fixed_height else np.random.uniform(*heights)
            position = positions if fixed_position else np.random.uniform(*positions)
            width = widths if fixed_width else np.random.uniform(*widths)

            height_array[col, idx] = height
            width_array[col, idx] = width
            position_array[col, idx] = position

            # Add the Gaussian to the signal
            signal += height * np.exp(-((x - position) ** 2) / (2 * width ** 2))

        # Add Gaussian noise
        signal += np.random.normal(0, noise, buffer)

        # Assign to the matrix
        signal_matrix[:, col] = signal

    if normalize:
        signal_matrix = (signal_matrix - signal_matrix.min()) / (signal_matrix.max() - signal_matrix.min())

    return dict(
        signals=signal_matrix.T,
        positions=position_array,
        heights=height_array,
        widths=width_array
    )


import matplotlib.pyplot as plt

def plot_comparison(
    test_signal,
    true_positions,
    predicted_positions,
    predicted_heights,
    slice_idx: Union[int, List[int]]
):
    """
    Plot a comparison of test signals with true and predicted peak positions.

    Parameters
    ----------
    test_signal : np.ndarray
        Array of test signals (shape: n_slices x signal_length).
    true_positions : List[List[float]]
        List of true peak positions for each slice.
    predicted_positions : List[List[float]]
        List of predicted peak positions for each slice.
    predicted_heights : List[List[float]]
        List of predicted peak heights for each slice.
    slice_idx : int or List[int]
        Index (or indices) of slices to plot.
    """
    # Check if slice_idx is a list
    if isinstance(slice_idx, list):
        n_slices = len(slice_idx)
        fig, axes = plt.subplots(n_slices, 1, figsize=(8, 4 * n_slices))

        if n_slices == 1:  # Handle case where there's only one subplot
            axes = [axes]

        for ax, idx in zip(axes, slice_idx):
            ax.plot(test_signal[idx], label="Signal")
            ax.vlines(
                true_positions[idx],
                ymin=0,
                ymax=1,
                transform=ax.get_xaxis_transform(),
                color='red',
                label="True Peaks"
            )
            ax.scatter(
                predicted_positions[idx],
                predicted_heights[idx],
                color='blue',
                label="Predicted Peaks"
            )
            ax.legend()
            ax.set_title(f"Slice {idx}")
        plt.tight_layout()
    else:
        # Single slice case
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        ax.plot(test_signal[slice_idx], label="Signal")
        ax.vlines(
            true_positions[slice_idx],
            ymin=0,
            ymax=1,
            transform=ax.get_xaxis_transform(),
            color='red',
            label="True Peaks"
        )
        ax.scatter(
            predicted_positions[slice_idx],
            predicted_heights[slice_idx],
            color='blue',
            label="Predicted Peaks"
        )
        ax.legend()
        ax.set_title(f"Slice {slice_idx}")
    plt.show()

def build_model(input_length, max_peaks):
    """
    Build an improved model for peak detection with constrained outputs and better spatial resolution.

    Parameters
    ----------
    input_length : int
        Length of the input signal (e.g., 128).
    max_peaks : int
        Maximum number of peaks to detect.

    Returns
    -------
    tensorflow.keras.Model
        The constructed Keras model.
    """
    input_layer = layers.Input(shape=(input_length, 1))

    # Feature extraction with dilated convolutions to increase receptive field
    x = layers.Conv1D(32, kernel_size=3, activation="relu", padding="same")(input_layer)
    x = layers.Conv1D(64, kernel_size=3, activation="relu", padding="same", dilation_rate=2)(x)
    x = layers.Conv1D(64, kernel_size=3, activation="relu", padding="same", dilation_rate=4)(x)

    # Global pooling to reduce the time dimension
    x = layers.GlobalMaxPooling1D()(x)

    # Fully connected layer to predict heights for max_peaks
    peak_heights = layers.Dense(max_peaks, activation="relu", name="peak_heights")(x)

    # Fully connected layer to predict positions for max_peaks
    peak_positions = layers.Dense(max_peaks, activation="sigmoid", name="peak_positions")(x)

    # Define the model with two outputs
    model = models.Model(inputs=input_layer, outputs=[peak_heights, peak_positions])

    return model


