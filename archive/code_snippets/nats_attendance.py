import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime


def join_year_url(i):
    # Join the year into the schedule url
    pre_url = 'https://www.baseball-reference.com/teams/WSN/'
    post_url = '-schedule-scores.shtml'
    return urllib.parse.urljoin(pre_url, "".join([str(i), post_url]))


# Inititialize blank dataframe
schedule_df_list = []
# Loop for year 2010-2018
for i in range(2010, 2018 + 1):
    # Define correct URL for year in range
    url = join_year_url(i)
    # Save get request as r
    r = requests.get(url)
    # Use beautifulsoup?
    soup = BeautifulSoup(r.text, "lxml")
    # Extract schedule table from HTML
    schedule = soup.find('div', attrs={'class': 'overthrow table_container'})
    # Create dataframe
    schedule_df = pd.read_html(str(schedule))[0]
    # Drop extra header rows embeded in dataframe
    schedule_df = schedule_df[schedule_df['Gm#'] != 'Gm#']
    # Remove parentheses and their contents from Date column
    # Split DOW from Date
    schedule_df['Date'] = schedule_df['Date'].str.split(", ").str[1]
    # Add the year to the dates in date
    schedule_df['Date'] = schedule_df['Date'].str.split("(").str[0].str.strip() + ", " + str(i)
    # Convert Date to date type
    schedule_df['Date'] = schedule_df['Date'].apply(lambda x: datetime.strptime(x, '%b %d, %Y'))
    # Append games from current iteration (season) to list
    schedule_df_list.append(schedule_df)


# Concat all the dataframe into one big schedule
nats_sched = pd.concat(schedule_df_list, axis=0)
nats_sched.rename(columns={'Unnamed: 2': 'BoxScore', 'Unnamed: 4': 'Home/Away'}, inplace=True)

# Keep only games played
nats_sched = nats_sched[nats_sched['BoxScore'] == 'boxscore']
nats_sched.to_csv("nats_sched.csv", sep='|')
print(nats_sched.dtypes)
