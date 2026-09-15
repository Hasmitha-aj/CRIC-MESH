import json
import glob

files = glob.glob("backend/data/matches/test/*.json")

print("Number of Test match files:", len(files))

if not files:
    print("No JSON files found!")
    exit()

file = files[0]

print("\nOpening:", file)

with open(file, "r", encoding="utf-8") as f:
    match = json.load(f)

info = match["info"]

print("\n--- INFO KEYS ---")
print(info.keys())

print("\n--- DATE ---")
print(info.get("dates"))

print("\n--- TEAMS ---")
print(info.get("teams"))

print("\n--- GENDER ---")
print(info.get("gender"))

print("\n--- PLAYERS ---")
print(info.get("players"))

print("\n--- REGISTRY ---")
print(info.get("registry"))

print("\n--- INNINGS ---")
print("Number of innings:", len(match.get("innings", [])))

if match.get("innings"):
    first_innings = match["innings"][0]

    print("\nFirst innings keys:")
    print(first_innings.keys())

    print("\nFirst innings:")
    print(first_innings)