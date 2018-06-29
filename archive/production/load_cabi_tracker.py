import requests
import pandas as pd
import numpy as np
import io
from datetime import date, timedelta
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import zipfile

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

drive = GoogleDrive(gauth)


# Download all CaBi Tracker files from our Google Drive
data_folder = '175Zhy6KRdgOwVhwqeZPANHCv6GvJJfvv'
query = "'{}' in parents and trashed=false".format(data_folder)
file_list = drive.ListFile({'q': query}).GetList()
for file_obj in file_list:
    file_create = drive.CreateFile({'id': file_obj['id']})
    file_content = file_create.GetContentFile(file_obj['title'])
    print("{} has been downloaded".format(file_obj['title']))
    # TODO: Unzip all files and load into dataframe
    if ".zip" in file_obj['title']:
        zf = zipfile.ZipFile(file_obj['title'])
        # Assume that there is only one file per zip and has same name, load as dataframe
        dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
        # Ensure that datatime fields are datetime, not strings
        data_df = pd.read_csv(file_obj['title'], sep=',', quotechar='"', parse_dates=['Start', 'End'], date_parser=dateparse)
        # Calculate duration as a float
        data_df['duration_calc'] = ((data_df['End'] - data_df['Start']) / np.timedelta64(1, 'm')).astype(float)
        print(data_df.head())
        print(data_df.describe())
        print(data_df.dtypes)


import sys
sys.exit()