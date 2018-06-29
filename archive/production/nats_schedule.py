import datetime
import mlbgame
import time
import pandas as pd
import os

# Define Years of Interest (2010-2018)
years = [year for year in range(2010, 2018 + 1)]

# Pull all games from MLBGAME API
schedule = mlbgame.games(years, home='Nationals')
games = mlbgame.combine_games(schedule)

results = []
# Loop through games and keep regular season games played in DC
for game in games:
    game_datetime = game.date
    game_date = game_datetime.date()
    game_overview = mlbgame.overview(game.game_id)
    # Game Type, should be == 'R' for regular season
    game_type = game_overview.game_type
    if (game_type != 'S'):
        print(game_date)
        game_df = pd.DataFrame({'natls_home': 1}, index=[game_date])
        results.append(game_df)

# Concatentate one big dataframe
results_df = pd.concat(results, axis=0)

# Output final dataframe
TIMESTR = time.strftime("%Y%m%d_%H%M%S")
filename = "Natls_Home_Games_2010_2018_" + TIMESTR + ".csv"
filepath = os.path.join("./Output", filename)
results_df.to_csv(filepath, index=True)
