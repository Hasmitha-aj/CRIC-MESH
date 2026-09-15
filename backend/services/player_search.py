import pandas as pd
import re

PEOPLE_FILE = "backend/data/people.csv"
NAMES_FILE = "backend/data/names.csv"
ALIASES_FILE = "backend/data/player_aliases.csv"


def normalize(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


people = pd.read_csv(PEOPLE_FILE)
names = pd.read_csv(NAMES_FILE)
aliases = pd.read_csv(ALIASES_FILE)

people["name"] = people["name"].fillna("")
people["unique_name"] = people["unique_name"].fillna("")
names["name"] = names["name"].fillna("")


# --------------------------------------------------
# Build Cricsheet aliases
# --------------------------------------------------

alias_map = {}

for identifier, group in names.groupby("identifier"):

    alias_map[identifier] = []

    for name in group["name"].tolist():

        cleaned = normalize(name)

        if cleaned and cleaned not in alias_map[identifier]:
            alias_map[identifier].append(cleaned)


# Add registered and unique names
for _, player in people.iterrows():

    identifier = player["identifier"]

    if identifier not in alias_map:
        alias_map[identifier] = []

    for name in [
        player["name"],
        player["unique_name"]
    ]:

        cleaned = normalize(name)

        if cleaned and cleaned not in alias_map[identifier]:
            alias_map[identifier].append(cleaned)


# --------------------------------------------------
# Add our full-name aliases
# --------------------------------------------------

full_name_map = {}

for _, row in aliases.iterrows():

    identifier = str(row["identifier"]).strip()

    full_name = normalize(row["full_name"])

    if full_name:
        full_name_map[identifier] = full_name

    extra_aliases = str(row["aliases"])

    for alias in extra_aliases.split(";"):

        cleaned = normalize(alias)

        if cleaned:

            if identifier not in alias_map:
                alias_map[identifier] = []

            if cleaned not in alias_map[identifier]:
                alias_map[identifier].append(cleaned)


# --------------------------------------------------
# Search scoring
# --------------------------------------------------

def get_match_score(query, candidate):

    if candidate == query:
        return 10000

    # Exact full-name alias
    if candidate == query:
        return 10000

    # Query is a complete word
    if query in candidate.split():

        if len(query) == 1:
            return 5000

        return 8000 + min(len(candidate), 100)

    # Candidate starts with query
    if candidate.startswith(query):

        if len(query) > 1:
            return 7500 + min(len(candidate), 100)

        return 5000

    # A word starts with query
    for word in candidate.split():

        if word.startswith(query):

            if len(word) > 1:
                return 7000 + min(len(word), 100)

    # Query appears anywhere
    if query in candidate:
        return 3000

    return 0


def search_players(query: str, limit: int = 10):

    query = normalize(query)

    if not query:
        return []

    results = []

    for _, player in people.iterrows():

        identifier = str(player["identifier"])

        registered_name = normalize(player["name"])
        unique_name = normalize(player["unique_name"])

        player_aliases = alias_map.get(identifier, [])

        searchable_names = [
            registered_name,
            unique_name
        ] + player_aliases

        # Add our full name
        if identifier in full_name_map:
            searchable_names.append(
                full_name_map[identifier]
            )

        searchable_names = list(
            set(
                name
                for name in searchable_names
                if name
            )
        )

        best_score = 0
        best_match = ""

        for candidate in searchable_names:

            score = get_match_score(
                query,
                candidate
            )

            if score > best_score:

                best_score = score
                best_match = candidate

        if best_score > 0:

            display_name = (
                full_name_map.get(identifier)
                or unique_name
                or registered_name
                or player["name"]
            )

            results.append({
                "id": identifier,
                "name": display_name.title(),
                "registered_name": player["name"],
                "match_score": best_score,
                "matched_as": best_match
            })

    results.sort(
        key=lambda x: (
            -x["match_score"],
            x["name"]
        )
    )

    unique_results = []
    seen = set()

    for result in results:

        if result["id"] not in seen:

            seen.add(result["id"])
            unique_results.append(result)

    return unique_results[:limit]