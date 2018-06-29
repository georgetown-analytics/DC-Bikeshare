import pandas as pd
import util_functions as uf
import os


def create_ml(cur, ml_name):
    # This script creates the machine learning results AWS tables
    cur.execute("""
    DROP TABLE IF EXISTS """ + ml_name + """;
    CREATE TABLE """ + ml_name + """(
        date date,
        dless numeric,
        error numeric,
        neg_error numeric,
        t date,
        yhat numeric,
        ytest numeric,
        dless_impact numeric);
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    for ml_file in os.listdir(os.path.join("data", "ml")):
        # Read in Overage Data
        csv_name = ml_file.replace(".csv", "")
        ml_df = pd.read_csv(os.path.join("data", "ml", csv_name + ".csv"))
        # Output final dataframe
        outname = csv_name + "pipe_delimited"
        ml_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
        # Create Database
        create_ml(cur, ml_name=csv_name)
        # Load to Database
        uf.aws_load(outname, csv_name, cur)
        # Commit changes to database
        conn.commit()
