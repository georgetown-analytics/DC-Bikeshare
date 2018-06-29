import pandas as pd
import os
import util_functions as uf
from splinter import Browser
import urllib.request
import shutil
import zipfile


def get_links():
    browser = Browser('firefox')
    browser.visit('https://s3.amazonaws.com/capitalbikeshare-data/index.html')

    links = browser.find_by_css('#tbody-content a')
    #links = [link for link in links if link['href']]
    zip_links = []
    for link in links:
        link_text = link['href']
        with urllib.request.urlopen(link_text) as response:
            subtype = response.info().get_content_subtype()
            if subtype == 'zip':
                zip_links.append(link_text)

    return zip_links


def download_links(links):
    download_dir = '../cabi_trip_data'
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    for link in links:
        file_name = os.path.join(download_dir, link.split('/')[-1])
        print(file_name)
        # save file to disk
        with urllib.request.urlopen(link) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall(download_dir)


def trips_to_df(cabi_trip_dir):
    # Loop through CSVs of Trip Data
    trip_df_list = []
    for csv in sorted(os.listdir(cabi_trip_dir)):
        csv_name = csv.replace('.csv', '')
        print("{} has started processing".format(csv_name))
        # Load original CSV as dataframe
        trip_df = pd.read_csv(os.path.join(cabi_trip_dir, csv_name + '.csv')).drop(['Start station', 'End station'], axis=1)
        trip_df.columns = ['duration', 'start_date', 'end_date', 'start_station', 'end_station', 'bike_number', 'member_type']
    combined_df = pd.concat(trip_df_list, axis=0)
    return combined_df


def create_cabi_trips(cur):
    # This script creates the CaBi System AWS table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cabi_trips(
        duration integer,
        start_date timestamp,
        end_date timestamp,
        start_station varchar(20),
        end_station varchar(20),
        bike_number varchar(30),
        member_type varchar(20)
    )
            """)


if __name__ == "__main__":
    # Pull CaBi Trips Data from AWS S3 Store
    links = get_links()
    download_links(links)
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Loop through all CSVs in cabi trip data folder
    cabi_trip_dir = '../cabi_trip_data'
    # Convert trip data from CSV to dataframe
    combined_df = trips_to_df(cabi_trip_dir)
    # Add trip_id continuing from last record in AWS table
    trip_id_df = pd.read_sql("""SELECT trip_id from cabi_trips order by outage_id desc LIMIT 1 """, con=conn)
    last_trip_id = trip_id_df['trip_id'].iloc[0]
    combined_df.reset_index(inplace=True)
    combined_df['trip_id'] = combined_df.index + 1 + last_trip_id
    # Drop unneeded fields
    combined_df.drop(['index'], axis=1, inplace=True)
    # Output dataframe as CSV
    outname = "CaBi_Trip_Data"
    combined_df.to_csv(outname + ".csv", index=False, sep='|')
    # Create Table
    create_cabi_trips(cur)
    # Load to Database
    uf.aws_load(outname, "cabi_trips", cur)
    # Commit changes to database
    conn.commit()
