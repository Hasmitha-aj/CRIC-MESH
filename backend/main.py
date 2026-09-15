from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.services.player_search import search_players
from backend.services.stats import calculate_stats
from backend.services.similarity import find_similar_players


app = FastAPI(title="CricMesh API")


# ============================================================
# CORS
# Allows the frontend to communicate with the FastAPI backend
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "project": "CricMesh",
        "message": "CricMesh API is running!"
    }


# ============================================================
# PLAYER SEARCH
# ============================================================

@app.get("/players/search")
def player_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20)
):
    results = search_players(q, limit)

    return {
        "query": q,
        "count": len(results),
        "players": results
    }


# ============================================================
# PLAYER STATS
# ============================================================

@app.get("/players/{player_id}/stats/{format_name}")
def player_stats(
    player_id: str,
    format_name: str
):
    """
    Get player statistics for:

        test
        odi
        t20i
    """

    format_name = format_name.lower()

    if format_name not in {
        "test",
        "odi",
        "t20i"
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use test, odi, or t20i."
        )

    try:

        stats = calculate_stats(
            player_id,
            format_name
        )

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "player_id": player_id,
        "format": format_name.upper(),
        "stats": stats
    }


# ============================================================
# SIMILAR PLAYERS
# ============================================================

@app.get("/players/{player_id}/similar/{format_name}")
def similar_players(
    player_id: str,
    format_name: str,
    limit: int = Query(5, ge=1, le=10)
):
    """
    Get statistically similar players.

    Supported formats:

        test
        odi
        t20i
    """

    format_name = format_name.lower()

    if format_name not in {
        "test",
        "odi",
        "t20i"
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use test, odi, or t20i."
        )

    try:

        results = find_similar_players(
            player_id,
            format_name,
            limit
        )

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "player_id": player_id,
        "format": format_name.upper(),
        "similar_players": results
    }