import json
import glob
import re


MATCH_FILES = glob.glob(
    "backend/data/matches/test/*.json"
)


def normalize_name(name):
    """
    Normalize a player name so small formatting differences
    do not affect player identification.
    """
    name = str(name).lower()
    return re.sub(r"[^a-z0-9]", "", name)


def get_player_id(name, registry):
    """
    Find the Cricsheet player ID for a name
    appearing in a match.
    """

    if not name:
        return None

    # Exact match
    if name in registry:
        return registry[name]

    # Normalized match
    normalized = normalize_name(name)

    for registry_name, player_id in registry.items():

        if normalize_name(registry_name) == normalized:
            return player_id

    return None


def calculate_test_stats(player_id):

    stats = {
        # MATCHES
        "matches": 0,

        # BATTING
        "batting_innings": 0,
        "runs": 0,
        "balls_faced": 0,
        "fours": 0,
        "sixes": 0,
        "dismissals": 0,
        "fifties": 0,
        "hundreds": 0,
        "highest_score": 0,

        # BOWLING
        "bowling_innings": 0,
        "bowling_balls": 0,
        "runs_conceded": 0,
        "wickets": 0,
        "four_wicket_hauls": 0,
        "five_wicket_hauls": 0,
        "best_bowling_wickets": 0,
        "best_bowling_runs": 0,

        # FIELDING
        "catches": 0,
        "run_outs": 0,
        "stumpings": 0,
    }

    # =========================================================
    # PROCESS ALL TEST MATCHES
    # =========================================================

    for file in MATCH_FILES:

        with open(file, "r", encoding="utf-8") as f:
            match = json.load(f)

        info = match.get("info", {})

        registry = (
            info
            .get("registry", {})
            .get("people", {})
        )

        # =====================================================
        # CHECK WHETHER PLAYER PLAYED THIS MATCH
        # =====================================================

        player_found = False

        for team_players in info.get(
            "players",
            {}
        ).values():

            for player_name in team_players:

                player_match_id = get_player_id(
                    player_name,
                    registry
                )

                if player_match_id == player_id:

                    player_found = True
                    break

            if player_found:
                break

        if not player_found:
            continue

        stats["matches"] += 1

        # =====================================================
        # PROCESS EACH INNINGS
        # =====================================================

        for innings in match.get(
            "innings",
            []
        ):

            # -------------------------------------------------
            # BATTING
            # -------------------------------------------------

            player_batted = False
            player_dismissed = False

            innings_runs = 0
            innings_balls = 0
            innings_fours = 0
            innings_sixes = 0

            # -------------------------------------------------
            # BOWLING
            # -------------------------------------------------

            player_bowled = False

            innings_bowling_balls = 0
            innings_runs_conceded = 0
            innings_wickets = 0

            # =================================================
            # PROCESS OVERS
            # =================================================

            for over in innings.get(
                "overs",
                []
            ):

                for delivery in over.get(
                    "deliveries",
                    []
                ):

                    batter_name = delivery.get(
                        "batter"
                    )

                    bowler_name = delivery.get(
                        "bowler"
                    )

                    batter_id = get_player_id(
                        batter_name,
                        registry
                    )

                    bowler_id = get_player_id(
                        bowler_name,
                        registry
                    )

                    runs_data = delivery.get(
                        "runs",
                        {}
                    )

                    batter_runs = runs_data.get(
                        "batter",
                        0
                    )

                    total_runs = runs_data.get(
                        "total",
                        0
                    )

                    extras = delivery.get(
                        "extras",
                        {}
                    )

                    # =================================================
                    # BATTING
                    # =================================================

                    if batter_id == player_id:

                        player_batted = True

                        innings_runs += batter_runs

                        # -------------------------------------------------
                        # BALLS FACED
                        #
                        # Wide = NOT a ball faced
                        # No-ball = IS counted as a ball faced
                        # for the statistics convention being used.
                        # -------------------------------------------------

                        if "wides" not in extras:

                            innings_balls += 1

                        # -------------------------------------------------
                        # BOUNDARIES
                        #
                        # non_boundary=True means the batter received
                        # 4 or 6 runs, but it was not an actual boundary.
                        # -------------------------------------------------

                        non_boundary = runs_data.get(
                            "non_boundary",
                            False
                        )

                        if (
                            batter_runs == 4
                            and not non_boundary
                        ):

                            innings_fours += 1

                        if (
                            batter_runs == 6
                            and not non_boundary
                        ):

                            innings_sixes += 1

                    # =================================================
                    # BOWLING
                    # =================================================

                    if bowler_id == player_id:

                        player_bowled = True

                        # -------------------------------------------------
                        # LEGAL BALL
                        #
                        # Wides and no-balls are NOT legal deliveries.
                        # -------------------------------------------------

                        if (
                            "wides" not in extras
                            and "noballs" not in extras
                        ):

                            innings_bowling_balls += 1

                        # -------------------------------------------------
                        # RUNS CONCEDED
                        #
                        # Byes and leg-byes are not charged to bowler.
                        # Wides and no-balls are charged.
                        # -------------------------------------------------

                        bowler_runs = total_runs

                        bowler_runs -= extras.get(
                            "byes",
                            0
                        )

                        bowler_runs -= extras.get(
                            "legbyes",
                            0
                        )

                        bowler_runs -= extras.get(
                            "penalty",
                            0
                        )

                        innings_runs_conceded += (
                            bowler_runs
                        )

                    # =================================================
                    # WICKETS
                    # =================================================

                    for wicket in delivery.get(
                        "wickets",
                        []
                    ):

                        player_out = wicket.get(
                            "player_out"
                        )

                        dismissal_kind = wicket.get(
                            "kind"
                        )

                        player_out_id = get_player_id(
                            player_out,
                            registry
                        )

                        # -------------------------------------------------
                        # OUR PLAYER WAS DISMISSED
                        # -------------------------------------------------

                        if player_out_id == player_id:

                            player_dismissed = True

                        # -------------------------------------------------
                        # BOWLER WICKET
                        # -------------------------------------------------

                        if bowler_id == player_id:

                            non_bowler_dismissals = {
                                "run out",
                                "retired hurt",
                                "retired out",
                                "obstructing the field",
                            }

                            if (
                                dismissal_kind
                                not in non_bowler_dismissals
                            ):

                                innings_wickets += 1

                        # =================================================
                        # FIELDING
                        # =================================================

                        for fielder in wicket.get(
                            "fielders",
                            []
                        ):

                            fielder_name = fielder.get(
                                "name"
                            )

                            fielder_id = get_player_id(
                                fielder_name,
                                registry
                            )

                            if fielder_id != player_id:
                                continue

                            if dismissal_kind == "caught":

                                stats["catches"] += 1

                            elif dismissal_kind == "run out":

                                stats["run_outs"] += 1

                            elif dismissal_kind == "stumped":

                                stats["stumpings"] += 1

            # =====================================================
            # SAVE BATTING INNINGS
            # =====================================================

            if player_batted:

                stats["batting_innings"] += 1

                stats["runs"] += innings_runs

                stats["balls_faced"] += innings_balls

                stats["fours"] += innings_fours

                stats["sixes"] += innings_sixes

                # 100+
                if innings_runs >= 100:

                    stats["hundreds"] += 1

                # 50-99
                elif innings_runs >= 50:

                    stats["fifties"] += 1

                # Highest score
                if (
                    innings_runs
                    > stats["highest_score"]
                ):

                    stats["highest_score"] = (
                        innings_runs
                    )

                # Dismissed
                if player_dismissed:

                    stats["dismissals"] += 1

            # =====================================================
            # SAVE BOWLING INNINGS
            # =====================================================

            if player_bowled:

                stats["bowling_innings"] += 1

                stats["bowling_balls"] += (
                    innings_bowling_balls
                )

                stats["runs_conceded"] += (
                    innings_runs_conceded
                )

                stats["wickets"] += (
                    innings_wickets
                )

                # 4-wicket haul
                if innings_wickets >= 4:

                    stats["four_wicket_hauls"] += 1

                # 5-wicket haul
                if innings_wickets >= 5:

                    stats["five_wicket_hauls"] += 1

                # =================================================
                # BEST BOWLING
                # =================================================

                if innings_wickets > 0:

                    current_best_wickets = (
                        stats["best_bowling_wickets"]
                    )

                    current_best_runs = (
                        stats["best_bowling_runs"]
                    )

                    # More wickets = better
                    if (
                        innings_wickets
                        > current_best_wickets
                    ):

                        stats[
                            "best_bowling_wickets"
                        ] = innings_wickets

                        stats[
                            "best_bowling_runs"
                        ] = innings_runs_conceded

                    # Same wickets, fewer runs = better
                    elif (
                        innings_wickets
                        == current_best_wickets
                    ):

                        if (
                            current_best_wickets == 0
                            or innings_runs_conceded
                            < current_best_runs
                        ):

                            stats[
                                "best_bowling_runs"
                            ] = innings_runs_conceded

    # =========================================================
    # BATTING AVERAGE
    # =========================================================

    if stats["dismissals"] > 0:

        stats["batting_average"] = round(
            stats["runs"]
            / stats["dismissals"],
            2
        )

    else:

        stats["batting_average"] = 0

    # =========================================================
    # STRIKE RATE
    # =========================================================

    if stats["balls_faced"] > 0:

        stats["strike_rate"] = round(
            (
                stats["runs"]
                / stats["balls_faced"]
            ) * 100,
            2
        )

    else:

        stats["strike_rate"] = 0

    # =========================================================
    # BOWLING AVERAGE
    # =========================================================

    if stats["wickets"] > 0:

        stats["bowling_average"] = round(
            stats["runs_conceded"]
            / stats["wickets"],
            2
        )

    else:

        stats["bowling_average"] = 0

    # =========================================================
    # BOWLING STRIKE RATE
    # =========================================================

    if stats["wickets"] > 0:

        stats["bowling_strike_rate"] = round(
            stats["bowling_balls"]
            / stats["wickets"],
            2
        )

    else:

        stats["bowling_strike_rate"] = 0

    # =========================================================
    # ECONOMY
    # =========================================================

    if stats["bowling_balls"] > 0:

        stats["economy"] = round(
            stats["runs_conceded"]
            / (
                stats["bowling_balls"]
                / 6
            ),
            2
        )

    else:

        stats["economy"] = 0

    # =========================================================
    # OVERS
    # =========================================================

    legal_balls = stats["bowling_balls"]

    stats["overs"] = (
        f"{legal_balls // 6}."
        f"{legal_balls % 6}"
    )

    return stats