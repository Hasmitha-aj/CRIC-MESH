import json
import glob
import os

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity


# =============================================================
# FILE PATHS
# =============================================================

FORMAT_FOLDERS = {
    "test": "backend/data/matches/test",
    "odi": "backend/data/matches/odi",
    "t20i": "backend/data/matches/t20i",
}

PEOPLE_FILE = "backend/data/people.csv"
ALIASES_FILE = "backend/data/player_aliases.csv"


# =============================================================
# LOAD PLAYER NAMES
# =============================================================

people_df = pd.read_csv(PEOPLE_FILE)

people_df["identifier"] = (
    people_df["identifier"]
    .fillna("")
    .astype(str)
    .str.strip()
)

people_df["name"] = people_df["name"].fillna("")
people_df["unique_name"] = people_df["unique_name"].fillna("")


# Start with names from people.csv
PLAYER_NAME_MAP = {}

for _, row in people_df.iterrows():

    player_id = str(
        row["identifier"]
    ).strip()

    unique_name = str(
        row["unique_name"]
    ).strip()

    registered_name = str(
        row["name"]
    ).strip()

    display_name = (
        unique_name
        if unique_name
        else registered_name
    )

    if player_id and display_name:

        PLAYER_NAME_MAP[player_id] = display_name


# =============================================================
# LOAD FULL NAMES FROM player_aliases.csv
# =============================================================

