// ==================================================
// CricMesh - Static GitHub Pages Version
// ==================================================

// Static data files generated from Cricsheet.
const DATA_PATH = "./data";

let playersData = [];
let statsData = {
    test: {},
    odi: {},
    t20i: {}
};

let similarData = {
    test: {},
    odi: {},
    t20i: {}
};


// ==================================================
// DOM elements
// ==================================================

const searchInput =
    document.getElementById("playerSearch");

const searchButton =
    document.getElementById("searchButton");

const suggestions =
    document.getElementById("suggestions");

const playerResult =
    document.getElementById("playerResult");

const playerName =
    document.getElementById("playerName");

const playerRegisteredName =
    document.getElementById("playerRegisteredName");

const statsContainer =
    document.getElementById("stats");

const loading =
    document.getElementById("loading");

const similarPlayersContainer =
    document.getElementById("similarPlayers");

let selectedPlayer = null;

let statsRequestNumber = 0;
let similarityRequestNumber = 0;


// ==================================================
// Normalize text
// ==================================================

function normalize(text) {
    return String(text || "")
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}


// ==================================================
// Load all static data
// ==================================================

async function loadAllData() {

    try {

        const [
            playersResponse,
            testStatsResponse,
            odiStatsResponse,
            t20iStatsResponse,
            testSimilarResponse,
            odiSimilarResponse,
            t20iSimilarResponse
        ] = await Promise.all([

            fetch(`${DATA_PATH}/players.json`),

            fetch(`${DATA_PATH}/stats_test.json`),

            fetch(`${DATA_PATH}/stats_odi.json`),

            fetch(`${DATA_PATH}/stats_t20i.json`),

            fetch(`${DATA_PATH}/similar_test.json`),

            fetch(`${DATA_PATH}/similar_odi.json`),

            fetch(`${DATA_PATH}/similar_t20i.json`)
        ]);


        if (
            !playersResponse.ok ||
            !testStatsResponse.ok ||
            !odiStatsResponse.ok ||
            !t20iStatsResponse.ok ||
            !testSimilarResponse.ok ||
            !odiSimilarResponse.ok ||
            !t20iSimilarResponse.ok
        ) {
            throw new Error(
                "One or more data files could not be loaded."
            );
        }


        playersData =
            await playersResponse.json();

        statsData.test =
            await testStatsResponse.json();

        statsData.odi =
            await odiStatsResponse.json();

        statsData.t20i =
            await t20iStatsResponse.json();

        similarData.test =
            await testSimilarResponse.json();

        similarData.odi =
            await odiSimilarResponse.json();

        similarData.t20i =
            await t20iSimilarResponse.json();


        console.log(
            "CricMesh static data loaded successfully."
        );

        console.log(
            `Players: ${playersData.length}`
        );


    } catch (error) {

        console.error(
            "Failed to load CricMesh data:",
            error
        );

        suggestions.innerHTML = `
            <div class="suggestion">
                Unable to load CricMesh data.
            </div>
        `;
    }
}


// ==================================================
// Search score
// ==================================================

function getMatchScore(query, candidate) {

    if (!candidate) {
        return 0;
    }

    if (candidate === query) {
        return 10000;
    }


    const words =
        candidate.split(" ");


    // Exact word match.
    if (words.includes(query)) {

        if (query.length === 1) {
            return 5000;
        }

        return 8000 + Math.min(
            candidate.length,
            100
        );
    }


    // Candidate starts with query.
    if (candidate.startsWith(query)) {

        if (query.length > 1) {
            return 7500 + Math.min(
                candidate.length,
                100
            );
        }

        return 5000;
    }


    // Any word starts with query.
    for (const word of words) {

        if (word.startsWith(query)) {

            if (word.length > 1) {
                return 7000 + Math.min(
                    word.length,
                    100
                );
            }
        }
    }


    // Query occurs somewhere inside candidate.
    if (candidate.includes(query)) {
        return 3000;
    }


    return 0;
}


// ==================================================
// Search players
// ==================================================

