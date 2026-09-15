import json
import glob
import re
from collections import defaultdict

TARGET_ID = "ba607b88"  # Virat Kohli

MATCH_FILES = glob.glob("backend/data/matches/test/*.json")


def normalize_name(name):
    """Make names easier to match."""
    name = str(name).lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def get_player_id(name, registry):
    """
    Convert a player name from the match data
    into the Cricsheet player ID.
    """

    if name in registry:
        return registry[name]

    normalized = normalize_name(name)

    for registry_name, player_id in registry.items():
        if normalize_name(registry_name) == normalized:
            return player_id

    return None


# -----------------------------
# STATISTICS
# -----------------------------

matches = 0

batting_innings = 0
runs = 0
balls_faced = 0
fours = 0
sixes = 0

dismissals = 0
fifties = 0
hundreds = 0
highest_score = 0

bowling_innings = 0
bowling_balls = 0
runs_conceded = 0
wickets = 0

four_wickets = 0
five_wickets = 0

best_bowling_wickets = 0
best_bowling_runs = 999999

catches = 0
run_outs = 0
stumpings = 0


# -----------------------------
# PROCESS MATCHES
# -----------------------------

for file in MATCH_FILES:

    with open(file, "r", encoding="utf-8") as f:
        match = json.load(f)

    info = match["info"]

    registry = info.get("registry", {}).get("people", {})

    # Check whether Virat appears in this match
    player_found = False

    for team_players in info.get("players", {}).values():

        for player_name in team_players:

            player_id = get_player_id(player_name, registry)

            if player_id == TARGET_ID:
                player_found = True
                break

        if player_found:
            break

    if not player_found:
        continue

    matches += 1

    # Track batting innings score for this match innings
    match_batting_scores = []

    # Track bowling figures for each innings
    match_bowling_figures = []

    # -----------------------------
    # INNINGS
    # -----------------------------

    for innings in match.get("innings", []):

        team = innings.get("team")

        # Batting
        player_batted = False
        innings_runs = 0
        innings_balls = 0
        innings_fours = 0
        innings_sixes = 0
        player_dismissed = False

        # Bowling
        player_bowled = False
        innings_bowling_balls = 0
        innings_runs_conceded = 0
        innings_wickets = 0

        for over in innings.get("overs", []):

            for delivery in over.get("deliveries", []):

                batter_name = delivery.get("batter")
                bowler_name = delivery.get("bowler")

                batter_id = get_player_id(batter_name, registry)
                bowler_id = get_player_id(bowler_name, registry)

                delivery_runs = delivery.get("runs", {})

                batter_runs = delivery_runs.get("batter", 0)
                total_runs = delivery_runs.get("total", 0)

                extras = delivery.get("extras", {})

                # -----------------------------
                # BATTING
                # -----------------------------

                if batter_id == TARGET_ID:

                    player_batted = True

                    innings_runs += batter_runs

                    # Balls faced:
                    # wides and no-balls do not count
                    if "wides" not in extras and "noballs" not in extras:
                        innings_balls += 1

                    if batter_runs == 4:
                        innings_fours += 1

                    if batter_runs == 6:
                        innings_sixes += 1

                # -----------------------------
                # BOWLING
                # -----------------------------

                if bowler_id == TARGET_ID:

                    player_bowled = True

                    # Legal delivery
                    if "wides" not in extras and "noballs" not in extras:
                        innings_bowling_balls += 1

                    # Bowler does NOT get charged for byes/leg-byes
                    bowler_runs = total_runs

                    bowler_runs -= extras.get("byes", 0)
                    bowler_runs -= extras.get("legbyes", 0)
                    bowler_runs -= extras.get("penalty", 0)

                    innings_runs_conceded += bowler_runs

                # -----------------------------
                # WICKETS / FIELDING
                # -----------------------------

                for wicket in delivery.get("wickets", []):

                    player_out = wicket.get("player_out")
                    dismissal_kind = wicket.get("kind")

                    player_out_id = get_player_id(
                        player_out,
                        registry
                    )

                    # Was our player dismissed while batting?
                    if player_out_id == TARGET_ID:

                        player_dismissed = True

                    # Bowling wicket
                    if bowler_id == TARGET_ID:

                        non_bowler_dismissals = {
                            "run out",
                            "retired hurt",
                            "retired out",
                            "obstructing the field"
                        }

                        if dismissal_kind not in non_bowler_dismissals:

                            innings_wickets += 1

                    # Fielding
                    fielders = wicket.get("fielders", [])

                    for fielder in fielders:

                        fielder_name = fielder.get("name")

                        fielder_id = get_player_id(
                            fielder_name,
                            registry
                        )

                        if fielder_id != TARGET_ID:
                            continue

                        if dismissal_kind == "caught":
                            catches += 1

                        elif dismissal_kind == "run out":
                            run_outs += 1

                        elif dismissal_kind == "stumped":
                            stumpings += 1

        # -----------------------------
        # SAVE BATTING INNINGS
        # -----------------------------

        if player_batted:

            batting_innings += 1

            runs += innings_runs
            balls_faced += innings_balls
            fours += innings_fours
            sixes += innings_sixes

            if innings_runs >= 100:
                hundreds += 1

            elif innings_runs >= 50:
                fifties += 1

            if innings_runs > highest_score:
                highest_score = innings_runs

            if player_dismissed:
                dismissals += 1

        # -----------------------------
        # SAVE BOWLING INNINGS
        # -----------------------------

        if player_bowled:

            bowling_innings += 1

            bowling_balls += innings_bowling_balls
            runs_conceded += innings_runs_conceded
            wickets += innings_wickets

            if innings_wickets >= 4:
                four_wickets += 1

            if innings_wickets >= 5:
                five_wickets += 1

            # Best bowling figures
            if innings_wickets > best_bowling_wickets:

                best_bowling_wickets = innings_wickets
                best_bowling_runs = innings_runs_conceded

            elif innings_wickets == best_bowling_wickets:

                if innings_runs_conceded < best_bowling_runs:
                    best_bowling_runs = innings_runs_conceded


