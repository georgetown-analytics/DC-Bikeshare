import pandas as pd
import util_functions as uf
import os


def create_dockless_bikes_api(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS dockless_bikes_api;
    CREATE TABLE dockless_bikes_api(
        date date,
        operator text,
        bikes_available integer
        );
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Load raw CSV as Dataframe
    raw_df = pd.read_csv(os.path.join("data", "bikes_per_day.csv"))

    # Lowercase provider and replace limebike with lime
    raw_df['provider'] = raw_df['provider'].str.lower().str.replace('limebike', 'lime')

    # Replace data outliers with reasonable number for Jump
    jump_outlier_mask = (raw_df['ride_date'].isin(['2018-02-22', '2018-02-23'])) & (raw_df['provider'] == 'jump')
    raw_df.loc[jump_outlier_mask, 'daily_bikes_available'] = 71
    print(raw_df.tail(20))

    # Output dataframe as CSV
    outname = "dockless_bikes_api"
    raw_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')

    # Create Table in AWS
    create_dockless_bikes_api(cur)
    # Load to Database
    uf.aws_load(outname, "dockless_bikes_api", cur)

    # Commit changes to database
    conn.commit()
