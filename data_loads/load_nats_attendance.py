import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import util_functions as uf
import os


def join_year_url(i):
    # Join the year into the schedule url
    pre_url = 'https://www.baseball-reference.com/teams/WSN/'
    post_url = '-schedule-scores.shtml'
    return urllib.parse.urljoin(pre_url, "".join([str(i), post_url]))


def format_date_field(series):
    # Convert Date from field text to datetime
    # Split DOW from Date
    series = series.str.split(", ").str[1]
    # Add the year to the dates in date
    series = series.str.split("(").str[0].str.strip() + ", " + str(i)
    # Convert Date to date type
    series = series.apply(lambda x: datetime.strptime(x, '%b %d, %Y'))
    return series


def create_nats_attendance(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS nats_attendance;
    CREATE TABLE nats_attendance(
                Gm_Num integer,
                Date date,
                BoxScore varchar(20),
                Tm varchar(20),
                Home_Away varchar(20),
                Opp varchar(20),
                W_or_L varchar(20),
                R integer,
                RA integer,
                Inn integer,
                W_L_record varchar(20),
                Rank integer,
                GB varchar(20),
                Win varchar(50),
                Loss varchar(50),
                Save varchar(50),
                Time time,
                D_N varchar(20),
                Attendance integer,
                Streak varchar(20),
                Orig_Scheduled varchar(100)
        );
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Scrape Nationals SChedule Data
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
        # Format date field
        schedule_df['Date'] = format_date_field(schedule_df['Date'])
        # Append games from current iteration (season) to list
        schedule_df_list.append(schedule_df)
    # Concat all the dataframe into one big schedule
    nats_sched = pd.concat(schedule_df_list, axis=0)
    nats_sched.rename(columns={'Unnamed: 2': 'BoxScore', 'Unnamed: 4': 'Home_Away'}, inplace=True)
    # Keep only games played
    nats_sched = nats_sched[nats_sched['BoxScore'] == 'boxscore']
    # Fill in zeros for integer columns
    integer_columns = ['R', 'RA', 'Inn', 'Rank', 'Attendance']
    nats_sched[integer_columns] = nats_sched[integer_columns].fillna(value=0)

    # Output dataframe as CSV
    outname = "nats_attendance"
    nats_sched.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
    # Create Table in AWS
    create_nats_attendance(cur)
    # Load to Database
    uf.aws_load(outname, "nats_attendance", cur)
    # Commit changes to database
    conn.commit()
