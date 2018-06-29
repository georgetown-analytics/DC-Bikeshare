import requests
import pandas as pd
import util_functions as uf
import geopandas as gpd
from shapely.geometry import Polygon
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


def create_ngh(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS ngh;
    CREATE TABLE ngh(
        name varchar(20),
        nbh_names varchar(200),
        objectid integer PRIMARY KEY,
        shape_area numeric,
        shape_length numeric,
        type text,
        web_url varchar(200),
        polygon geography);
            """)


def create_anc(cur):
    # This script creates the CaBi Stations Geo Temp AWS table
    cur.execute("""
    DROP TABLE IF EXISTS anc;
    CREATE TABLE anc(
        anc_id varchar(20),
        name varchar(20),
        objectid integer PRIMARY KEY,
        shape_area numeric,
        shape_length numeric,
        web_url varchar(200),
        polygon geography);
            """)


if __name__ == '__main__':
    # Set environmental variable
    uf.set_env_path()
    # Connect to AWS
    conn, cur = uf.aws_connect()
    # Download DC ANCs and Neighborhood Clusters From Open Data DC Website as JSONs
    json_id_dict = {'ngh': "f6c703ebe2534fc3800609a07bad8f5b_17",
                    'anc': "fcfbf29074e549d8aff9b9c708179291_1"}
    for json_name, json_id in json_id_dict.items():
        combined_df = extract_json(json_id)
        # Output dataframe as CSV
        outname = "json_name"
        combined_df.to_csv(os.path.join("data", outname + ".csv"), index=False, sep='|')
        # Create Database
        if json_name == 'ngh':
            create_ngh(cur)
        else:
            create_anc(cur)
        # Load to Database
        uf.aws_load(outname, json_name, cur)
        # Commit changes to database
        conn.commit()
