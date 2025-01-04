import os
import numpy as np
from scipy.io import loadmat
import pandas as pd

def clean_csv_folder(csv_folder_path):
    """Remove files not matching the *_A.csv format in the CSV folder."""
    for file_name in os.listdir(csv_folder_path):
        if not file_name.endswith('_A.csv'):
            file_path = os.path.join(csv_folder_path, file_name)
            os.remove(file_path)
            print(f"Removed: {file_path}")

def convert_mat_to_csv(mat_folder_path, csv_folder_path):
    # Ensure the folders exist
    if not os.path.exists(mat_folder_path):
        print(f"Folder '{mat_folder_path}' does not exist.")
        return

    os.makedirs(csv_folder_path, exist_ok=True)

    # Iterate through all .mat files in the folder
    for file_name in os.listdir(mat_folder_path):
        if file_name.endswith('.mat'):
            mat_file_path = os.path.join(mat_folder_path, file_name)
            mat_data = loadmat(mat_file_path)

            # Exclude MATLAB metadata keys
            keys_to_save = [key for key in mat_data.keys() if not key.startswith('__')]

            for key in keys_to_save:
                variable_data = mat_data[key]

                # Ensure data is 2D (necessary for CSV format)
                if variable_data.ndim == 1:
                    variable_data = np.expand_dims(variable_data, axis=1)

                # Save as CSV
                csv_file_name = f"{os.path.splitext(file_name)[0]}_{key}.csv"
                csv_file_path = os.path.join(csv_folder_path, csv_file_name)

                # Convert to DataFrame for CSV writing
                df = pd.DataFrame(variable_data)
                df.to_csv(csv_file_path, index=False, header=False)
                print(f"Saved: {csv_file_path}")

    print("MAT to CSV conversion complete.")


def conversion_workflow(directory):
    relative_directory = directory + "/mat_files"
    csv_directory = directory + "/CSV"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mat_files_dir = os.path.join(base_dir, relative_directory)
    csv_folder_path = os.path.join(base_dir, csv_directory)  # Output folder for CSV files

    # Ensure the 'mat_files' folder exists or notify the user
    if not os.path.exists(mat_files_dir):
        print(f"Directory '{mat_files_dir}' does not exist. Please create it and add .mat files.")
    else:
        # Convert MAT to CSV
        convert_mat_to_csv(mat_files_dir, csv_folder_path)

        # Clean up CSV folder
        clean_csv_folder(csv_folder_path)
