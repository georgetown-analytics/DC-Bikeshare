import pandas as pd
import util_functions as uf


def create_cabi_price(cur):
    # This script creates the CaBi Price AWS table
    cur.execute("""
    DROP TABLE cabi_price;
    CREATE TABLE cabi_price(
        min_seconds integer PRIMARY KEY,
        max_seconds integer,
        casual_cost numeric,
        member_cost numeric
        )
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Read in Overage Data
    csv_name = "CaBiOverageCosts"
    overage_df = pd.read_csv(csv_name + ".csv")
    # Output final dataframe
    outname = csv_name + "pipe_delimited"
    overage_df.to_csv(outname + ".csv", index=False, sep='|')
    # Create Database
    create_cabi_price(cur)
    # Load to Database
    uf.aws_load(outname, "cabi_price", cur)
    # Commit changes to database
    conn.commit()
