import pandas as pd

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

    with open(file_path, 'r') as file:
        for line in file:
            stripped_line = line.strip()
            
            # Detect new metadata block
            if 'Activity Summary' in stripped_line:
                if current_metadata:
                    all_metadata.append(current_metadata)
                    if activity_data_lines:
                        df_activity = parse_data_to_dataframe(activity_header_lines, activity_data_lines)
                        activity_dataframes.append(df_activity)
                        activity_data_lines = []
                        activity_header_lines = []
                    if jump_data_lines:
                        df_jump = parse_data_to_dataframe(jump_header_lines, jump_data_lines)
                        jump_dataframes.append(df_jump)
                        jump_data_lines = []
                        jump_header_lines = []
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
        all_metadata.append(current_metadata)
    if activity_data_lines:
        df_activity = parse_data_to_dataframe(activity_header_lines, activity_data_lines)
        activity_dataframes.append(df_activity)
    if jump_data_lines:
        df_jump = parse_data_to_dataframe(jump_header_lines, jump_data_lines)
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

# Path to your file
file_path = 'sample.txt'

# Extract metadata and data
metadata_blocks, activity_dataframes, jump_dataframes = extract_metadata_and_data(file_path)

print_summary(metadata_blocks, activity_dataframes, jump_dataframes)