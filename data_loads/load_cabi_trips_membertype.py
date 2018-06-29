import pandas as pd
import os
import util_functions as uf

# TODO: Define function to pull CaBi Trip data from DDOT source


def trips_to_df(cabi_trip_dir):
    # Loop through CSVs of Trip Data
    trip_df_list = []
    csv_list = [f for f in os.listdir(cabi_trip_dir) if f.endswith('.txt')]
    for csv in csv_list:
        csv_name = csv.replace('.txt', '')
        print("{} has started processing".format(csv_name))
        # Load original CSV as dataframe
        trip_df = pd.read_csv(os.path.join(cabi_trip_dir, csv_name + '.txt'), delimiter="|")
        keep_cols = ["Startdate", "Enddate", "Bikenumber", "MemberType"]
        trip_df = trip_df[keep_cols]
        trip_df_list.append(trip_df)
    combined_df = pd.concat(trip_df_list, axis=0)
    return combined_df


def create_cabi_trips_membertype(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS cabi_trips_membertype;
    CREATE TABLE cabi_trips_membertype(
        Startdate timestamp,
        Enddate timestamp,
        Bikenumber varchar(30),
        member_type varchar(20),
        trip_id varchar(20) PRIMARY KEY
        );
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Loop through all CSVs in cabi trip data folder
    cabi_trip_dir = r'./data/Cabi_Trips_MemberType'

    # Convert trip data from CSV to dataframe
    combined_df = trips_to_df(cabi_trip_dir)

    # Sort by StartDate and Add trip_id
    combined_df.sort_values(['Startdate'], inplace=True)
    combined_df.reset_index(inplace=True)
    combined_df.drop(['index'], axis=1, inplace=True)

    combined_df['trip_id'] = combined_df.index + 1

    # Output dataframe as CSV
    outname = "Cabi_Trips_MemberType"
    combined_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')

    # Create Table in AWS
    create_cabi_trips_membertype(cur)

    # Load to Database
    uf.aws_load(outname, "cabi_trips_membertype", cur)

    # Commit changes to database
    conn.commit()
