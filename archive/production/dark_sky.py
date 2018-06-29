import datetime
import pandas as pd
import forecastio
import time
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import zipfile
import math

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

drive = GoogleDrive(gauth)


def daily_weather(api_key, d):
    ''' Pull historical daily weather from Dark Sky API'''

    # DC latitude and longitude coordinate
    lat = 38.9072
    lng = -77.0369

    # Pull Daily forcast from Dark Sky API
    forecast = forecastio.load_forecast(api_key, lat, lng, time=d)
    daily = forecast.daily()

    # Convert daily data dictionary to dataframe
    daily_data = daily.data[0].d
    daily_data_df = pd.DataFrame(daily_data, index=[d])
    return daily_data_df


# Define Range of Date to pull forecast and turn into a list
start_date = datetime.datetime(2010, 10, 1)
end_date = datetime.datetime(2018, 2, 28)
delta = end_date - start_date
date_list = [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]

# List of APIs to loop through, 1000 calls per API
api_key_list_id = '1GBquCFcLRWKiVhsYxisyI-ahVDTbPPTQ'
api_key_list_file = drive.CreateFile({'id': api_key_list_id})
content = api_key_list_file.GetContentFile(api_key_list_file['title'])

api_key_list = open('Dark_Sky_API.csv').read().splitlines()

# Duplicate api_key_list to match the number of items in the Date Range
api_key_list_exp = api_key_list * math.floor(len(date_list) / len(api_key_list))

# Turn date and api key lists into dictionary
date_dict = dict(zip(date_list, api_key_list_exp))

# Loop through dates and pull weather data
results = []
for d, api_key in date_dict.items():
    # get daily weather attributes
    row_df = daily_weather(api_key, d)
    results.append(row_df)
    print('{} has been processed'.format(d))

# Concatentate one big dataframe
results_df = pd.concat(results, axis=0)

# Output final dataframe
TIMESTR = time.strftime("%Y%m%d_%H%M%S")
outname = "Dark_Sky_From_" + start_date.strftime('%Y-%m-%d') + "_To_" + end_date.strftime('%Y-%m-%d')
results_df.to_csv(outname + ".csv", index=True)

# Add CSV to zip
compression = zipfile.ZIP_DEFLATED
zf = zipfile.ZipFile(outname + ".zip", mode='w')
zf.write(outname + ".csv", compress_type=compression)
zf.close()


# Google Drive folder id
data_folder = '1aDd5fcdbxJfPUDN0i7thmWcUqx8PRmPv'

file1 = drive.CreateFile({'title': outname + ".zip",
                          "parents": [{"kind": "drive#fileLink", "id": data_folder}]})
file1.SetContentFile(outname + ".zip")  # Set content of the file from given string.
file1.Upload()
