import json
import glob
import os


# ============================================================
# CRICMESH GENERIC CRICKET STATS ENGINE
# Supports:
#   - Test
#   - ODI
#   - T20I
# ============================================================

FORMAT_FOLDERS = {
    "test": "backend/data/matches/test",
    "odi": "backend/data/matches/odi",
    "t20i": "backend/data/matches/t20i",
}


# Dismissals where the bowler does NOT get credit
NON_BOWLER_DISMISSALS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
    "retired not out",
}


def get_match_files(format_name):
    """
    Return all JSON match files for a format.
    """

    format_name = format_name.lower()

    if format_name not in FORMAT_FOLDERS:
        raise ValueError(
            f"Unsupported format: {format_name}. "
            f"Use one of: {list(FORMAT_FOLDERS.keys())}"
        )

    folder = FORMAT_FOLDERS[format_name]

    if not os.path.exists(folder):
        raise FileNotFoundError(
            f"Match folder not found: {folder}"
        )

    return glob.glob(
        os.path.join(folder, "*.json")
    )


def calculate_stats(player_id, format_name):
    """
    Calculate complete cricket statistics for one player
    in one format.

    Example:
        calculate_stats("ba607b88", "test")
        calculate_stats("ba607b88", "odi")
    """

    match_files = get_match_files(format_name)

    # ========================================================
    # PLAYER TOTALS
    # ========================================================

    matches = 0

    # --------------------------------------------------------
    # Batting
    # --------------------------------------------------------

    batting_innings = 0
    runs = 0
    balls_faced = 0
    fours = 0
    sixes = 0
    dismissals = 0
    fifties = 0
    hundreds = 0

    highest_score = 0
    highest_score_not_out = False

    # --------------------------------------------------------
    # Bowling
    # --------------------------------------------------------

    bowling_innings = 0
    bowling_balls = 0
    runs_conceded = 0
    wickets = 0

    four_wicket_hauls = 0
    five_wicket_hauls = 0

    best_bowling_wickets = 0
    best_bowling_runs = None

    # --------------------------------------------------------
    # Fielding
    # --------------------------------------------------------

    catches = 0
    run_outs = 0
    stumpings = 0

    # ========================================================
    # PROCESS EVERY MATCH
    # ========================================================

    for match_file in match_files:

        with open(
            match_file,
            "r",
            encoding="utf-8"
        ) as f:

            match = json.load(f)

        # ====================================================
        # REGISTRY
        #
        # IMPORTANT:
        # Cricsheet JSON stores registry inside info.
        # ====================================================

        info = match.get("info", {})

        registry = info.get(
            "registry",
            {}
        )

        people = registry.get(
            "people",
            {}
        )

        # ----------------------------------------------------
        # Find player's name used in this match
        # ----------------------------------------------------

        player_name = None

        for name, identifier in people.items():

            if identifier == player_id:

                player_name = name
                break

        # Player did not participate in this match
        if player_name is None:
            continue

        matches += 1

        # ====================================================
        # PROCESS MATCH INNINGS
        # ====================================================

        for innings in match.get(
            "innings",
            []
        ):

            overs = innings.get(
                "overs",
                []
            )

            # =================================================
            # INNINGS VARIABLES
            # =================================================

            player_batted = False
            player_bowled = False

            # -------------------------------------------------
            # Batting
            # -------------------------------------------------

            innings_runs = 0
            innings_balls = 0
            innings_fours = 0
            innings_sixes = 0

            # -------------------------------------------------
            # Bowling
            # -------------------------------------------------

            innings_bowling_balls = 0
            innings_runs_conceded = 0
            innings_wickets = 0

            # =================================================
            # PROCESS EVERY DELIVERY
            # =================================================

            for over in overs:

                for delivery in over.get(
                    "deliveries",
                    []
                ):

                    batter = delivery.get(
                        "batter"
                    )

                    bowler = delivery.get(
                        "bowler"
                    )

                    runs_data = delivery.get(
                        "runs",
                        {}
                    )

                    extras = delivery.get(
                        "extras",
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

                    # =================================================
                    # BATTING
                    # =================================================

                    if batter == player_name:

                        player_batted = True

                        innings_runs += batter_runs

                        # ------------------------------------------------
                        # BALLS FACED
                        #
                        # Wides are not balls faced.
                        # No-balls are included to match the convention
                        # used by the published statistics we verified.
                        # ------------------------------------------------

                        if "wides" not in extras:

                            innings_balls += 1

                        # ------------------------------------------------
                        # BOUNDARIES
                        #
                        # A 4/6 with non_boundary=True is not counted
                        # as an actual boundary.
                        # ------------------------------------------------

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

                    if bowler == player_name:

                        player_bowled = True

                        # ------------------------------------------------
                        # LEGAL BOWLING BALL
                        #
                        # Wides and no-balls are not legal deliveries.
                        # ------------------------------------------------

                        if (
                            "wides" not in extras
                            and "noballs" not in extras
                        ):

                            innings_bowling_balls += 1

                        # ------------------------------------------------
                        # BOWLER RUNS CONCEDED
                        #
                        # Byes, leg-byes and penalty runs are not
                        # charged to the bowler.
                        # ------------------------------------------------

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

                        innings_runs_conceded += bowler_runs

                    # =================================================
                    # WICKETS / FIELDING
                    # =================================================

                    for wicket in delivery.get(
                        "wickets",
                        []
                    ):

                        dismissed_player = wicket.get(
                            "player_out"
                        )

                        dismissal_kind = wicket.get(
                            "kind",
                            ""
                        ).lower()

                        fielders = wicket.get(
                            "fielders",
                            []
                        )

                        # =============================================
                        # PLAYER'S BATTING DISMISSAL
                        # =============================================

                        if (
                            dismissed_player
                            == player_name
                        ):

                            dismissals += 1

                        # =============================================
                        # PLAYER'S BOWLING WICKET
                        # =============================================

                        if bowler == player_name:

                            if (
                                dismissal_kind
                                not in NON_BOWLER_DISMISSALS
                            ):

                                innings_wickets += 1

                        # =============================================
                        # CATCHES
                        # =============================================

                        if dismissal_kind == "caught":

                            for fielder in fielders:

                                fielder_name = fielder.get(
                                    "name"
                                )

                                if (
                                    fielder_name
                                    == player_name
                                ):

                                    catches += 1

                        # =============================================
                        # RUN OUTS
                        # =============================================

                        elif dismissal_kind == "run out":

                            for fielder in fielders:

                                fielder_name = fielder.get(
                                    "name"
                                )

                                if (
                                    fielder_name
                                    == player_name
                                ):

                                    run_outs += 1

                        # =============================================
                        # STUMPINGS
                        # =============================================

                        elif dismissal_kind == "stumped":

                            for fielder in fielders:

                                fielder_name = fielder.get(
                                    "name"
                                )

                                if (
                                    fielder_name
                                    == player_name
                                ):

                                    stumpings += 1

            # =================================================
            # FINISH BATTING INNINGS
            # =================================================

            if player_batted:

                batting_innings += 1

                runs += innings_runs

                balls_faced += innings_balls

                fours += innings_fours

                sixes += innings_sixes

                # ---------------------------------------------
                # Check whether player was dismissed
                # ---------------------------------------------

                innings_was_dismissed = False

                for over in overs:

                    for delivery in over.get(
                        "deliveries",
                        []
                    ):

                        for wicket in delivery.get(
                            "wickets",
                            []
                        ):

                            if (
                                wicket.get("player_out")
                                == player_name
                            ):

                                innings_was_dismissed = True

                                break

                        if innings_was_dismissed:
                            break

                    if innings_was_dismissed:
                        break

                # ---------------------------------------------
                # Highest score
                # ---------------------------------------------

                if innings_runs > highest_score:

                    highest_score = innings_runs

                    highest_score_not_out = (
                        not innings_was_dismissed
                    )

                elif innings_runs == highest_score:

                    if not innings_was_dismissed:

                        highest_score_not_out = True

                # ---------------------------------------------
                # 50s
                # ---------------------------------------------

                if (
                    50 <= innings_runs < 100
                ):

                    fifties += 1

                # ---------------------------------------------
                # 100s
                # ---------------------------------------------

                if innings_runs >= 100:

                    hundreds += 1

            # =================================================
            # FINISH BOWLING INNINGS
            # =================================================

            if player_bowled:

                bowling_innings += 1

                bowling_balls += (
                    innings_bowling_balls
                )

                runs_conceded += (
                    innings_runs_conceded
                )

                wickets += innings_wickets

                # ---------------------------------------------
                # 4 wicket haul
                # ---------------------------------------------

                if innings_wickets >= 4:

                    four_wicket_hauls += 1

                # ---------------------------------------------
                # 5 wicket haul
                # ---------------------------------------------

                if innings_wickets >= 5:

                    five_wicket_hauls += 1

                # ---------------------------------------------
                # Best bowling
                # ---------------------------------------------

                if (
                    innings_wickets
                    > best_bowling_wickets
                ):

                    best_bowling_wickets = (
                        innings_wickets
                    )

                    best_bowling_runs = (
                        innings_runs_conceded
                    )

                elif (
                    innings_wickets
                    == best_bowling_wickets
                    and innings_wickets > 0
                ):

                    if (
                        best_bowling_runs is None
                        or innings_runs_conceded
                        < best_bowling_runs
                    ):

                        best_bowling_runs = (
                            innings_runs_conceded
                        )

    # ========================================================
    # CALCULATED STATISTICS
    # ========================================================

    # Number of innings where player was not dismissed
    not_outs = (
        batting_innings - dismissals
    )

    # --------------------------------------------------------
    # Batting average
    # --------------------------------------------------------

    if dismissals > 0:

        batting_average = (
            runs / dismissals
        )

    else:

        batting_average = 0

    # --------------------------------------------------------
    # Strike rate
    # --------------------------------------------------------

    if balls_faced > 0:

        strike_rate = (
            runs / balls_faced
        ) * 100

    else:

        strike_rate = 0

    # --------------------------------------------------------
    # Bowling average
    # --------------------------------------------------------

    if wickets > 0:

        bowling_average = (
            runs_conceded / wickets
        )

    else:

        bowling_average = 0

    # --------------------------------------------------------
    # Economy
    # --------------------------------------------------------

    if bowling_balls > 0:

        economy = (
            runs_conceded
            / bowling_balls
        ) * 6

    else:

        economy = 0

    # --------------------------------------------------------
    # Bowling strike rate
    # --------------------------------------------------------

    if wickets > 0:

        bowling_strike_rate = (
            bowling_balls / wickets
        )

    else:

        bowling_strike_rate = 0

    # ========================================================
    # OVERS
    # ========================================================

    complete_overs = (
        bowling_balls // 6
    )

    remaining_balls = (
        bowling_balls % 6
    )

    overs_display = (
        f"{complete_overs}.{remaining_balls}"
    )

    # ========================================================
    # BEST BOWLING
    # ========================================================

    if best_bowling_runs is None:

        best_bowling_runs = 0

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        # ----------------------------------------------------
        # General
        # ----------------------------------------------------

        "matches": matches,

        # ----------------------------------------------------
        # Batting
        # ----------------------------------------------------

        "batting_innings": batting_innings,

        "runs": runs,

        "balls_faced": balls_faced,

        "fours": fours,

        "sixes": sixes,

        "dismissals": dismissals,

        "not_outs": not_outs,

        "fifties": fifties,

        "hundreds": hundreds,

        "highest_score": highest_score,

        "highest_score_not_out": (
            highest_score_not_out
        ),

        # ----------------------------------------------------
        # Bowling
        # ----------------------------------------------------

        "bowling_innings": bowling_innings,

        "bowling_balls": bowling_balls,

        "runs_conceded": runs_conceded,

        "wickets": wickets,

        "four_wicket_hauls": (
            four_wicket_hauls
        ),

        "five_wicket_hauls": (
            five_wicket_hauls
        ),

        "best_bowling_wickets": (
            best_bowling_wickets
        ),

        "best_bowling_runs": (
            best_bowling_runs
        ),

        # ----------------------------------------------------
        # Fielding
        # ----------------------------------------------------

        "catches": catches,

        "run_outs": run_outs,

        "stumpings": stumpings,

        # ----------------------------------------------------
        # Calculated batting statistics
        # ----------------------------------------------------

        "batting_average": round(
            batting_average,
            2
        ),

        "strike_rate": round(
            strike_rate,
            2
        ),

        # ----------------------------------------------------
        # Calculated bowling statistics
        # ----------------------------------------------------

        "bowling_average": round(
            bowling_average,
            2
        ),

        "economy": round(
            economy,
            2
        ),

        "bowling_strike_rate": round(
            bowling_strike_rate,
            2
        ),

        # ----------------------------------------------------
        # Overs
        # ----------------------------------------------------

        "overs": overs_display,
    }