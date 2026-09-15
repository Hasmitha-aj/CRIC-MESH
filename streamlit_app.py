import streamlit as st

from backend.services.player_search import search_players
from backend.services.stats import calculate_stats
from backend.services.similarity import find_similar_players


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CricMesh",
    page_icon="🏏",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 0;
        }

        .subtitle {
            font-size: 18px;
            color: #666;
            margin-top: 0;
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 28px;
            font-weight: 700;
            margin-top: 30px;
            margin-bottom: 15px;
        }

        .similar-name {
            font-size: 20px;
            font-weight: 600;
        }

        .similar-score {
            font-size: 22px;
            font-weight: 700;
        }

        div.stButton > button {
            width: 100%;
            text-align: left;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "selected_player" not in st.session_state:
    st.session_state.selected_player = None

if "selected_format" not in st.session_state:
    st.session_state.selected_format = "test"


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🏏 CricMesh</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Cricket Player Intelligence & Similarity'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SEARCH
# =========================================================

st.markdown(
    '<div class="section-title">Search Player</div>',
    unsafe_allow_html=True
)

query = st.text_input(
    "Enter player name",
    placeholder="Try Virat Kohli, Kohli, V Kohli, Vir..."
)


# =========================================================
# SEARCH RESULTS
# =========================================================

if query.strip():

    try:
        search_results = search_players(query, 10)

    except Exception as e:
        st.error(f"Player search error: {e}")
        search_results = []

    if search_results:

        st.write("### Select a player")

        for player in search_results:

            display_name = player["name"]
            registered_name = player["registered_name"]

            if registered_name and registered_name != display_name:
                button_text = (
                    f"{display_name} "
                    f"({registered_name})"
                )
            else:
                button_text = display_name

            if st.button(
                button_text,
                key=f"player_{player['id']}"
            ):

                st.session_state.selected_player = player

                # Reset format when selecting a new player
                st.session_state.selected_format = "test"

                st.rerun()

    else:
        st.warning("No players found.")


# =========================================================
# PLAYER PROFILE
# =========================================================

player = st.session_state.selected_player


if player:

    player_id = player["id"]
    player_name = player["name"]

    st.divider()

    st.markdown(
        f"# {player_name}"
    )


    # =====================================================
    # FORMAT SELECTOR
    # =====================================================

    st.markdown(
        '<div class="section-title">Format</div>',
        unsafe_allow_html=True
    )

    format_options = ["TEST", "ODI", "T20I"]

    current_index = format_options.index(
        st.session_state.selected_format.upper()
    )

    format_choice = st.radio(
        "Select format",
        format_options,
        index=current_index,
        horizontal=True
    )

    selected_format = format_choice.lower()

    st.session_state.selected_format = selected_format


    # =====================================================
    # LOAD STATISTICS
    # =====================================================

    try:

        stats = calculate_stats(
            player_id,
            selected_format
        )

    except Exception as e:

        st.error(
            f"Could not load statistics: {e}"
        )

        stats = None


    if stats:

        # =================================================
        # BATTING
        # =================================================

        st.markdown(
            '<div class="section-title">'
            'Batting Statistics'
            '</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Matches",
            stats["matches"]
        )

        col2.metric(
            "Innings",
            stats["batting_innings"]
        )

        col3.metric(
            "Runs",
            stats["runs"]
        )

        col4.metric(
            "Average",
            stats["batting_average"]
        )


        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Strike Rate",
            stats["strike_rate"]
        )

        highest_score = str(
            stats["highest_score"]
        )

        if stats["highest_score_not_out"]:
            highest_score += "*"

        col2.metric(
            "Highest Score",
            highest_score
        )

        col3.metric(
            "50s",
            stats["fifties"]
        )

        col4.metric(
            "100s",
            stats["hundreds"]
        )


        col1, col2, col3 = st.columns(3)

        col1.metric(
            "4s",
            stats["fours"]
        )

        col2.metric(
            "6s",
            stats["sixes"]
        )

        col3.metric(
            "Not Outs",
            stats["not_outs"]
        )


        # =================================================
        # BOWLING
        # =================================================

        st.markdown(
            '<div class="section-title">'
            'Bowling Statistics'
            '</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Bowling Innings",
            stats["bowling_innings"]
        )

        col2.metric(
            "Overs",
            stats["overs"]
        )

        col3.metric(
            "Wickets",
            stats["wickets"]
        )

        col4.metric(
            "Bowling Average",
            stats["bowling_average"]
        )


        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Economy",
            stats["economy"]
        )

        col2.metric(
            "Bowling SR",
            stats["bowling_strike_rate"]
        )

        col3.metric(
            "4-Wicket Hauls",
            stats["four_wicket_hauls"]
        )

        col4.metric(
            "5-Wicket Hauls",
            stats["five_wicket_hauls"]
        )


        if stats["best_bowling_wickets"] > 0:

            best_bowling = (
                f"{stats['best_bowling_wickets']}/"
                f"{stats['best_bowling_runs']}"
            )

        else:

            best_bowling = "-"


        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Best Bowling",
            best_bowling
        )

        col2.metric(
            "Bowling Balls",
            stats["bowling_balls"]
        )

        col3.metric(
            "Runs Conceded",
            stats["runs_conceded"]
        )


        # =================================================
        # FIELDING
        # =================================================

        st.markdown(
            '<div class="section-title">'
            'Fielding Statistics'
            '</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Catches",
            stats["catches"]
        )

        col2.metric(
            "Run Outs",
            stats["run_outs"]
        )

        col3.metric(
            "Stumpings",
            stats["stumpings"]
        )


        # =================================================
        # SIMILAR PLAYERS
        # =================================================

        st.divider()

        st.markdown(
            '<div class="section-title">'
            'Similar Players'
            '</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Players with statistically similar performance "
            "according to the CricMesh ML similarity model."
        )


        try:

            # IMPORTANT:
            # Your find_similar_players function expects
            # the third argument positionally, not limit=5.

            similar_players = find_similar_players(
                player_id,
                selected_format,
                5
            )

        except Exception as e:

            st.error(
                f"Could not calculate similar players: {e}"
            )

            similar_players = []


        if similar_players:

            for similar in similar_players:

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    st.markdown(
                        f'<div class="similar-name">'
                        f'{similar["name"]}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with col2:

                    st.markdown(
                        f'<div class="similar-score">'
                        f'{similar["similarity"]}%'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                st.divider()

        else:

            st.info(
                "No similar players available for this format."
            )