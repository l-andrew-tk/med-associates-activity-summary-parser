def extract_all_metadata(file_path):
    all_metadata = []
    current_metadata = {}
    inside_metadata = False

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            
            # Detect the start of a new metadata block
            if 'Activity Summary' in line:
                if current_metadata:
                    all_metadata.append(current_metadata)
                    current_metadata = {}
                inside_metadata = True
            
            # Detect the end of metadata block
            if 'Dist.' in line:
                if current_metadata:
                    all_metadata.append(current_metadata)
                    current_metadata = {}
                inside_metadata = False

            # Extract key-value pairs if inside metadata block
            if inside_metadata and ':' in line:
                key, value = line.split(':', 1)
                current_metadata[key.strip()] = value.strip()

    # Append the last metadata block if any
    if current_metadata:
        all_metadata.append(current_metadata)

    return all_metadata

def print_metadata(metadata_blocks):
    # Display each metadata block
    for i, metadata in enumerate(metadata_blocks, 1):
        print(f"Metadata Block {i}:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print("\n" + "="*40 + "\n")

# Path to the sample file
file_path = 'sample.txt'

# Extract all metadata blocks
metadata_blocks = extract_all_metadata(file_path)

print(metadata_blocks)