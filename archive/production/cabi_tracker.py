import requests
import pandas as pd
import io
from datetime import date, timedelta
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import zipfile

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

drive = GoogleDrive(gauth)


def pull_daily_data(date):
    ''' pulls a date of outage data from Cabi Tracker'''
    params = {'s': date,
              'e': date}
    CaBiTrackerURl = "http://cabitracker.com/downloadoutage.php"
    urlData = requests.get(CaBiTrackerURl, params=params).content
    rawData = pd.read_csv(io.StringIO(urlData.decode('utf-8')))
    return rawData


d1 = date(2011, 5, 1)  # start date
d2 = date(2018, 2, 28)  # end date
delta = d2 - d1         # timedelta


df_list = []
for i in range(delta.days + 1):
    date = (d1 + timedelta(days=i))
    date_df = pull_daily_data(date)
    df_list.append(date_df)
    print("{} processed".format(date))

# Combine and Keep only "empty" and "full" statuses
combined_df = pd.concat(df_list, axis=0)
combined_df = combined_df[combined_df['Status'].isin(['empty', 'full'])].drop('Station Name')

# Output dataframe as CSV
outname = "CaBi_Tracker_Outage_History_From_" + d1.strftime('%Y-%m-%d') + "_To_" + d2.strftime('%Y-%m-%d')
combined_df.to_csv(outname + ".csv", index=False)

# Add CSV to zip
compression = zipfile.ZIP_DEFLATED
zf = zipfile.ZipFile(outname + ".zip", mode='w')
zf.write(outname + ".csv", compress_type=compression)
zf.close()

# Upload CSV to Google Drive
data_folder = '175Zhy6KRdgOwVhwqeZPANHCv6GvJJfvv'

file1 = drive.CreateFile({'title': outname + ".zip",
                          "parents": [{"kind": "drive#fileLink", "id": data_folder}]})
file1.SetContentFile(outname + ".zip")  # Set content of the file from given string.
file1.Upload()
