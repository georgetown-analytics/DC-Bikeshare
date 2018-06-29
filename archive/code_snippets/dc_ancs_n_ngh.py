import requests
import pandas as pd
import util_functions as uf
import geopandas as gpd
from shapely.geometry import Point, Polygon


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
    '''Bring in station information and assign cluster to each '''
    # Connect to AWS
    conn, cur = uf.aws_connect()
    # Query cabi_region - note that longitute should always come first to generate a geographic Point
    stations_df = pd.read_sql("""SELECT lon, lat, name, short_name, name  from cabi_stations_temp""", con=conn)
    return stations_df


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


if __name__ == '__main__':
    # Set environmental variable
    uf.set_env_path()
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
    stations_df = stations_df.merge(combined_assigned_df, on='short_name', how='left')

    stations_df.to_csv("stations_df_geo.csv")