if os.path.exists(ALIASES_FILE):

    aliases_df = pd.read_csv(
        ALIASES_FILE
    )

    aliases_df["identifier"] = (
        aliases_df["identifier"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    aliases_df["full_name"] = (
        aliases_df["full_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # IMPORTANT:
    # Alias full names override people.csv names.
    for _, row in aliases_df.iterrows():

        player_id = str(
            row["identifier"]
        ).strip()

        full_name = str(
            row["full_name"]
        ).strip()

        if player_id and full_name:

            PLAYER_NAME_MAP[
                player_id
            ] = full_name


# =============================================================
# DISMISSALS THAT DO NOT COUNT AS BOWLER WICKETS
# =============================================================

NON_BOWLER_DISMISSALS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
    "retired not out",
}


# =============================================================
# BUILD PLAYER DATASET
# =============================================================

def build_player_dataset(format_name):

    format_name = format_name.lower()

    if format_name not in FORMAT_FOLDERS:

        raise ValueError(
            "Format must be test, odi, or t20i."
        )

    folder = FORMAT_FOLDERS[
        format_name
    ]

    if not os.path.exists(folder):

        raise FileNotFoundError(
            f"Match folder not found: {folder}"
        )

    match_files = glob.glob(
        os.path.join(
            folder,
            "*.json"
        )
    )

    players = {}

    # =========================================================
    # PROCESS EVERY MATCH
    # =========================================================

    for match_file in match_files:

        with open(
            match_file,
            "r",
            encoding="utf-8"
        ) as f:

            match = json.load(f)

        info = match.get(
            "info",
            {}
        )

        registry = info.get(
            "registry",
            {}
        )

        people = registry.get(
            "people",
            {}
        )

        # -----------------------------------------------------
        # REGISTER PLAYERS
        # -----------------------------------------------------

        for player_name, player_id in people.items():

            if player_id not in players:

                players[player_id] = {

                    "player_id":
                        player_id,

                    "name":
                        player_name,

                    # Career volume
                    "matches": 0,

                    # Batting
                    "batting_innings": 0,
                    "runs": 0,
                    "balls_faced": 0,
                    "fours": 0,
                    "sixes": 0,
                    "dismissals": 0,
                    "fifties": 0,
                    "hundreds": 0,
                    "highest_score": 0,

                    # Bowling
                    "bowling_innings": 0,
                    "bowling_balls": 0,
                    "runs_conceded": 0,
                    "wickets": 0,

                    # Fielding
                    "catches": 0,
                    "run_outs": 0,
                    "stumpings": 0,
                }

            players[player_id][
                "matches"
            ] += 1

        # =====================================================
        # PROCESS INNINGS
        # =====================================================

        for innings in match.get(
            "innings",
            []
        ):

            overs = innings.get(
                "overs",
                []
            )

            innings_batting = {}
            innings_bowling = {}

            dismissed_players = set()

            # -------------------------------------------------
            # PROCESS DELIVERIES
            # -------------------------------------------------

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

                    # =========================================
                    # BATTING
                    # =========================================

                    if batter in people:

                        player_id = people[
                            batter
                        ]

                        if player_id not in innings_batting:

                            innings_batting[
                                player_id
                            ] = {

                                "runs": 0,
                                "balls": 0,
                                "fours": 0,
                                "sixes": 0,
                            }

                        data = innings_batting[
                            player_id
                        ]

                        data["runs"] += (
                            batter_runs
                        )

                        # Wides are not balls faced.
                        # No-balls are included.
                        if "wides" not in extras:

                            data["balls"] += 1

                        non_boundary = (
                            runs_data.get(
                                "non_boundary",
                                False
                            )
                        )

                        if (
                            batter_runs == 4
                            and not non_boundary
                        ):

                            data["fours"] += 1

                        if (
                            batter_runs == 6
                            and not non_boundary
                        ):

                            data["sixes"] += 1

                    # =========================================
                    # BOWLING
                    # =========================================

                    if bowler in people:

                        player_id = people[
                            bowler
                        ]

                        if player_id not in innings_bowling:

                            innings_bowling[
                                player_id
                            ] = {

                                "balls": 0,
                                "runs": 0,
                                "wickets": 0,
                            }

                        data = innings_bowling[
                            player_id
                        ]

                        # Legal bowling delivery
                        if (
                            "wides" not in extras
                            and "noballs" not in extras
                        ):

                            data["balls"] += 1

                        bowler_runs = (
                            total_runs
                        )

                        # These are not charged
                        # to the bowler.
                        bowler_runs -= (
                            extras.get(
                                "byes",
                                0
                            )
                        )

                        bowler_runs -= (
                            extras.get(
                                "legbyes",
                                0
                            )
                        )

                        bowler_runs -= (
                            extras.get(
                                "penalty",
                                0
                            )
                        )

                        data["runs"] += (
                            bowler_runs
                        )

                    # =========================================
                    # WICKETS + FIELDING
                    # =========================================

                    for wicket in delivery.get(
                        "wickets",
                        []
                    ):

                        dismissed_player = (
                            wicket.get(
                                "player_out"
                            )
                        )

                        dismissal_kind = (
                            wicket.get(
                                "kind",
                                ""
                            )
                            .lower()
                        )

                        fielders = (
                            wicket.get(
                                "fielders",
                                []
                            )
                        )

                        # -------------------------------------
                        # Dismissed player
                        # -------------------------------------

                        if dismissed_player in people:

                            dismissed_id = (
                                people[
                                    dismissed_player
                                ]
                            )

                            dismissed_players.add(
                                dismissed_id
                            )

                        # -------------------------------------
                        # Bowler wicket
                        # -------------------------------------

                        if bowler in people:

                            bowler_id = people[
                                bowler
                            ]

                            if (
                                dismissal_kind
                                not in NON_BOWLER_DISMISSALS
                            ):

                                if (
                                    bowler_id
                                    not in innings_bowling
                                ):

                                    innings_bowling[
                                        bowler_id
                                    ] = {

                                        "balls": 0,
                                        "runs": 0,
                                        "wickets": 0,
                                    }

                                innings_bowling[
                                    bowler_id
                                ]["wickets"] += 1

                        # -------------------------------------
                        # Fielding
                        # -------------------------------------

                        for fielder in fielders:

                            fielder_name = (
                                fielder.get(
                                    "name"
                                )
                            )

                            if (
                                fielder_name
                                not in people
                            ):
                                continue

                            fielder_id = people[
                                fielder_name
                            ]

                            if (
                                dismissal_kind
                                == "caught"
                            ):

                                players[
                                    fielder_id
                                ]["catches"] += 1

                            elif (
                                dismissal_kind
                                == "run out"
                            ):

                                players[
                                    fielder_id
                                ]["run_outs"] += 1

                            elif (
                                dismissal_kind
                                == "stumped"
                            ):

                                players[
                                    fielder_id
                                ]["stumpings"] += 1

            # =================================================
            # ADD BATTING DATA
            # =================================================

            for player_id, data in (
                innings_batting.items()
            ):

                player = players[
                    player_id
                ]

                player[
                    "batting_innings"
                ] += 1

                player[
                    "runs"
                ] += data["runs"]

                player[
                    "balls_faced"
                ] += data["balls"]

                player[
                    "fours"
                ] += data["fours"]

                player[
                    "sixes"
                ] += data["sixes"]

                if player_id in dismissed_players:

                    player[
                        "dismissals"
                    ] += 1

                score = data[
                    "runs"
                ]

                if score > player[
                    "highest_score"
                ]:

                    player[
                        "highest_score"
                    ] = score

                if (
                    50 <= score < 100
                ):

                    player[
                        "fifties"
                    ] += 1

                if score >= 100:

                    player[
                        "hundreds"
                    ] += 1

            # =================================================
            # ADD BOWLING DATA
            # =================================================

            for player_id, data in (
                innings_bowling.items()
            ):

                player = players[
                    player_id
                ]

                player[
                    "bowling_innings"
                ] += 1

                player[
                    "bowling_balls"
                ] += data["balls"]

                player[
                    "runs_conceded"
                ] += data["runs"]

                player[
                    "wickets"
                ] += data["wickets"]

    # =========================================================
    # FEATURE ENGINEERING
    # =========================================================

    rows = []

    for player in players.values():

        batting_innings = player[
            "batting_innings"
        ]

        dismissals = player[
            "dismissals"
        ]

        balls_faced = player[
            "balls_faced"
        ]

        bowling_balls = player[
            "bowling_balls"
        ]

        wickets = player[
            "wickets"
        ]

        # -----------------------------------------------------
        # Batting features
        # -----------------------------------------------------

        batting_average = (

            player["runs"]
            / dismissals

            if dismissals > 0

            else 0
        )

        strike_rate = (

            player["runs"]
            / balls_faced
            * 100

            if balls_faced > 0

            else 0
        )

        runs_per_innings = (

            player["runs"]
            / batting_innings

            if batting_innings > 0

            else 0
        )

        fours_per_innings = (

            player["fours"]
            / batting_innings

            if batting_innings > 0

            else 0
        )

        sixes_per_innings = (

            player["sixes"]
            / batting_innings

            if batting_innings > 0

            else 0
        )

        hundreds_per_innings = (

            player["hundreds"]
            / batting_innings

            if batting_innings > 0

            else 0
        )

        fifties_per_innings = (

            player["fifties"]
            / batting_innings

            if batting_innings > 0

            else 0
        )

        # -----------------------------------------------------
        # Bowling features
        # -----------------------------------------------------

        bowling_average = (

            player["runs_conceded"]
            / wickets

            if wickets > 0

            else 0
        )

        economy = (

            player["runs_conceded"]
            / bowling_balls
            * 6

            if bowling_balls > 0

            else 0
        )

        wickets_per_match = (

            wickets
            / player["matches"]

            if player["matches"] > 0

            else 0
        )

        # -----------------------------------------------------
        # Fielding features
        # -----------------------------------------------------

        catches_per_match = (

            player["catches"]
            / player["matches"]

            if player["matches"] > 0

            else 0
        )

        run_outs_per_match = (

            player["run_outs"]
            / player["matches"]

            if player["matches"] > 0

            else 0
        )

        stumpings_per_match = (

            player["stumpings"]
            / player["matches"]

            if player["matches"] > 0

            else 0
        )

        rows.append({

            "player_id":
                player["player_id"],

            "name":
                player["name"],

            # Experience
            "matches":
                player["matches"],

            # Batting
            "batting_average":
                batting_average,

            "strike_rate":
                strike_rate,

            "runs_per_innings":
                runs_per_innings,

            "fours_per_innings":
                fours_per_innings,

            "sixes_per_innings":
                sixes_per_innings,

            "fifties_per_innings":
                fifties_per_innings,

            "hundreds_per_innings":
                hundreds_per_innings,

            "highest_score":
                player["highest_score"],

            # Bowling
            "wickets_per_match":
                wickets_per_match,

            "bowling_average":
                bowling_average,

            "economy":
                economy,

            # Fielding
            "catches_per_match":
                catches_per_match,

            "run_outs_per_match":
                run_outs_per_match,

            "stumpings_per_match":
                stumpings_per_match,
        })

    return pd.DataFrame(
        rows
    )


# =============================================================
# FEATURES USED BY ML MODEL
# =============================================================

FEATURES = [

    "batting_average",
    "strike_rate",
    "runs_per_innings",

    "fours_per_innings",
    "sixes_per_innings",

    "fifties_per_innings",
    "hundreds_per_innings",

    "highest_score",

    "wickets_per_match",
    "bowling_average",
    "economy",

    "catches_per_match",
    "run_outs_per_match",
    "stumpings_per_match",

    "matches",
]


# =============================================================
# FIND SIMILAR PLAYERS
# =============================================================

def find_similar_players(
    player_id,
    format_name,
    top_n=5
):

    dataset = build_player_dataset(
        format_name
    )

    if dataset.empty:
        return []

    # ---------------------------------------------------------
    # Check target player
    # ---------------------------------------------------------

    target_rows = dataset[
        dataset["player_id"]
        == player_id
    ]

    if target_rows.empty:
        return []

    # ---------------------------------------------------------
    # Remove players with no meaningful statistics
    # ---------------------------------------------------------

    dataset = dataset[
        (dataset["matches"] > 0)
        &
        (
            (dataset["batting_average"] > 0)
            |
            (dataset["wickets_per_match"] > 0)
            |
            (dataset["catches_per_match"] > 0)
        )
    ].copy()

    if dataset.empty:
        return []

    # ---------------------------------------------------------
    # Check target again
    # ---------------------------------------------------------

    target_rows = dataset[
        dataset["player_id"]
        == player_id
    ]

    if target_rows.empty:
        return []

    # ---------------------------------------------------------
    # Feature matrix
    # ---------------------------------------------------------

    feature_matrix = dataset[
        FEATURES
    ].fillna(0)

    # ---------------------------------------------------------
    # Standardization
    # ---------------------------------------------------------

    scaler = StandardScaler()

    scaled_features = (
        scaler.fit_transform(
            feature_matrix
        )
    )

    # ---------------------------------------------------------
    # Feature weights
    # ---------------------------------------------------------

    weights = {

        "batting_average": 1.5,
        "strike_rate": 1.2,
        "runs_per_innings": 1.4,

        "fours_per_innings": 1.0,
        "sixes_per_innings": 1.0,

        "fifties_per_innings": 1.0,
        "hundreds_per_innings": 1.2,

        "highest_score": 0.8,

        "wickets_per_match": 1.2,
        "bowling_average": 1.0,
        "economy": 1.0,

        "catches_per_match": 0.7,
        "run_outs_per_match": 0.5,
        "stumpings_per_match": 0.5,

        "matches": 0.5,
    }

    weight_array = [

        weights[feature]

        for feature in FEATURES
    ]

    scaled_features = (
        scaled_features
        * weight_array
    )

    # ---------------------------------------------------------
    # Target vector
    # ---------------------------------------------------------

    target_index = dataset.index[
        dataset["player_id"]
        == player_id
    ][0]

    target_position = (
        dataset.index.get_loc(
            target_index
        )
    )

    target_vector = (
        scaled_features[
            target_position
        ]
        .reshape(1, -1)
    )

    # ---------------------------------------------------------
    # Cosine similarity
    # ---------------------------------------------------------

    similarity_scores = (
        cosine_similarity(
            target_vector,
            scaled_features
        )[0]
    )

    dataset[
        "similarity"
    ] = similarity_scores

    # ---------------------------------------------------------
    # Remove selected player
    # ---------------------------------------------------------

    dataset = dataset[
        dataset["player_id"]
        != player_id
    ]

    # ---------------------------------------------------------
    # Sort by similarity
    # ---------------------------------------------------------

    dataset = dataset.sort_values(
        "similarity",
        ascending=False
    )

    dataset = dataset.head(
        top_n
    )

    # =========================================================
    # API RESPONSE
    # =========================================================

    results = []

    for _, row in dataset.iterrows():

        similarity = (
            float(
                row["similarity"]
            )
            * 100
        )

        # Keep percentage between 0 and 100.
        similarity = max(
            0,
            min(
                100,
                similarity
            )
        )

        player_id = str(
            row["player_id"]
        )

        # -----------------------------------------------------
        # IMPORTANT:
        # player_aliases.csv is checked first.
        # people.csv is already used as fallback.
        # -----------------------------------------------------

        display_name = PLAYER_NAME_MAP.get(
            player_id,
            row["name"]
        )

        results.append({

            "player_id":
                player_id,

            "name":
                display_name,

            "similarity":
                round(
                    similarity,
                    2
                ),
        })

    return results