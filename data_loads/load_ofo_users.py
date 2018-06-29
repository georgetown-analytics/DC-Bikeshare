import pandas as pd
import os
import util_functions as uf
from datetime import datetime


def convert_month_toDT(x):
    # Convert text month to datetime, Ofo started on 10/8/2017
    if x in ['October']:
        s = "08 {}, 2017".format(x)
    elif x in ['November', 'December']:
        s = "01 {}, 2017".format(x)
    else:
        s = "01 {}, 2018".format(x)
    return datetime.strptime(s, '%d %B, %Y')


def create_ofo_users(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS ofo_users;
    CREATE TABLE ofo_users(
        userid varchar(30),
        usage_month date,
        trips integer
        );
            """)


if __name__ == "__main__":

    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Load Ofo user from report provided by DDOT
    user_report_loc = os.path.join("data", "User ids.xlsx")
    ofo_df = pd.read_excel(user_report_loc, sheet_name="ofo User IDs")
    # Drop second row since it's a second header
    ofo_df = ofo_df[ofo_df['October'] != 'UserID']
    ofo_df_stack = ofo_df.stack()
    ofo_df_stack = ofo_df_stack.reset_index()
    # Define Month in Datetime
    ofo_df_stack['usage_month'] = ofo_df_stack['level_1'].apply(convert_month_toDT)
    ofo_df_stack.drop(['level_0', 'level_1'], axis=1, inplace=True)
    ofo_df_stack.columns = ['user_id', 'usage_month']
    # Count trips by User and month
    ofo_count_df = ofo_df_stack.groupby(['user_id', 'usage_month']).size()
    ofo_count_df = ofo_count_df.reset_index()
    ofo_count_df.columns = ['user_id', 'usage_month', 'trips']
    ofo_count_df.sort_values(['user_id', 'usage_month'], inplace=True)
    # Output dataframe as CSV
    outname = "ofo_users"
    ofo_count_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
    # Create Table in AWS
    create_ofo_users(cur)
    # Load to Database
    uf.aws_load(outname, "ofo_users", cur)
    # Commit changes to database
    conn.commit()
