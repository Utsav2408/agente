import json
import csv

# Input and output file paths
json_file = "model_test.json"
csv_file = "model_test.csv"

# Read the JSON file
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ensure it's a list of dictionaries
if isinstance(data, dict):
    # If the JSON is a dict, maybe wrap it in a list
    data = [data]

if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
    raise ValueError("JSON must be an array of objects to convert to CSV.")

# Get CSV column names from all keys across records
fieldnames = set()
for row in data:
    fieldnames.update(row.keys())
fieldnames = list(fieldnames)

# Write CSV
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

print(f"CSV file created: {csv_file}")
