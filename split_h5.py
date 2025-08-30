import h5py
import numpy as np
import os
import math

# --- 1. Configuration ---
# VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
# --- ONLY EDIT THESE TWO LINES ---
directory = "c:/Users/Sergii/Dell_D/GNSS/Raw/2023/"
file = "los_20231019.001.h5"
SOURCE_FILE = directory + file  # Change this to your file's name
ROWS_PER_FILE = 1_000_000  # The desired number of rows in each smaller file
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

OUTPUT_DIR = 'split_files_output'

# --- 2. First Pass: Discover the Main Dimension to Split On ---
max_rows = 0
with h5py.File(SOURCE_FILE, 'r') as f_in:
    def find_max_rows(name, obj):
        global max_rows
        if isinstance(obj, h5py.Dataset) and obj.ndim > 0:
            if obj.shape[0] > max_rows:
                max_rows = obj.shape[0]


    # visititems traverses the entire file to find the largest first dimension
    f_in.visititems(find_max_rows)

if max_rows == 0:
    print("Could not find any datasets with a splittable dimension. Exiting.")
    exit()

# --- 3. Main Splitting Logic ---
print("Starting the splitting process...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

with h5py.File(SOURCE_FILE, 'r') as f_in:
    num_split_files = math.ceil(max_rows / ROWS_PER_FILE)

    print(f"Detected largest dimension as {max_rows} rows.")
    print(f"Splitting into {num_split_files} file(s) with ~{ROWS_PER_FILE} rows each.\n")

    # Iterate to create each new split file
    for i in range(num_split_files):
        start_row = i * ROWS_PER_FILE
        end_row = min((i + 1) * ROWS_PER_FILE, max_rows)

        output_filename = os.path.join(OUTPUT_DIR, f'{os.path.basename(SOURCE_FILE)}_split_{i}.h5')
        print(f"Creating '{output_filename}' (rows {start_row} to {end_row - 1})...")

        with h5py.File(output_filename, 'w') as f_out:
            # This is the core logic: copy the structure and sliced data
            def copy_object(name, obj):
                if isinstance(obj, h5py.Group):
                    f_out.create_group(name)  # Create groups to preserve structure
                elif isinstance(obj, h5py.Dataset):
                    # Check if this dataset has the 'max_rows' dimension and should be sliced
                    if obj.ndim > 0 and obj.shape[0] == max_rows:
                        # This is a large dataset we need to slice
                        original_shape = obj.shape
                        new_shape = (end_row - start_row,) + original_shape[1:]
                        data_slice = obj[start_row:end_row]
                    else:
                        # This is a smaller "metadata" dataset, so copy it entirely
                        new_shape = obj.shape
                        data_slice = obj[:]

                    # Create the new dataset in the output file and write the data
                    target_dset = f_out.create_dataset(
                        name,
                        shape=new_shape,
                        dtype=obj.dtype,
                        compression=obj.compression
                    )
                    target_dset[:] = data_slice


            # visititems() walks through every object in the source file
            f_in.visititems(copy_object)

print("\nSplitting process complete.")