function searchPlayers() {

    const query =
        normalize(searchInput.value);


    if (!query) {

        suggestions.innerHTML = "";

        return;
    }


    const results = [];


    for (const player of playersData) {

        const searchableNames = [

            player.name,

            player.registered_name,

            player.unique_name,

            ...(player.aliases || [])

        ]
        .map(normalize)
        .filter(Boolean);


        let bestScore = 0;
        let bestMatch = "";


        for (const candidate of searchableNames) {

            const score =
                getMatchScore(
                    query,
                    candidate
                );


            if (score > bestScore) {

                bestScore = score;

                bestMatch = candidate;
            }
        }


        if (bestScore > 0) {

            results.push({

                ...player,

                match_score: bestScore,

                matched_as: bestMatch

            });
        }
    }


    results.sort(
        (a, b) => {

            if (
                b.match_score !==
                a.match_score
            ) {
                return (
                    b.match_score -
                    a.match_score
                );
            }

            return a.name.localeCompare(
                b.name
            );
        }
    );


    displaySuggestions(
        results.slice(0, 10)
    );
}


// ==================================================
// Display autocomplete suggestions
// ==================================================

function displaySuggestions(players) {

    suggestions.innerHTML = "";


    if (
        !players ||
        players.length === 0
    ) {

        suggestions.innerHTML =
            "<div class='suggestion'>No players found</div>";

        return;
    }


    players.forEach(player => {

        const item =
            document.createElement("div");

        item.className =
            "suggestion";


        item.innerHTML = `

            <div class="suggestion-name">
                ${player.name}
            </div>

            <div class="suggestion-registered">
                ${player.registered_name || ""}
            </div>

        `;


        item.addEventListener(
            "click",
            () => {

                selectPlayer(player);

            }
        );


        suggestions.appendChild(item);

    });
}


// ==================================================
// Select player
// ==================================================

function selectPlayer(player) {

    selectedPlayer = player;


    searchInput.value =
        player.name;


    suggestions.innerHTML =
        "";


    playerResult.classList.remove(
        "hidden"
    );


    playerName.textContent =
        player.name;


    playerRegisteredName.textContent =
        `Registered name: ${player.registered_name || player.name}`;


    // Reset format buttons to Test.
    document
        .querySelectorAll(".format-button")
        .forEach(button => {

            button.classList.remove(
                "active"
            );


            if (
                button.dataset.format ===
                "test"
            ) {

                button.classList.add(
                    "active"
                );
            }

        });


    loadStats(
        player.id,
        "test"
    );


    loadSimilarPlayers(
        player.id,
        "test"
    );
}


// ==================================================
// Load player statistics
// ==================================================

function loadStats(
    playerId,
    format
) {

    const requestNumber =
        ++statsRequestNumber;


    loading.classList.remove(
        "hidden"
    );


    statsContainer.innerHTML =
        "";


    try {

        const formatStats =
            statsData[format];


        const stats =
            formatStats[playerId];


        if (!stats) {

            throw new Error(
                "Statistics not found."
            );
        }


        if (
            requestNumber !==
            statsRequestNumber
        ) {
            return;
        }


        displayStats(stats);


    } catch (error) {

        if (
            requestNumber !==
            statsRequestNumber
        ) {
            return;
        }


        console.error(error);


        statsContainer.innerHTML = `

            <div class="stat-card">
                Unable to load statistics.
            </div>

        `;

    } finally {

        if (
            requestNumber ===
            statsRequestNumber
        ) {

            loading.classList.add(
                "hidden"
            );
        }
    }
}


// ==================================================
// Display statistics
// ==================================================

