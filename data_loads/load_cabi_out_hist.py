import pandas as pd
import util_functions as uf
import datetime
import requests
import io
import os


def pull_daily_data(date):
    # Pulls a date of outage data from Cabi Tracker
    params = {'s': date,
              'e': date}
    CaBiTrackerURl = "http://cabitracker.com/downloadoutage.php"
    urlData = requests.get(CaBiTrackerURl, params=params).content
    rawData = pd.read_csv(io.StringIO(urlData.decode('utf-8')))
    return rawData


def date_list(start_date, end_date):
    # Create list of date to loop through
    delta = end_date - start_date
    date_list = [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    return date_list


def gather_out_data(date_list):
    df_list = []
    for date in date_list:
        date_df = pull_daily_data(date)
        # keep only empty and full stations
        date_df = date_df[date_df['Status'].isin(['empty', 'full'])]
        df_list.append(date_df)
        print("{} processed".format(date))
    return df_list


def create_cabi_out_hist(cur):
    # This script creates the Cabi Outage Hitory AWS table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cabi_out_hist(
        terminal_number varchar(20),
        status varchar(20),
        start_time timestamp,
        end_time timestamp,
        duration integer,
        outage_id integer PRIMARY KEY
        )
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Gather Outage data
    start_date = datetime.datetime(2018, 4, 1)
    end_date = datetime.datetime(2018, 4, 30)
    date_list = date_list(start_date, end_date)
    df_list = gather_out_data(date_list)

    # Combine daily dataframes
    combined_df = pd.concat(df_list, axis=0)

    # Drop any fields that do not have numeric terminal number
    combined_df = combined_df[combined_df['Terminal Number'].astype(str).str.isdigit()]

    # Add outage_id continuing from last record in AWS table
    out_id_df = pd.read_sql("""SELECT outage_id from cabi_out_hist order by outage_id desc LIMIT 1 """, con=conn)
    last_outage_id = out_id_df['outage_id'].iloc[0]
    combined_df.reset_index(inplace=True)
    combined_df['outage_id'] = combined_df.index + 1 + last_outage_id
    # Drop unneeded fields
    combined_df.drop(['index', 'Station Name'], axis=1, inplace=True)
    # Output dataframe as CSV
    outname = "CaBi_Tracker_Outage_History_From_" + start_date.strftime('%Y-%m-%d') + "_To_" + end_date.strftime('%Y-%m-%d')
    combined_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
    # Create Database
    create_cabi_out_hist(cur)
    # Load to Database
    uf.aws_load(outname, "cabi_out_hist", cur)
    # Commit changes to database
    conn.commit()
