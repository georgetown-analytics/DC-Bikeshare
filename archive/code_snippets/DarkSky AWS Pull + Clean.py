import psycopg2
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import time

''' This script pulls and cleans all Dark Sky raw data from AWS.
    Not sure what blank and 0 columns are.
    In progress - need to create weather_time dummies using 'summary' column.
    Output = csv containing cleaned weather data (optional)
'''

env_path = Path('..') / '.env' 
load_dotenv(dotenv_path=env_path)

host = "capstone-bikeshare.cs9te7lm3pt2.us-east-1.rds.amazonaws.com"
port = 5432
database = "bikeshare"

user = os.environ.get("AWS_READONLY_USER")
password = os.environ.get("AWS_READONLY_PASS")

# Connect to aws postgres DB
conn = psycopg2.connect(host=host, user=user, port=port, password=password, database=database)
cur = conn.cursor()

# Query Dark Sky Raw
raw_df = pd.read_sql("""SELECT * FROM dark_sky_raw;""", con=conn)

### Cleaning and creating variables

# weather dummies
df = pd.concat([raw_df, pd.get_dummies(raw_df['preciptype'])], axis=1)
df.rename(columns = {'rain': 'rain_dummy', 'snow': 'snow_dummy'}, inplace = True)

# datetime
df['date'] = pd.to_datetime(df['weather_date'])
df['year'] = df['date'].dt.year 
df['month'] = df['date'].dt.month
df['weekday'] = df['date'].dt.weekday
df['weekday_name'] = df['date'].dt.weekday_name
df['quarter'] = df['date'].dt.quarter

# converting Unix time to human-readable time
timevars = ['apparenttemperaturehightime','apparenttemperaturelowtime','precipintensitymaxtime',
           'sunrisetime','sunsettime','temperaturehightime','temperaturelowtime', 'day_time']
for var in timevars:
    df[var] = pd.to_datetime(df[var],unit='s')
    
# deleting deprecated names
df.drop(['apparenttemperaturemax', 'apparenttemperaturemaxtime',
         'apparenttemperaturemin', 'apparenttemperaturemintime',
         'temperaturemax', 'temperaturemaxtime', 'temperaturemin',
         'temperaturemintime'], axis=1, inplace=True)

### output as csv
TIMESTR = time.strftime('%Y%m%d_%H%M%S')
filename = "DarkSky_Clean_" + TIMESTR + ".csv"
filepath = os.path.join("~/CaBi/", filename)
#df.to_csv(filepath, index=True)