function displayStats(stats) {

    const statList = [

        ["Matches", stats.matches],

        ["Batting Innings",
            stats.batting_innings],

        ["Runs", stats.runs],

        ["Balls Faced",
            stats.balls_faced],

        ["Batting Average",
            stats.batting_average],

        ["Strike Rate",
            stats.strike_rate],

        [
            "Highest Score",
            stats.highest_score +
            (
                stats.highest_score_not_out
                    ? "*"
                    : ""
            )
        ],

        ["50s", stats.fifties],

        ["100s", stats.hundreds],

        ["Fours", stats.fours],

        ["Sixes", stats.sixes],

        ["Not Outs", stats.not_outs],

        ["Bowling Innings",
            stats.bowling_innings],

        ["Overs", stats.overs],

        ["Runs Conceded",
            stats.runs_conceded],

        ["Wickets", stats.wickets],

        ["Bowling Average",
            stats.bowling_average],

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


    statList.forEach(
        ([title, value]) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "stat-card";


            card.innerHTML = `

                <div class="stat-title">
                    ${title}
                </div>

                <div class="stat-value">
                    ${value ?? 0}
                </div>

            `;


            statsContainer.appendChild(
                card
            );

        }
    );
}


// ==================================================
// Load similar players
// ==================================================

function loadSimilarPlayers(
    playerId,
    format
) {

    const requestNumber =
        ++similarityRequestNumber;


    if (!similarPlayersContainer) {
        return;
    }


    similarPlayersContainer.innerHTML = `

        <div class="similar-loading">
            Finding similar players...
        </div>

    `;


    try {

        const formatSimilar =
            similarData[format];


        const players =
            formatSimilar[playerId] || [];


        if (
            requestNumber !==
            similarityRequestNumber
        ) {
            return;
        }


        displaySimilarPlayers(
            players
        );


    } catch (error) {

        if (
            requestNumber !==
            similarityRequestNumber
        ) {
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


// ==================================================
// Display similar players
// ==================================================

function displaySimilarPlayers(
    players
) {

    similarPlayersContainer.innerHTML =
        "";


    if (
        !players ||
        players.length === 0
    ) {

        similarPlayersContainer.innerHTML = `

            <div class="similar-error">
                No similar players found.
            </div>

        `;

        return;
    }


    players.forEach(
        (player, index) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "similar-player-card";


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


            card.addEventListener(
                "click",
                () => {

                    const playerFromIndex =
                        playersData.find(
                            item =>
                                item.id ===
                                player.player_id
                        );


                    if (playerFromIndex) {

                        selectPlayer(
                            playerFromIndex
                        );

                    } else {

                        selectPlayer({

                            id:
                                player.player_id,

                            name:
                                player.name,

                            registered_name:
                                player.name,

                            unique_name:
                                player.name,

                            aliases: []

                        });

                    }


                    playerResult.scrollIntoView({

                        behavior: "smooth",

                        block: "start"

                    });

                }
            );


            similarPlayersContainer.appendChild(
                card
            );

        }
    );
}


// ==================================================
// Search button
// ==================================================

searchButton.addEventListener(
    "click",
    () => {

        searchPlayers();

    }
);


// ==================================================
// Search while typing
// ==================================================

let searchTimeout;


searchInput.addEventListener(
    "input",
    () => {

        clearTimeout(
            searchTimeout
        );


        searchTimeout =
            setTimeout(
                searchPlayers,
                150
            );

    }
);


// ==================================================
// Enter key
// ==================================================

searchInput.addEventListener(
    "keydown",
    event => {

        if (
            event.key ===
            "Enter"
        ) {

            event.preventDefault();

            searchPlayers();

        }

    }
);


// ==================================================
// Test / ODI / T20I buttons
// ==================================================

document
    .querySelectorAll(".format-button")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                if (!selectedPlayer) {
                    return;
                }


                document
                    .querySelectorAll(
                        ".format-button"
                    )
                    .forEach(btn => {

                        btn.classList.remove(
                            "active"
                        );

                    });


                button.classList.add(
                    "active"
                );


                const format =
                    button.dataset.format;


                loadStats(
                    selectedPlayer.id,
                    format
                );


                loadSimilarPlayers(
                    selectedPlayer.id,
                    format
                );

            }
        );

    });


// ==================================================
// Start CricMesh
// ==================================================

loadAllData();