import sys
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import argparse
import os

def open_file_picker():
    # Initialize a hidden Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open file picker dialog
    file_path = filedialog.askopenfilename(title="Select a File",
                                           filetypes=[("Summary Files", "*.Summary"), 
                                                      ("TXT Files", "*.txt")])
    
    if file_path:
        print(f"Selected file: {file_path}")
    else:
        print("No file selected.")

    return file_path  # Return the selected file path

def extract_metadata_and_data(file_path):
    all_metadata = []
    activity_dataframes = []
    jump_dataframes = []
    
    current_metadata = {}
    activity_data_lines = []
    jump_data_lines = []
    
    inside_metadata = False
    inside_activity_data = False
    inside_jump_data = False
    activity_header_lines = []
    jump_header_lines = []

    record_id = 0  # Unique identifier for each record

    with open(file_path, 'r') as file:
        for line in file:
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                continue
            
            # Detect new metadata block
            if 'Activity Summary' in stripped_line:
                if current_metadata:
                    # Assign unique ID to metadata
                    current_metadata["Record ID"] = record_id
                    all_metadata.append(current_metadata)

                    # Process activity data
                    if activity_data_lines:
                        df_activity = parse_data_to_dataframe(activity_header_lines, activity_data_lines)
                        df_activity["Record ID"] = record_id  # Assign same unique ID
                        activity_dataframes.append(df_activity)
                        activity_data_lines = []
                        activity_header_lines = []

                    # Process jump data
                    if jump_data_lines:
                        df_jump = parse_data_to_dataframe(jump_header_lines, jump_data_lines)
                        df_jump["Record ID"] = record_id  # Assign same unique ID
                        jump_dataframes.append(df_jump)
                        jump_data_lines = []
                        jump_header_lines = []

                    # Increment unique record ID for the next dataset block
                    record_id += 1
                    current_metadata = {}

                inside_metadata = True
                inside_activity_data = False
                inside_jump_data = False

            # Detect start of activity data block
            if 'Dist.' in stripped_line:
                inside_metadata = False
                inside_activity_data = True
                inside_jump_data = False
                activity_header_lines.append(stripped_line)
                continue

            # Detect second activity header row
            if inside_activity_data and len(activity_header_lines) == 1:
                activity_header_lines.append(stripped_line)
                continue
            
            # Detect start of jump data block
            if 'Jump' in stripped_line:
                inside_metadata = False
                inside_activity_data = False
                inside_jump_data = True
                jump_header_lines.append(stripped_line)
                continue

            # Detect second jump header row
            if inside_jump_data and len(jump_header_lines) == 1:
                jump_header_lines.append(stripped_line)
                continue

            # Parse metadata
            if inside_metadata and ':' in stripped_line:
                key, value = stripped_line.split(':', 1)
                current_metadata[key.strip()] = value.strip()

            # Collect activity data
            if inside_activity_data and len(activity_header_lines) == 2:
                if '=====' not in stripped_line:
                    activity_data_lines.append(stripped_line)

            # Collect jump data
            if inside_jump_data and len(jump_header_lines) == 2:
                if '=====' not in stripped_line:
                    jump_data_lines.append(stripped_line)
    
    # Save the last metadata and data blocks
    if current_metadata:
        current_metadata["Record ID"] = record_id
        all_metadata.append(current_metadata)
    if activity_data_lines:
        df_activity = parse_data_to_dataframe(activity_header_lines, activity_data_lines)
        df_activity["Record ID"] = record_id  # Assign ID to activity data
        activity_dataframes.append(df_activity)
    if jump_data_lines:
        df_jump = parse_data_to_dataframe(jump_header_lines, jump_data_lines)
        df_jump["Record ID"] = record_id  # Assign ID to jump data
        jump_dataframes.append(df_jump)
    
    return all_metadata, activity_dataframes, jump_dataframes

def parse_data_to_dataframe(header_lines, data_lines):
    header_1 = header_lines[0].split()
    header_2 = header_lines[1].split()

    combined_headers = []
    for i in range(max(len(header_1), len(header_2))):
        col1 = header_1[i] if i < len(header_1) else ''
        col2 = header_2[i] if i < len(header_2) else ''
        combined_header = f"{col1} {col2}".strip()
        combined_headers.append(combined_header)
    
    data_rows = [line.split() for line in data_lines]
    df = pd.DataFrame(data_rows, columns=combined_headers)
    return df
    
