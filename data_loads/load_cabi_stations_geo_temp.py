import requests
import pandas as pd
import util_functions as uf
import geopandas as gpd
from shapely.geometry import Point, Polygon
import itertools
from geopy.distance import vincenty
import os


def extract_json(json_id):
    # Loop through each feature in GeoJson and pull our metadata and polygon
    url = "https://opendata.arcgis.com/datasets/{}.geojson".format(json_id)
    resp = requests.get(url).json()
    # Define empty list for concat
    feature_df_list = []
    for enum, feature in enumerate(resp['features']):
        # Pull out metadata
        feature_df = pd.DataFrame(feature['properties'], index=[enum])
        # Convert Polygon geometry to geodataframe
        geometry_df = gpd.GeoDataFrame(feature['geometry'])
        # Convert geometry to polygon and add back to metadata dataframe
        feature_df['polygon'] = Polygon(geometry_df['coordinates'].iloc[0])
        feature_df_list.append(feature_df)
    # Combine each Cluster into master dataframe
    combined_df = pd.concat(feature_df_list, axis=0)
    return combined_df


def get_aws_station_info():
    # Bring in station information and assign cluster to each
    stations_df = pd.read_sql("""SELECT cabi_stations_temp.*, cabi_system.code AS region_code
                                 FROM cabi_stations_temp
                                 LEFT JOIN cabi_system
                                 ON cabi_stations_temp.region_id = cabi_system.region_id""", con=conn)
    return stations_df


def expand_grid(data_dict):
    # Expands the start and stop stations to have every combination as rows
    rows = itertools.product(*data_dict.values())
    return pd.DataFrame.from_records(rows, columns=data_dict.keys())


def define_final_vars(json_name, geo_row, short_name):
    # Define the variables specific to each geojson
    if json_name == 'anc':
        anc = geo_row['ANC_ID']
        ward = anc[0]
        row_df = pd.DataFrame([[short_name, anc, ward]], columns=['short_name', 'anc', 'ward'])
    else:
        ngh_names = geo_row['NBH_NAMES']
        cluster_name = geo_row['NAME']
        row_df = pd.DataFrame([[short_name, cluster_name, ngh_names]], columns=[json_name + '_short_name', 'cluster_name', 'ngh_names'])
    return row_df


def assign_polygon():
    # Loop through each station and define the point based on log and lat
    assignment_list = []
    for enum, row in stations_df.iterrows():
        short_name = row['short_name']
        point = Point(row['lon'], row['lat'])
        # Loop through each neighorhood cluster determine if point is in polygon
        for geo_enum, geo_row in combined_df.iterrows():
            if geo_row['polygon'].contains(point):
                row_df = define_final_vars(json_name, geo_row, short_name)
                assignment_list.append(row_df)
                # Should only have one ANC assignment, so break once match is found
                break
    # Combine cluster assignments
    assigned_df = pd.concat(assignment_list, axis=0)
    return assigned_df


def create_cabi_stations_geo_temp(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE cabi_stations_geo_temp;
    CREATE TABLE cabi_stations_geo_temp(
        start_short_name varchar(20),
        end_short_name varchar(20),
        start_capacity integer,
        start_eightd_has_key_dispenser boolean,
        start_lat numeric,
        start_lon numeric,
        start_name varchar(200),
        start_region_id integer,
        start_rental_methods varchar(200),
        start_rental_url varchar(200),
        start_station_id integer,
        start_region_code varchar(10),
        start_cluster_name varchar(20),
        start_ngh_names varchar(300),
        start_anc varchar(10),
        start_ward varchar(10),
        end_capacity integer,
        end_eightd_has_key_dispenser boolean,
        end_lat numeric,
        end_lon numeric,
        end_name varchar(200),
        end_region_id integer,
        end_rental_methods varchar(200),
        end_rental_url varchar(200),
        end_station_id integer,
        end_region_code varchar(10),
        end_cluster_name varchar(20),
        end_ngh_names varchar(300),
        end_anc varchar(10),
        end_ward varchar(10),
        dist_miles numeric)
            """)


if __name__ == '__main__':
    # Set environmental variable
    uf.set_env_path()
    # Connect to AWS
    conn, cur = uf.aws_connect()
    # Bring in station information AWS
    stations_df = get_aws_station_info()
    # Download DC ANCs and Neighborhood Clusters From Open Data DC Website as JSONs
    json_id_dict = {'ngh': "f6c703ebe2534fc3800609a07bad8f5b_17",
                    'anc': "fcfbf29074e549d8aff9b9c708179291_1"}
    combined_assigned_df_list = []
    for json_name, json_id in json_id_dict.items():
        combined_df = extract_json(json_id)
        # Assign respecitve polygon to each station lat and lon
        assigned_df = assign_polygon()
        combined_assigned_df_list.append(assigned_df)
    # Concatentate combined assigned dfs
    combined_assigned_df = pd.concat(combined_assigned_df_list, axis=1).drop(['ngh_short_name'], axis=1)
    # Merge Assigned cluster back onto station information by short name
    stations_df = stations_df.merge(combined_assigned_df, on='short_name', how='left').drop(['eightd_station_services'], axis=1)
    # Expand station information to have each station be both a start and end station
    start_stations_df = stations_df.copy()
    start_stations_df.columns = ["start_" + str(col) for col in start_stations_df.columns]
    end_stations_df = stations_df.copy()
    end_stations_df.columns = ["end_" + str(col) for col in end_stations_df.columns]
    expanded_df = expand_grid(dict(pd.DataFrame(start_stations_df['start_short_name']).to_dict('list'), **pd.DataFrame(end_stations_df['end_short_name']).to_dict('list')))
    # Merge on start and end station DFs
    expanded_df = expanded_df.merge(start_stations_df, on='start_short_name', how='left')
    expanded_df = expanded_df.merge(end_stations_df, on='end_short_name', how='left')
    # Calculate Distance between start and end station
    dist_miles_list = []
    for enum, row in expanded_df.iterrows():
        start_loc = (row['start_lat'], row['start_lon'])
        end_loc = (row['end_lat'], row['end_lon'])
        dist_miles = vincenty(start_loc, end_loc).miles
        dist_miles_list.append(dist_miles)
    dist_miles_df = pd.DataFrame({'dist_miles': dist_miles_list})
    expanded_df = pd.concat([expanded_df, dist_miles_df], axis=1)
    # Output dataframe as CSV
    outname = "CaBi_Stations_Geo_Temp"
    expanded_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
    # Create Database
    create_cabi_stations_geo_temp(cur)
    # Load to Database
    uf.aws_load(outname, "cabi_stations_geo_temp", cur)
    # Commit changes to database
    conn.commit()
