import pandas as pd
import os
import util_functions as uf


def load_spreadsheet(spreadsheet):
    # Load membership spreadsheet as dataframe
    loc = os.path.join("data", spreadsheet)
    return pd.read_excel(loc, index_col=0)


def create_cabi_membership(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS cabi_membership;
    CREATE TABLE cabi_membership(
        month date PRIMARY KEY,
        annual_member_purch numeric,
        monthly_member_purch numeric,
        day_key_member_purch numeric,
        multi_day_pass_purch numeric,
        single_day_pass_purch numeric,
        single_trip_pass_purch numeric
        );
            """)


if __name__ == "__main__":

    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    spreadsheet_list = ["03a Subscription Purchases by Month All Time - Annual 2018-05-17T0922.xlsx",
                        "03b Subscription Purchases by Month All Time - 30-Day 2018-05-17T0923.xlsx",
                        "03c Subscription Purchases by Month All Time - Day Key 2018-05-17T0924.xlsx",
                        "03d Subscription Purchases by Month All Time - Casuals 2018-05-17T0924.xlsx"]
    df_list = []
    for spreadsheet in spreadsheet_list:
        # Load Spreadsheet as Dataframe
        df = load_spreadsheet(spreadsheet)
        membership_type = spreadsheet.split(' - ')[1].split(" ")[0]
        # Keep only month and total
        if membership_type != 'Casuals':
            keep_cols = ['Local Purchase Month', 'Total Number Bikes Purchased']
            df = df[keep_cols]
            df.columns = ['Local Purchase Month', membership_type]
        # set month as index
        df.set_index(['Local Purchase Month'], inplace=True)
        # Append dataframe to list
        df_list.append(df)

    # Combine Dataframe
    combined_df = pd.concat(df_list, axis=1)
    combined_df.reset_index(inplace=True)
    combined_df['Local Purchase Month'] = combined_df['Local Purchase Month'].astype('datetime64[ns]')
    # Fill missing with zeros
    combined_df = combined_df.fillna(0)
    # Output dataframe as CSV
    outname = "cabi_membership"
    combined_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')

    # Create Table in AWS
    create_cabi_membership(cur)

    # Load to Database
    uf.aws_load(outname, "cabi_membership", cur)

    # Commit changes to database
    conn.commit()
