import pandas as pd
import numpy as np
import os
from geopy.geocoders import Nominatim
import time


def get_address_raw(x):
    # apply reverse geocode to geocoordinates, but sleep a millisecond in between requests
    time.sleep(.001)
    return geolocator.reverse(x).raw


if __name__ == "__main__":
    # Read in Overage Data
    csv_name = "feburaryaddedutc"
    trips_df = pd.read_csv(os.path.join('data', csv_name + ".csv"), index_col=[0], dtype=str)
    # Drop duplicate records by Operator and TripID
    trips_df = trips_df.drop_duplicates(["Operator", "TripID"])
    # Fill missing with 0
    trips_df.fillna(0, inplace=True)
    # Create a new trip_id that includes the first letter of the operator name
    trips_df['UniqueTripID'] = trips_df['Operator'].str[0] + trips_df['TripID']
    # Drop records without an Operator
    trips_df = trips_df[trips_df['Operator'] != 0]
    # Create clean version of operator
    trips_df['OperatorClean'] = trips_df['Operator'].map(lambda x: x.split(" ")[0].lower().replace('limebike', 'lime'))
    # Set enddate equal to startdate if missing
    trips_df['EndDate'] = np.where(trips_df['EndDate'] == 0, trips_df['StartDate'], trips_df['EndDate'])
    trips_df['endposct'] = np.where(trips_df['endposct'] == 0, trips_df['posct'], trips_df['endposct'])
    trips_df['endutc'] = np.where(trips_df['endutc'] == 0, trips_df['startutc'], trips_df['endutc'])
    # Reverse Geocode the start and end points
    geolocator = Nominatim()
    # Start Point City, State, Zip
    trips_df['start_geo'] = trips_df['StartLatitude'].astype(float).round(2).astype(str) + ", " + trips_df['StartLongitude'].astype(float).round(2).astype(str)
    trips_df['end_geo'] = trips_df['EndLatitude'].astype(float).round(2).astype(str) + ", " + trips_df['EndLongitude'].astype(float).round(2).astype(str)
    print(trips_df['start_geo'].value_counts())
    print(trips_df['start_geo'].value_counts())

    import sys
    sys.exit()
    trips_df['start_address_raw'] = trips_df['start_geo'].apply(lambda x: get_address_raw(x))
    trips_df['start_city'] = trips_df['start_address_raw'].apply(lambda x: x['address']['city'])
    trips_df['start_state'] = trips_df['start_address_raw'].apply(lambda x: x['address']['state'])
    trips_df['start_zip'] = trips_df['start_address_raw'].apply(lambda x: x['address']['postcode'])
    # End Point City, State, Zip
    trips_df['end_geo'] = trips_df['EndLatitude'] + ", " + trips_df['EndLongitude']
    trips_df['end_address_raw'] = trips_df['end_geo'].apply(lambda x: get_address_raw(x))
    trips_df['end_city'] = trips_df['end_address_raw'].apply(lambda x: x['address']['city'])
    trips_df['end_state'] = trips_df['end_address_raw'].apply(lambda x: x['address']['state'])
    trips_df['end_zip'] = trips_df['end_address_raw'].apply(lambda x: x['address']['postcode'])
    trips_df.to_csv(os.path.join("data", "dockless_plus_city_state_zip.csv"))
    # Count by operator, start city state and end city state
    groupby_cols = ['OperatorClean', 'start_city', 'start_state', 'end_city', 'end_state']
    print(trips_df.groupby(groupby_cols).size())

