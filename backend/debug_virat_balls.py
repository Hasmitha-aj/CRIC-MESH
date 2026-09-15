import json
import glob

TARGET_ID = "ba607b88"

MATCH_FILES = glob.glob(
    "backend/data/matches/test/*.json"
)


def normalize_name(name):
    return (
        str(name)
        .lower()
        .replace(".", "")
        .replace(" ", "")
    )


def get_player_id(name, registry):

    if name in registry:
        return registry[name]

    normalized = normalize_name(name)

    for registry_name, player_id in registry.items():

        if normalize_name(registry_name) == normalized:
            return player_id

    return None


total_balls = 0
wide_balls = 0
no_ball_balls = 0
legal_balls = 0

examples = []


for file in MATCH_FILES:

    with open(file, "r", encoding="utf-8") as f:
        match = json.load(f)

    info = match.get("info", {})

    registry = (
        info
        .get("registry", {})
        .get("people", {})
    )

    player_found = False

    for players in info.get(
        "players", {}
    ).values():

        for player in players:

            if get_player_id(
                player,
                registry
            ) == TARGET_ID:

                player_found = True
                break

        if player_found:
            break

    if not player_found:
        continue

    for innings_number, innings in enumerate(
        match.get("innings", []),
        start=1
    ):

        innings_balls = 0

        for over in innings.get(
            "overs", []
        ):

            for delivery in over.get(
                "deliveries", []
            ):

                batter = delivery.get(
                    "batter"
                )

                batter_id = get_player_id(
                    batter,
                    registry
                )

                if batter_id != TARGET_ID:
                    continue

                total_balls += 1

                extras = delivery.get(
                    "extras",
                    {}
                )

                if "wides" in extras:

                    wide_balls += 1

                    if len(examples) < 20:
                        examples.append({
                            "type": "wide",
                            "file": file,
                            "delivery":
                                delivery.get(
                                    "actual_delivery"
                                ),
                            "batter": batter,
                            "extras": extras
                        })

                elif "noballs" in extras:

                    no_ball_balls += 1

                    if len(examples) < 20:
                        examples.append({
                            "type": "no-ball",
                            "file": file,
                            "delivery":
                                delivery.get(
                                    "actual_delivery"
                                ),
                            "batter": batter,
                            "extras": extras
                        })

                else:

                    legal_balls += 1
                    innings_balls += 1


print()
print("==============================")
print(" VIRAT BALLS-FACED DEBUG")
print("==============================")

print()
print("Total deliveries faced:", total_balls)
print("Wide deliveries:", wide_balls)
print("No-ball deliveries:", no_ball_balls)
print("Legal balls:", legal_balls)

print()
print("Expected current calculator:")
print("16538 balls")

print()
print("Difference from 16608:")
print(16608 - legal_balls)

print()
print("--- EXAMPLES OF EXCLUDED DELIVERIES ---")

for example in examples:

    print(example)

print()
print("==============================")