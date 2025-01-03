import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def plot_csv(file_path: str, n_points: int) -> None:
    """
    Load a CSV file and plot its data.
    
    Args:
        file_path (str): Path to the CSV file.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Load the CSV file
        data = pd.read_csv(Path(base_dir) / file_path, header=None)[:n_points]

        print(data)

        # Check if the file is empty
        if data.empty:
            print(f"The file '{file_path}' is empty.")
            return

        # Plot each column
        for column in data.columns:
            plt.plot(data.index, data[column], label=f"Column {column}")

        # Configure the plot
        plt.xlabel("Index")
        plt.ylabel("Value")
        plt.title(f"Plot of {file_path}")
        plt.legend()
        plt.grid(True)

        # Show the plot
        plt.show()

    except Exception as e:
        print(f"An error occurred while processing the file: {e}")

plot_csv(file_path="../data/dataset_0/0_A.csv", n_points=500)