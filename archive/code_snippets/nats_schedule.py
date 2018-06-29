import datetime
import mlbgame
import sys

years = [year for year in range(2010, 2018 + 1)]
print(years)
sys.exit()
schedule = mlbgame.games(years, 3, home='Nationals')
games = mlbgame.combine_games(schedule)
for game in games:
    game_date = game.date
    game_overview = mlbgame.overview(game.game_id)
    game_location = game_overview.location
    # Game Attendance
    print(game_date, game_location)