# -----------------------------
# CALCULATIONS
# -----------------------------

batting_average = (
    runs / dismissals
    if dismissals > 0
    else runs
)

strike_rate = (
    (runs / balls_faced) * 100
    if balls_faced > 0
    else 0
)

overs = (
    bowling_balls // 6
    + (bowling_balls % 6) / 10
)

economy = (
    runs_conceded / (bowling_balls / 6)
    if bowling_balls > 0
    else 0
)

bowling_average = (
    runs_conceded / wickets
    if wickets > 0
    else 0
)

bowling_strike_rate = (
    bowling_balls / wickets
    if wickets > 0
    else 0
)


# -----------------------------
# PRINT RESULTS
# -----------------------------

print("\n==============================")
print("      CRICMESH TEST STATS")
print("==============================")

print("\nPLAYER")
print("Virat Kohli")
print("Cricsheet ID:", TARGET_ID)

print("\n--- BATTING ---")

print("Matches:", matches)
print("Innings:", batting_innings)
print("Runs:", runs)
print("Balls:", balls_faced)
print("Average:", round(batting_average, 2))
print("Strike Rate:", round(strike_rate, 2))
print("50s:", fifties)
print("100s:", hundreds)
print("Highest Score:", highest_score)
print("4s:", fours)
print("6s:", sixes)

print("\n--- BOWLING ---")

print("Bowling Innings:", bowling_innings)
print("Balls:", bowling_balls)
print("Overs:", overs)
print("Runs Conceded:", runs_conceded)
print("Wickets:", wickets)
print("Average:", round(bowling_average, 2))
print("Economy:", round(economy, 2))
print("Strike Rate:", round(bowling_strike_rate, 2))
print("4 Wicket Hauls:", four_wickets)
print("5 Wicket Hauls:", five_wickets)

if wickets > 0:
    print(
        "Best Bowling:",
        f"{best_bowling_wickets}/{best_bowling_runs}"
    )
else:
    print("Best Bowling: 0/0")

print("\n--- FIELDING ---")

print("Catches:", catches)
print("Run Outs:", run_outs)
print("Stumpings:", stumpings)

print("\n==============================")