def print_summary(metadata, activity_df, jump_df):
    # Displaying results
    for i, (metadata, activity_df, jump_df) in enumerate(zip(metadata_blocks, activity_dataframes, jump_dataframes), 1):
        print(f"Metadata Block {i}:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print("\nActivity Data Block:")
        print(activity_df.head())  # Display first few rows of activity data
        
        print("\nJump Data Block:")
        print(jump_df.head())  # Display first few rows of jump data
        
        print("\n" + "="*40 + "\n")

def export_data(data, id):
    output_dir = "output"
    output_filename = f"{output_dir}/{id}.csv"

    # Create the directory if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    # Get absolute file path
    absolute_path = os.path.abspath(output_filename)

    # Save to CSV including metadata
    data.to_csv(absolute_path, index=False)

    print(f"CSV file saved successfully with name {absolute_path}!")


## Target output is a table for is x, y 
# 1 file = 1 mouse
# x axis = n days bin
# y axis = date
def delta_time_distance(dataframes, interval, metadata):
    grouped_dataframes = []
    summary_id = ""  # unique id for this summary

    for i, df in enumerate(dataframes):
        if isinstance(df, pd.DataFrame):
            if not summary_id:
                # Extract summary id
                subject_id = metadata[i].get("Subject ID", f"Subject_{i}")
                group_id = metadata[i].get("Group ID", f"Group_{i}")
                experiment_id = metadata[i].get("Experiment ID", f"Experiment_{i}")
                summary_id = f"{subject_id}_{group_id}_{experiment_id}"

            # Extract metadata date fields
            date = metadata[i].get("Start Date", f"Dataset_{i}")  # Use date as column name

            # Convert distance column to numeric
            df["Dist. Trav."] = pd.to_numeric(df["Dist. Trav."], errors='coerce')

            # Calculate movement difference (delta)
            df["Dist. Trav. Delta"] = df["Dist. Trav."].diff().round(4).fillna(df["Dist. Trav."])

            # Create groups based on interval
            df["Group"] = df.index // interval  

            # Sum "Dist. Trav. Delta" in groups of interval
            df_grouped = df.groupby("Group")["Dist. Trav. Delta"].sum().round(4).reset_index()

            # Rename "Dist. Trav. Delta" to the date
            df_grouped = df_grouped.rename(columns={"Dist. Trav. Delta": date})

            # Append to list
            grouped_dataframes.append(df_grouped)
        
        else:
            print("Item is not a DataFrame:", type(df))

    # Merge DataFrames using "Group" as the index
    final_df = grouped_dataframes[0].set_index("Group")  # Start with first DataFrame
    for df in grouped_dataframes[1:]:
        final_df = final_df.join(df.set_index("Group"), how="outer")  # Join on "Group"

    # Reset index after merging
    final_df = final_df.reset_index()

    export_data(final_df, summary_id)

    return final_df, summary_id  # Return the final DataFrame

def plot_delta_time_distance(dataframe, interval, summary_id):
    # Select all columns except "Group" for plotting (since they are dates)
    date_columns = [col for col in dataframe.columns if col != "Group"]

    # Ensure there are valid columns to plot
    if date_columns:
        dataframe.plot(x="Group", y=date_columns, marker="o")

        # Customize plot
        plt.xlabel(f"Group (in {interval}-minute Time Intervals)")
        plt.ylabel("Distance Traveled")
        plt.title(f"Distance Traveled Over Time for {summary_id}")
        plt.legend(title="Date")
        plt.grid()

        # Show plot
        plt.show()
    else:
        print("No valid columns found for plotting!")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process data and optionally generate plots.")
    parser.add_argument("--plot", action="store_true", help="Enable plotting")

    # Parse arguments
    args = parser.parse_args()

    # Call the function to open the file picker
    file_path = open_file_picker()

    # Exit if no file provided
    if not file_path:
        print("Error: No file path provided. Please select a .Summary or .txt file to process.")
        print("Usage: python script.py [--plot]")
        sys.exit(1)  # Exit with error status 1

    # parse input text file
    metadata_blocks, activity_dataframes, jump_dataframes = extract_metadata_and_data(file_path)

    # Constants
    INTERVAL = 5
    
    # Save a new output csv file to specified directory
    grouped_df, SUMMARY_ID = delta_time_distance(activity_dataframes, INTERVAL, metadata_blocks)
    
    # Only generate plots if --plot is provided
    if args.plot:
        plt = plot_delta_time_distance(grouped_df, INTERVAL, SUMMARY_ID)


if __name__ == "__main__":
    main()