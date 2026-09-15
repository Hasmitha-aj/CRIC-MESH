from backend.services.stats import calculate_stats


player_id = "ba607b88"  # Virat Kohli


stats = calculate_stats(
    player_id,
    "odi"
)


print("\n==============================")
print("       CRICMESH ODI STATS")
print("==============================")


print("\n--- BATTING ---")
print("Matches:", stats["matches"])
print("Innings:", stats["batting_innings"])
print("Runs:", stats["runs"])
print("Balls:", stats["balls_faced"])
print("Average:", stats["batting_average"])
print("Strike Rate:", stats["strike_rate"])
print("50s:", stats["fifties"])
print("100s:", stats["hundreds"])
print("Highest Score:", stats["highest_score"])
print("4s:", stats["fours"])
print("6s:", stats["sixes"])


print("\n--- BOWLING ---")
print("Bowling Innings:", stats["bowling_innings"])
print("Overs:", stats["overs"])
print("Runs Conceded:", stats["runs_conceded"])
print("Wickets:", stats["wickets"])
print("Average:", stats["bowling_average"])
print("Economy:", stats["economy"])
print("Strike Rate:", stats["bowling_strike_rate"])
print("4 Wicket Hauls:", stats["four_wicket_hauls"])
print("5 Wicket Hauls:", stats["five_wicket_hauls"])

print(
    "Best Bowling:",
    f'{stats["best_bowling_wickets"]}/'
    f'{stats["best_bowling_runs"]}'
)


print("\n--- FIELDING ---")
print("Catches:", stats["catches"])
print("Run Outs:", stats["run_outs"])
print("Stumpings:", stats["stumpings"])


print("\n==============================")