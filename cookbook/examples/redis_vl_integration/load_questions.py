import pandas as pd
from pathlib import Path

# Path to the CSV file (relative to this script)
data_path = Path(__file__).parent.parent.parent.parent / 'data' / 'questions.csv'

# Load a small sample of the CSV to avoid memory issues
try:
    df = pd.read_csv(data_path, nrows=1000)  # Adjust nrows if you want a larger sample
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit(1)

print("\n--- Columns ---")
print(df.columns.tolist())

print(f"\n--- Shape (rows, columns) ---\n{df.shape}")

print("\n--- First 5 Rows ---")
print(df.head()) 