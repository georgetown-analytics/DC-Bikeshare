import util_functions as uf
import pandas as pd
import os


def create_metro_hours(cur):
    # This script creates the bike events AWS table
    cur.execute("""
    DROP TABLE IF EXISTS metro_hours;
    CREATE TABLE metro_hours (
        day_of_week integer,
        op_status text,
        start_time time,
        end_time time)
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Load CSV FROM IPMUS Download as Dataframe
    csv_name = 'metro_hours'
    metro_hours_df = pd.read_csv(os.path.join("data", csv_name) + ".csv")
    # Output dataframe as CSV
    outname = csv_name + "_pipe_delimited"
    metro_hours_df.to_csv(os.path.join("data", outname) + ".csv", index=False, sep='|')
    # Create Database
    create_metro_hours(cur)
    # Load to Database
    uf.aws_load(outname, "metro_hours", cur)
    # Commit changes to database
    conn.commit()
