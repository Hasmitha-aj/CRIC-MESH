const API_URL = "http://127.0.0.1:8000";

const searchInput = document.getElementById("playerSearch");
const searchButton = document.getElementById("searchButton");
const suggestions = document.getElementById("suggestions");

const playerResult = document.getElementById("playerResult");
const playerName = document.getElementById("playerName");
const playerRegisteredName =
    document.getElementById("playerRegisteredName");

const statsContainer = document.getElementById("stats");
const loading = document.getElementById("loading");

// Similar players elements
const similarPlayersContainer =
    document.getElementById("similarPlayers");

let selectedPlayer = null;

// Keeps track of the newest statistics request.
// This prevents an older request from overwriting
// the statistics of the format currently selected.
let statsRequestNumber = 0;

// Keeps track of the newest similarity request.
// This prevents an older similarity response from
// overwriting the latest selected format.
let similarityRequestNumber = 0;


// --------------------------------------------------
// Search players
// --------------------------------------------------

async function searchPlayers() {

    const query = searchInput.value.trim();

    if (!query) {

        suggestions.innerHTML = "";

        return;
    }

    try {

        const response = await fetch(
            `${API_URL}/players/search?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {

            throw new Error("Search failed");

        }

        const data = await response.json();

        displaySuggestions(data.players);

    } catch (error) {

        console.error(error);

        suggestions.innerHTML =
            "<div class='suggestion'>Unable to connect to API</div>";
    }
}


// --------------------------------------------------
// Display autocomplete suggestions
// --------------------------------------------------

function displaySuggestions(players) {

    suggestions.innerHTML = "";

    if (!players || players.length === 0) {

        suggestions.innerHTML =
            "<div class='suggestion'>No players found</div>";

        return;
    }

    players.forEach(player => {

        const item = document.createElement("div");

        item.className = "suggestion";

        item.innerHTML = `
            <div class="suggestion-name">
                ${player.name}
            </div>

            <div class="suggestion-registered">
                ${player.registered_name}
            </div>
        `;

        item.addEventListener("click", () => {

            selectPlayer(player);

        });

        suggestions.appendChild(item);

    });
}


// --------------------------------------------------
// Select player
// --------------------------------------------------

function selectPlayer(player) {

    selectedPlayer = player;

    searchInput.value = player.name;

    suggestions.innerHTML = "";

    playerResult.classList.remove("hidden");

    playerName.textContent = player.name;

    playerRegisteredName.textContent =
        `Registered name: ${player.registered_name}`;

    // When selecting a new player,
    // always start with Test format.
    document
        .querySelectorAll(".format-button")
        .forEach(button => {

            button.classList.remove("active");

            if (button.dataset.format === "test") {
                button.classList.add("active");
            }

        });

    // Load Test statistics
    loadStats(
        player.id,
        "test"
    );

    // Load Test similar players
    loadSimilarPlayers(
        player.id,
        "test"
    );
}


// --------------------------------------------------
// Load player statistics
// --------------------------------------------------

async function loadStats(playerId, format) {

    // Create a unique number for this request.
    // Only the newest request is allowed to update
    // the statistics on the page.
    const requestNumber = ++statsRequestNumber;

    loading.classList.remove("hidden");

    statsContainer.innerHTML = "";

    try {

        const response = await fetch(
            `${API_URL}/players/${playerId}/stats/${format}`
        );

        if (!response.ok) {

            throw new Error("Could not load statistics");

        }

        const data = await response.json();

        // If another format was selected while this
        // request was running, ignore this old response.
        if (requestNumber !== statsRequestNumber) {

            return;

        }

        displayStats(data.stats);

    } catch (error) {

        // Do not show an error from an old request.
        if (requestNumber !== statsRequestNumber) {

            return;

        }

        console.error(error);

        statsContainer.innerHTML = `
            <div class="stat-card">
                Unable to load statistics.
            </div>
        `;

    } finally {

        // Only hide loading for the latest request.
        if (requestNumber === statsRequestNumber) {

            loading.classList.add("hidden");

        }

    }
}


// --------------------------------------------------
// Display statistics
// --------------------------------------------------

function displayStats(stats) {

    const statList = [

        ["Matches", stats.matches],

        ["Batting Innings", stats.batting_innings],

        ["Runs", stats.runs],

        ["Balls Faced", stats.balls_faced],

        ["Batting Average", stats.batting_average],

        ["Strike Rate", stats.strike_rate],

        [
            "Highest Score",
            stats.highest_score +
            (stats.highest_score_not_out ? "*" : "")
        ],

        ["50s", stats.fifties],

        ["100s", stats.hundreds],

        ["Fours", stats.fours],

        ["Sixes", stats.sixes],

        ["Not Outs", stats.not_outs],

        ["Bowling Innings", stats.bowling_innings],

        ["Overs", stats.overs],

        ["Runs Conceded", stats.runs_conceded],

        ["Wickets", stats.wickets],

        ["Bowling Average", stats.bowling_average],

        ["Economy", stats.economy],

        [
            "Bowling Strike Rate",
            stats.bowling_strike_rate
        ],

        [
            "4 Wicket Hauls",
            stats.four_wicket_hauls
        ],

        [
            "5 Wicket Hauls",
            stats.five_wicket_hauls
        ],

        [
            "Best Bowling",
            stats.best_bowling_wickets > 0
                ? `${stats.best_bowling_wickets}/${stats.best_bowling_runs}`
                : "-"
        ],

        ["Catches", stats.catches],

        ["Run Outs", stats.run_outs],

        ["Stumpings", stats.stumpings]

    ];


    statList.forEach(([title, value]) => {

        const card = document.createElement("div");

        card.className = "stat-card";

        card.innerHTML = `
            <div class="stat-title">
                ${title}
            </div>

            <div class="stat-value">
                ${value}
            </div>
        `;

        statsContainer.appendChild(card);

    });
}


// --------------------------------------------------
// Load similar players
// --------------------------------------------------

async function loadSimilarPlayers(playerId, format) {

    // Create a unique request number.
    // This prevents an older similarity response
    // from replacing the latest selected format.
    const requestNumber = ++similarityRequestNumber;

    if (!similarPlayersContainer) {

        return;

    }

    similarPlayersContainer.innerHTML = `
        <div class="similar-loading">
            Finding similar players...
        </div>
    `;

    try {

        const response = await fetch(
            `${API_URL}/players/${playerId}/similar/${format}`
        );

        if (!response.ok) {

            throw new Error(
                "Could not load similar players"
            );

        }

        const data = await response.json();

        // Ignore old responses.
        if (requestNumber !== similarityRequestNumber) {

            return;

        }

        displaySimilarPlayers(
            data.similar_players
        );

    } catch (error) {

        // Ignore errors from old requests.
        if (requestNumber !== similarityRequestNumber) {

            return;

        }

        console.error(error);

        similarPlayersContainer.innerHTML = `
            <div class="similar-error">
                Unable to load similar players.
            </div>
        `;
    }
}


// --------------------------------------------------
// Display similar players
// --------------------------------------------------

function displaySimilarPlayers(players) {

    similarPlayersContainer.innerHTML = "";

    if (!players || players.length === 0) {

        similarPlayersContainer.innerHTML = `
            <div class="similar-error">
                No similar players found.
            </div>
        `;

        return;
    }

    players.forEach((player, index) => {

        const card = document.createElement("div");

        card.className = "similar-player-card";

        card.innerHTML = `
            <div class="similar-rank">
                #${index + 1}
            </div>

            <div class="similar-player-info">

                <div class="similar-player-name">
                    ${player.name}
                </div>

                <div class="similar-score">
                    ${player.similarity}%
                    similarity
                </div>

            </div>
        `;


        // ------------------------------------------
        // Click similar player
        // ------------------------------------------

        card.addEventListener("click", () => {

            const newPlayer = {

                id: player.player_id,

                name: player.name,

                registered_name: player.name

            };


            // Make this player the new selected player.
            selectPlayer(newPlayer);


            // Scroll to the player profile.
            playerResult.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });


        similarPlayersContainer.appendChild(card);

    });
}


// --------------------------------------------------
// Search button
// --------------------------------------------------

searchButton.addEventListener(
    "click",
    async () => {

        await searchPlayers();

    }
);


// --------------------------------------------------
// Search while typing
// --------------------------------------------------

let searchTimeout;

searchInput.addEventListener(
    "input",
    () => {

        clearTimeout(searchTimeout);

        searchTimeout = setTimeout(
            searchPlayers,
            250
        );

    }
);


// --------------------------------------------------
// Enter key
// --------------------------------------------------

searchInput.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {

            event.preventDefault();

            searchPlayers();

        }

    }
);


// --------------------------------------------------
// Test / ODI / T20I buttons
// --------------------------------------------------

document
    .querySelectorAll(".format-button")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                if (!selectedPlayer) {

                    return;

                }

                // Remove active state from every button.
                document
                    .querySelectorAll(".format-button")
                    .forEach(btn => {

                        btn.classList.remove("active");

                    });


                // Activate the button clicked by the user.
                button.classList.add("active");


                const format =
                    button.dataset.format;


                // Load statistics for the
                // selected format.
                loadStats(
                    selectedPlayer.id,
                    format
                );


                // Load similar players for the
                // selected format.
                loadSimilarPlayers(
                    selectedPlayer.id,
                    format
                );

            }
        );

    });