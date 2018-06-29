import pandas as pd
import util_functions as uf
import os
from datetime import datetime


def convert_month_toDT(x, cur):
    # Convert int month to datetime, just dockless trips to get min date
    if x in [9, 10, 11, 12]:
        date = datetime(year=2017, month=x, day=1)
    elif x in [1, 2, 3, 4]:
        date = datetime(year=2018, month=x, day=1)
    else:
        date = x
    return date


def create_dockless_summary(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS dockless_summary;
    CREATE TABLE dockless_summary(
        operator text,
        month date,
        totaltrips numeric,
        totalbikes numeric
        );
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Load Summary Spreadsheet as Dataframe
    summary_loc = os.path.join("data", "Summary data.xlsx")
    summary_df = pd.read_excel(summary_loc, sheet_name="Summary")

    # Lowercase Operator and replace limebike with lime
    summary_df['Operator'] = summary_df['Operator'].str.lower().str.replace('limebike', 'lime').str.split(' ').str[0]

    # Standardize month
    summary_df['Month'] = summary_df['Month'].apply(lambda x: convert_month_toDT(x, cur))

    # Keep only Trips and Bikes
    keep_cols = ['Operator', 'Month', 'TotalTrips', 'TotalBikes']
    summary_df = summary_df[keep_cols]

    # Drop Records without Trips and Bikes
    summary_df = summary_df[summary_df['TotalBikes'].notnull()]
    # Output dataframe as CSV
    outname = "dockless_summary"
    summary_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')

    # Create Table in AWS
    create_dockless_summary(cur)
    # Load to Database
    uf.aws_load(outname, "dockless_summary", cur)

    # Commit changes to database
    conn.commit()
