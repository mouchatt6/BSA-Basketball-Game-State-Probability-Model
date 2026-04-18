List of the data we would like for the win probability model.
    
Note: Current idea is to train on 2021-22 - 2024-25 and evaluate on 2025-26

List:
    - Play by play data for 2021-22 - 2025-26
        Status: Have data for 2024-25 and a working script to pull more data.

    - Game-by-game team stats so we can create some time-dependent features such as a team's offensive rating, defensive rating, etc. We want these to not be calculated for an entire season, but only up to that point in the season. Perhaps we could use a moving weighted average over prior games.

    - Lineup data to easily determine starting lineups and track the players on the court (later)