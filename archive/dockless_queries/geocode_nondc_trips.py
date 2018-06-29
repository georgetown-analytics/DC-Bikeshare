import pandas as pd
import util_functions as uf
import geocoder


def get_state_county(x):
    # apply reverse geocode to geocoordinates, but sleep a millisecond in between requests
    g = geocoder.uscensus(x, method='reverse')
    return g.state, g.county


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Latitude and Longitude in trips data that is not in DC
    lat_lon_df = pd.read_sql("""select distinct
                     lat,
                     lon
                     from dockless_ngh_lookup
                     where nbh_names is null
                     """, con=conn)
    # Round the Latitude and Longitude to 5 decimal points and get a count, need less than 2K
    lat_lon_df['geo'] = list(zip(lat_lon_df['lat'].astype(float).round(3), lat_lon_df['lon'].astype(float).round(3)))
    to_geocode_df = lat_lon_df.drop_duplicates(['geo'])
    # Reverse Geocode lat and lon, grabbing city state and zip
    to_geocode_df[['state', 'county']] = to_geocode_df['geo'].apply(lambda x: get_state_county(x)).apply(pd.Series)

    # Generate Dataframe of dockless trips that where latitude and longitude is null in dockless_ngh_lookup
    outdc_trips_df = pd.read_sql("""select
                                tripid,
                                operatorclean,
                                startutc::date as start_date,
                                StartLatitude,
                                StartLongitude,
                                EndLatitude,
                                EndLongitude,
                                start_ngh.nbh_names as start_ngh,
                                end_ngh.nbh_names as end_ngh
                                FROM dockless_trips as trips
                                LEFT JOIN dockless_ngh_lookup as start_ngh
                                ON trips.StartLatitude = start_ngh.lat AND trips.StartLongitude = start_ngh.lon
                                LEFT JOIN dockless_ngh_lookup as end_ngh
                                ON trips.EndLatitude = end_ngh.lat AND trips.EndLongitude = end_ngh.lon
                                WHERE start_ngh.nbh_names is null or end_ngh.nbh_names is null
                     """, con=conn)
    # Round start and end geocoordinates
    outdc_trips_df['startgeo'] = list(zip(outdc_trips_df['startlatitude'].astype(float).round(3), outdc_trips_df['startlongitude'].astype(float).round(3)))
    outdc_trips_df['endgeo'] = list(zip(outdc_trips_df['endlatitude'].astype(float).round(3), outdc_trips_df['endlongitude'].astype(float).round(3)))

    # Merge on zip, suburb, city, state to start
    geo_keep_col = ['geo', 'county', 'state']
    start_geo = to_geocode_df[geo_keep_col].add_prefix("start")
    end_geo = to_geocode_df[geo_keep_col].add_prefix("end")
    outdc_trips_df = outdc_trips_df.merge(start_geo, how='left', on='startgeo')
    outdc_trips_df = outdc_trips_df.merge(end_geo, how='left', on='endgeo')
    outdc_trips_df.to_csv('test.csv', index=False)
 