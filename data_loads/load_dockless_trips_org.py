import pandas as pd
import util_functions as uf
import numpy as np
import os


def create_dockless_trips_org(cur):
    # This script creates the dockless trips received in April 2018 AWS table
    cur.execute("""
    DROP TABLE IF EXISTS dockless_trips_org;
    CREATE TABLE dockless_trips_org(
        X integer,
        Operator varchar(50),
        TripID varchar(50) PRIMARY KEY,
        BikeID varchar(50),
        UserID varchar(50),
        StartDate timestamp,
        EndDate timestamp,
        StartLatitude numeric,
        StartLongitude numeric,
        EndLatitude numeric,
        EndLongitude numeric,
        TripDistance numeric,
        MetersMoved numeric,
        StartWard numeric,
        EndWard numeric,
        Distance numeric,
        posct timestamp,
        endposct timestamp,
        startutc timestamp,
        endutc timestamp,
        UniqueTripID varchar(50),
        OperatorClean varchar(50)
    )
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Read in Overage Data
    csv_name = "feburaryaddedutc"
    trips_df = pd.read_csv(os.path.join("data", csv_name + ".csv"), index_col=[0], dtype=str)
    # Drop duplicate records by Operator and TripID
    trips_df = trips_df.drop_duplicates(["Operator", "TripID"])
    print(len(trips_df['TripID']))
    # Fill missing with 0
    trips_df.fillna(0, inplace=True)
    # Create a new trip_id that includes the first letter of the operator name
    trips_df['UniqueTripID'] = trips_df['Operator'].str[0] + trips_df['TripID']
    # Drop records without an Operator
    trips_df = trips_df[trips_df['Operator'] != 0]
    # Create clean version of operator
    trips_df['OperatorClean'] = trips_df['Operator'].map(lambda x: x.split(" ")[0].lower().replace('limebike', 'lime'))
    # Set enddate equal to startdate if missing
    trips_df['EndDate'] = np.where(trips_df['EndDate'] == 0, trips_df['StartDate'], trips_df['EndDate'])
    trips_df['endposct'] = np.where(trips_df['endposct'] == 0, trips_df['posct'], trips_df['endposct'])
    trips_df['endutc'] = np.where(trips_df['endutc'] == 0, trips_df['startutc'], trips_df['endutc'])
    # Output final dataframe
    outname = csv_name + "pipe_delimited"
    trips_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
    # Create Database
    create_dockless_trips_org(cur)
    # Load to Database
    uf.aws_load(outname, "dockless_trips_org", cur)
    # Commit changes to database
    conn.commit()
