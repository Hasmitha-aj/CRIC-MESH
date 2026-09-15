import pandas as pd

people = pd.read_csv("backend/data/people.csv")
names = pd.read_csv("backend/data/names.csv")

players_to_check = [
    "Virat Kohli",
    "Rohit Sharma",
    "MS Dhoni",
    "Sachin Tendulkar",
    "Jasprit Bumrah"
]

for search_name in players_to_check:

    print("\n" + "=" * 50)
    print(f"SEARCHING: {search_name}")

    matches = names[
        names["name"].str.contains(
            search_name.split()[-1],
            case=False,
            na=False
        )
    ]

    identifiers = matches["identifier"].unique()

    players = people[
        people["identifier"].isin(identifiers)
    ]

    print(players[["identifier", "name", "unique_name"]].to_string(index=False))

    print("\nName variations:")

    for identifier in identifiers:
        aliases = names[
            names["identifier"] == identifier
        ]

        print(
            f"{identifier}: "
            + ", ".join(aliases["name"].tolist())
        )