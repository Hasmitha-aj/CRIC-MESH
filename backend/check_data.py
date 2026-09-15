import pandas as pd

people = pd.read_csv("backend/data/people.csv")
names = pd.read_csv("backend/data/names.csv")

print("\n========== PEOPLE.CSV ==========")
print("Columns:")
print(people.columns.tolist())

print("\nFirst 5 rows:")
print(people.head().to_string())

print("\n========== NAMES.CSV ==========")
print("Columns:")
print(names.columns.tolist())

print("\nFirst 10 rows:")
print(names.head(10).to_string())