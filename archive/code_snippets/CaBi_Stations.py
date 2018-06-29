import pandas as pd
import requests
import numpy as np
import time
import os

# Load station information
station_url = "https://gbfs.capitalbikeshare.com/gbfs/en/station_information.json"
stations = requests.get(station_url).json()
station_df = pd.DataFrame(stations['data']['stations'])
station_df = station_df[['lat', 'lon', 'region_id', 'short_name']].copy()
# Default any missing region ids to DC (only example as of 2/21 is new station at Anacostia Park)
station_df['region_id'] = np.where(
    station_df['region_id'].isnull(), 42, station_df['region_id'])

# Convert region_id to str from float
station_df['region_id'] = station_df['region_id'].astype(int).astype(str)

# Load region information
region_url = "https://gbfs.capitalbikeshare.com/gbfs/en/system_regions.json"
regions = requests.get(region_url).json()
regions_df = pd.DataFrame(regions['data']['regions'])

# Merge region information onto stations
station_df = station_df.merge(
    regions_df, left_on='region_id', right_on='region_id', how='left')
station_df.rename(index=str, columns={'name': 'region_name'}, inplace=True)
print(len(station_df))
print(station_df['region_name'].value_counts())

# Define Abbreviations for each region

region_code = {'Washington, DC': 'WDC',
               'Arlington, VA': 'ARL',
               'Montgomery County, MD (South)': 'MCS',
               'Montgomery County, MD (North)': 'MCN',
               'Alexandria, VA': 'ALX',
               'Fairfax, VA': 'FFX'}

region_code_series = pd.Series(region_code, name='region_code')
region_code_series.index.name = 'region_name'
region_code_df = region_code_series.reset_index()
station_df = station_df.merge(
    region_code_df, left_on='region_name', right_on='region_name', how='left')
station_df.drop(['region_name', 'region_id'], inplace=True, axis=1)

# Output DataFrame as CSV with timestamp
TIMESTR = time.strftime("%Y%m%d_%H%M%S")
filename = "CABI_Station_Info_" + TIMESTR + ".csv"
filepath = os.path.join("./Output", filename)
station_df.to_csv(filepath, index=False)
