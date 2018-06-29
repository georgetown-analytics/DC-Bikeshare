import psycopg2
import pandas as pd
import os
import util_functions as uf
import numpy as np
import matplotlib.style as style
import matplotlib.pyplot as plt
import seaborn as sns

uf.set_env_path()
conn, cur = uf.aws_connect()

# Query cabi trips
cabi_trips = pd.read_sql("""SELECT DISTINCT EXTRACT(YEAR FROM start_date) AS year,
                                            member_type,
                                            COUNT(*) as trip_count,
                                            MIN(duration/60000) AS min_duration_mins,
                                            AVG(duration/60000) AS mean_duration_mins,
                                            MAX(duration/60000) AS max_duration_mins
                                            from cabi_trips
                                            WHERE member_type != 'Unknown' and EXTRACT(YEAR FROM start_date) = 2010
                                            GROUP BY EXTRACT(YEAR FROM start_date), member_type
                                            """, con=conn)

print(cabi_trips)
import sys
sys.exit()

#Calculate median and IQR
duration_med = np.percentile(cabi_trips['duration_mins'], 50)
q75, q25 = np.percentile(cabi_trips['duration_mins'], [75 , 25])
iqr = q75 - q25

#Remove values (outliers) that are 3 times IQR away from median
cabi_trips = cabi_trips[cabi_trips['duration_mins'] < duration_med + (3 * iqr)]

#Set plot style
style.use('fivethirtyeight')

#create violin plot
ax = sns.violinplot(x = 'year', y = 'duration_mins', hue = 'member_type', data = cabi_trips)
plt.show()
