import pandas as pd
import util_functions as uf


def create_dockless_price(cur):
    # Loads data to the dockless_price AWS table
    cur.execute("""
    DROP TABLE dockless_price;
    CREATE TABLE dockless_price(
        min_seconds integer PRIMARY KEY,
        max_seconds integer,
        limebike numeric,
        spin numeric,
        ofo numeric,
        mobike numeric
        )
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Read in Overage Data
    csv_name = "DocklessTripCosts"
    overage_df = pd.read_csv(csv_name + ".csv")
    # Output final dataframe
    outname = csv_name + "pipe_delimited"
    overage_df.to_csv(outname + ".csv", index=False, sep='|')
    # Create Table
    create_dockless_price(cur)
    # Load to Database
    uf.aws_load(outname, "dockless_price", cur)
    # Commit changes to database
    conn.commit()
