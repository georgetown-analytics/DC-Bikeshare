import util_functions as uf
import pandas as pd


def create_acs(cur):
    # This script creates the bike events AWS table
    cur.execute("""
    DROP TABLE acs;
    CREATE TABLE acs (
        acs_id bigserial PRIMARY KEY,
        year integer,
        datanum integer,
        serial integer,
        hhwt integer,
        stateicp integer,
        statefip integer,
        county  integer,
        countyfips integer,
        metarea numeric,
        metaread numeric,
        city integer,
        citypop integer,
        gq integer,
        pernum integer,
        perwt integer,
        sex integer,
        age integer,
        race integer,
        raced integer,
        citizen integer,
        racesing numeric,
        racesingd numeric,
        racamind integer,
        racasian integer,
        racblk integer,
        racpacis integer,
        racwht integer,
        racother integer,
        empstat integer,
        empstatd integer,
        labforce integer,
        wkswork1 numeric,
        inctot integer,
        ftotinc integer,
        incwage integer,
        pwstate2 integer,
        tranwork integer,
        carpool integer,
        riders integer,
        trantime integer,
        qtrantim integer,
        qtranwor integer)
        )
    """)


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Load CSV FROM IPMUS Download as Dataframe
    csv_name = 'usa_00007'
    acs_df = pd.read_csv(csv_name + ".csv")
    # Set Primary Key
    acs_df.reset_index(inplace=True)
    # Fill all na with zeros
    acs_df.fillna(0, inplace=True)
    # Output dataframe as CSV
    outname = csv_name + "_pipe_delimited"
    acs_df.to_csv(outname + ".csv", index=False, sep='|')
    # Create Database
    create_acs(cur)
    # Load to Database
    uf.aws_load(outname, "acs", cur)
    # Commit changes to database
    conn.commit()
