from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pandas as pd
import time
import os
import numpy as np
import util_functions as uf


def gcal_authorization():
    # Authorize access to personal Google Calendar
    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store, flags) \
            if flags else tools.run(flow, store)
    CAL = build('calendar', 'v3', http=creds.authorize(Http()))
    return CAL


def pull_waba_events(CAL):
    # Pull all Events from the WABA Calendar
    calendarID = 'waba.org_ig71a8ro5egochvtt5l4ibf384@group.calendar.google.com'
    results = []
    page_token = None
    while True:
        events = CAL.events().list(calendarId=calendarID, pageToken=page_token).execute()
        for event_count, event in enumerate(events['items'][1:]):
            event_df = pd.io.json.json_normalize(event)
            event_df.columns = [col.replace(".", "_") for col in event_df.columns]
            results.append(event_df)
        page_token = events.get('nextPageToken')
        if not page_token:
            break
    # Concatentate one big dataframe
    results_df = pd.concat(results, axis=0)
    return results_df


def limit_sign_events(results_df):
    # Limit the WABA events to only those deemed signficant by manual filtering
    sign_events = open("bike_events_2014_2018.txt").read().splitlines()
    sign_events_df = results_df[results_df['id'].isin(sign_events)]
    sign_events_df = sign_events_df[['id', 'start_date', 'start_dateTime', 'summary']]
    return sign_events_df


def combine_dates():
    # Google calendar event sometimes have a date and sometime a datetime, this function combines them
    start_date = pd.to_datetime(sign_events_df['start_date'])
    start_dateTime = pd.to_datetime(sign_events_df['start_dateTime'])
    sign_events_df['combine_date'] = np.where(start_date.isnull(), start_dateTime, start_date)
    # Pull out date only from combine date
    return sign_events_df['combine_date'].dt.date


def create_bike_events(cur):
    # This script creates the bike events AWS table
    cur.execute("""
    DROP TABLE bike_events;
    CREATE TABLE bike_events(
        id  varchar(500) PRIMARY KEY,
        final_date  date,
        summary varchar(500)
        )
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Connect to Google Calendar
    CAL = gcal_authorization()
    # Pull all WABA Events
    results_df = pull_waba_events(CAL)
    # Limit calendar events to those that are significant based on subjective filtering
    sign_events_df = limit_sign_events(results_df)
    # Combine start date and start date time
    sign_events_df['final_date'] = combine_dates()
    # Set final date as index and keep only summary and id
    sign_events_df = sign_events_df[['id', 'final_date', 'summary']]
    sign_events_df.sort_values(['final_date'], inplace=True)
    # Output full WABA calendar
    TIMESTR = time.strftime("%Y%m%d_%H%M%S")
    filename = "WABA_Calendar_" + TIMESTR + ".csv"
    filepath = os.path.join(filename)
    results_df.to_csv(filepath, index=True)
    # Output significant events
    outname = "WABA_Significant_Events" + TIMESTR
    sign_events_df.to_csv(outname + ".csv", index=False, sep='|')
    # Create Database
    create_bike_events(cur)
    # Load to Database
    uf.aws_load(outname, "bike_events", cur)
    # Commit changes to database
    conn.commit()

