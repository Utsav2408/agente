import json
from pathlib import Path

# Folder containing JSON files
folder_path = Path("data/jsons")

# Where to save the merged file
output_file = Path("merged.json")

merged_data = []

# Merge all JSONs
for file_path in sorted(folder_path.glob("*.json")):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged_data.extend(data[:50])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

# Save merged result
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, indent=4, ensure_ascii=False)

print(f"Total merged elements: {len(merged_data)}")
print(f"Saved first {len(merged_data)} elements to {output_file}")
