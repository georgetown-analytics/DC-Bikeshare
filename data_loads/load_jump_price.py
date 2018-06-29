import pandas as pd
import util_functions as uf


def create_jump_price(cur):
    # This script loads data to the jump_price AWS table
    cur.execute("""
    DROP TABLE jump_price;
    CREATE TABLE jump_price(
        min_seconds integer PRIMARY KEY,
        max_seconds integer,
        cost numeric
        )
            """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Read in Overage Data
    csv_name = "JumpTripCosts"
    overage_df = pd.read_csv(csv_name + ".csv")
    # Output final dataframe to memory
    outname = csv_name + "pipe_delimited"
    overage_df.to_csv(outname + ".csv", index=False, sep='|')
    # Create Table
    create_jump_price(cur)
    # Load to Database
    uf.aws_load(outname, "jump_price", cur)
    # Commit changes to database
    conn.commit()
