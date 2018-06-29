import sys
sys.path.append("..")

import numpy as np
from read_aws import *
from google_drive_push import *
import seaborn as sns
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
import re
from dockless_exploration_graphs import *

'''Single Trips as % of all CaBi passes (not memberships) purchased monthly
     [[PLOT]]
'''
if __name__ == '__main__':

    conn = read_only_connect_aws()
    plt.style.use('fivethirtyeight')
    df = pd.read_sql(
        """select
            month,
            (single_trip_pass_purch/(multi_day_pass_purch + single_day_pass_purch + single_trip_pass_purch)) as single_pass_perc
            from cabi_membership
            where single_trip_pass_purch>0;
             """, con=conn, parse_dates=['month'])
    print(df.tail())

    df['m_yr'] = month_prep(df['month'].dt.month).map(str) + \
        "\n" + df['month'].dt.year.map(str)
    ax = sns.pointplot(x='m_yr', y='single_pass_perc', data=df)
    plt.xticks(rotation=45)

    dr = open_drive()

    all_in_one_save(
        "Single Trip Percent", "C:/Users/Noah/Bikeshare-DC_Old/For Upload", dr,
        '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3')
