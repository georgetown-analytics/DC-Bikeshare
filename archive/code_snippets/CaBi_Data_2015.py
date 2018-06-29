import pandas as pd
import time
import os
import sys

TIMESTR = time.strftime("%Y%m%d_%H%M%S")

# Load Cabi Trip Data as Data Frame
trip_df = pd.read_csv(r'Data/2015-q1_trip_history_data.csv')

# Derive Trip Date from Start Date time stamp
start_datetime = pd.to_datetime(trip_df['Start date'])
end_datetime = pd.to_datetime(trip_df['End date'])
trip_df['start_date'] = start_datetime.map(lambda x: x.date())
trip_df['end_date'] = end_datetime.map(lambda x: x.date())

# Append Region Code onto Trip Data
station_info_df = pd.read_csv(r'Output/CABI_Station_Info_20180223_090245.csv')
start_station_info_df = station_info_df.add_prefix('start_')
trip_df = trip_df.merge(start_station_info_df, left_on='Start station number',
                        right_on='start_short_name', how='left')
end_station_info_df = station_info_df.add_prefix('end_')
trip_df = trip_df.merge(end_station_info_df, left_on='End station number',
                        right_on='end_short_name', how='left')
trip_df['region_start_end'] = trip_df['start_region_code'] + \
    '_to_' + trip_df['end_region_code']
trip_df['station_start_end'] = trip_df['Start station'] + \
    '_to_' + trip_df['End station']

'''There are a handful of trips that will be dropped
because they are either warehouse trips or the station
no longer exists,option to find location by name instead of
station information'''
# print(trip_df[(trip_df['region_start_end'].isnull()) & (
# ~trip_df['station_start_end'].str.contains('6035 Warehouse'))]['station_start_end'].value_counts())


# Save the code for this pivot to potentially be used at a later date
'''trips_cols = ['start_date', 'region_start_end', 'Member type']
trips_by_cols = ['region_start_end', 'Member type']
trips_pivoted = pd.pivot_table(trip_df[trips_cols], index=[
                               'start_date'], columns=trips_by_cols, aggfunc=[len])
trips_flat_df = pd.DataFrame(trips_pivoted.to_records())
trips_flat_df.columns = [hdr.replace("('len', '", "").replace(
    "', '", "_").replace("')", "") for hdr in trips_flat_df.columns]'''

# Total Unique Bikes Used
bikes_count = trip_df.groupby('start_date')['Bike number'].nunique()
bikes_count = bikes_count.reset_index()
bikes_count = pd.DataFrame(bikes_count.to_records())
bikes_count.set_index('start_date', inplace=True)
bikes_count = bikes_count[['Bike number']].rename(columns={'Bike number': 'CaBi_B_All'})

# Unique Bikes Used by Region Start and End
bikes_by_regions_count = trip_df.groupby(['start_date', 'region_start_end'])['Bike number'].nunique()
bikes_by_regions_unstack = bikes_by_regions_count.unstack(level=-1)
bikes_by_regions_unstack = pd.DataFrame(bikes_by_regions_unstack.to_records())
bikes_by_regions_unstack.set_index('start_date', inplace=True)
bikes_by_regions_unstack = bikes_by_regions_unstack.add_prefix('CaBi_B_')

# Unique Bikes Used by Region and Member Type
bikes_by_member_count = trip_df.groupby(['start_date', 'region_start_end', 'Member type'])['Bike number'].nunique()
bikes_by_member_unstack = bikes_by_member_count.unstack(level=[-2, -1])
bikes_by_member_unstack = pd.DataFrame(bikes_by_member_unstack.to_records())
bikes_by_member_unstack.set_index('start_date', inplace=True)
bikes_by_member_unstack = bikes_by_member_unstack.add_prefix('CaBi_B_')
bikes_by_member_unstack.columns = [hdr.replace("('", "").replace("', '", "_").replace("')", "") for hdr in bikes_by_member_unstack.columns]

# Concat all these bike datasets
bikes_all = pd.concat([bikes_count, bikes_by_regions_unstack, bikes_by_member_unstack], axis=1)
# Fill all na as zeros
bikes_all.fillna(value=0, inplace=True)
filename = "CABI_Daily_Bikes" + TIMESTR + ".csv"
filepath = os.path.join("./Output", filename)
# bikes_all.to_csv(filepath, index=True)

# Total Trips per Day
trips_count = trip_df.groupby('start_date').size().reset_index(name='CaBi_T_All')
trips_count = trips_count.set_index(['start_date'])

# Total Trip per Day by Region Start and End
trips_by_regions = trip_df.groupby(['start_date', 'region_start_end']).size()
trips_by_regions = trips_by_regions.unstack(level=-1).add_prefix('CaBi_T_')


# Total Trips by Region and Member Type
trips_by_member = trip_df.groupby(['start_date', 'region_start_end', 'Member type']).size().unstack(level=[-2, -1])
trips_by_member = pd.DataFrame(trips_by_member.to_records()).set_index('start_date')
trips_by_member.columns = [hdr.replace("('", "").replace("', '", "_").replace("')", "") for hdr in trips_by_member.columns]


# Concat all these bike datasets and export
trips_all = pd.concat([trips_count, trips_by_regions, trips_by_member], axis=1)
trips_all.fillna(value=0, inplace=True)
filename = "CABI_Daily_Trips" + TIMESTR + ".csv"
filepath = os.path.join("./Output", filename)
trips_all.to_csv(filepath, index=True)

sys.exit()
