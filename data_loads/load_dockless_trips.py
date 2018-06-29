import pandas as pd
import util_functions as uf
import os
import numpy as np


def create_dockless_trips(cur):
    # This script creates the dockless trips received May, 18, 2018 AWS table
    cur.execute("""
    DROP TABLE IF EXISTS dockless_trips;
    CREATE TABLE dockless_trips(
        duration_in_minute numeric,
        EndLatitude numeric,
        EndLongitude numeric,
        end_time timestamp,
        endutc timestamp,
        EndWard numeric,
        Distance numeric,
        MilesMoved numeric,
        Operator varchar(50),
        StartLatitude numeric,
        StartLongitude numeric,
        start_time timestamp,
        startutc timestamp,
        StartWard numeric,
        TripID varchar(50) ,
        TripDistance numeric,
        UserID varchar(50),
        BikeID varchar(50),
        UniqueTripID varchar(50) PRIMARY KEY,
        OperatorClean varchar(50)
    )
    """)


def patch_user_id():
    # Userid is missing for ~15,000 limebike records in most recent file provided by DDOT. Patch with older file
    patch_df = pd.read_sql("""select DISTINCT
                              userid::text as user_id_patch,
                              startutc,
                              endutc,
                              operatorclean,
                              startlatitude::text as start_lat,
                              startlongitude::text as start_lon,
                              endlatitude::text as end_lat,
                              endlongitude::text as end_lon
                              FROM dockless_trips_org
                              WHERE OperatorClean='lime';
                           """, con=conn)
    trips_df['startutc'] = pd.to_datetime(trips_df['start_time_est'])
    trips_df['endutc'] = pd.to_datetime(trips_df['end_time_est'])
    merge_columns = [col for col in patch_df.columns if col != 'user_id_patch']
    merge_df = trips_df.merge(patch_df, on=merge_columns, how='left')
    trips_df['user_id'] = np.where((merge_df['user_id_patch'].notnull()) & (merge_df['user_id'] == 0), merge_df['user_id_patch'], trips_df['user_id'])
    # Drop extra calculated fields
    return trips_df.drop(['startutc', 'endutc'], axis=1)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Read in Dockless Trips Data
    csv_name = "Updated_Cleaned_Data_June8th_UptoMay"
    trips_df = pd.read_csv(os.path.join("data", csv_name + ".csv"), dtype=str)
    # Drop Scooter Only Operators
    trips_df = trips_df[~trips_df['operator'].isin(['Bird', 'Skip'])]
    # Drop records in May 2018, will not be evaluating since missing some
    trips_df = trips_df[pd.to_datetime(trips_df['start_time_est']) < '2018-05-01']
    trips_df.reset_index(inplace=True)
    trips_df.drop(['index'], axis=1, inplace=True)
    # Generate Tripid, since blank is data from DDOT
    trips_df['trip_id'] = pd.Series(trips_df.index + 1).astype(str).apply(lambda x: x.zfill(5))
    # Create a new trip_id that includes the first letter of the operator name
    trips_df['UniqueTripID'] = trips_df['operator'].str.upper().str[0] + trips_df['trip_id']
    # Fill missing with 0
    trips_df.fillna(0, inplace=True)
    # Create clean version of operator
    trips_df['operatorclean'] = trips_df['operator'].map(lambda x: x.split(" ")[0].lower().replace('limebike', 'lime'))
    # Patch limebike user_id with original dockless trips if missing
    trips_df = patch_user_id()
    # Output final dataframe
    outname = csv_name + "pipe_delimited"
    trips_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
    # Create Database
    create_dockless_trips(cur)
    # Load to Database
    uf.aws_load(outname, "dockless_trips", cur)
    # Commit changes to database
    conn.commit()
