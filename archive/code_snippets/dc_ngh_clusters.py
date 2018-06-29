import requests
import pandas as pd
import util_functions as uf
import geopandas as gpd
from shapely.geometry import Point, Polygon

# Set environmental variable
uf.set_env_path()

# Download DC Neighborhood Clusters Data From Open Data DC Website as JSON
dc_clusters_url = "https://opendata.arcgis.com/datasets/f6c703ebe2534fc3800609a07bad8f5b_17.geojson"
dc_clusters = requests.get(dc_clusters_url).json()

# Loop through each feature (cluster) in GeoJson and pull our metadata and polygon
feature_df_list = []
for enum, feature in enumerate(dc_clusters['features']):
    # Pull out metadata
    feature_df = pd.DataFrame(feature['properties'], index=[enum])
    # Convert Polygon geometry to geodataframe
    geometry_df = gpd.GeoDataFrame(feature['geometry'])
    # Convert geometry to polygon and add back to metadata dataframe
    feature_df['polygon'] = Polygon(geometry_df['coordinates'].iloc[0])
    feature_df_list.append(feature_df)

# Combine each Cluster into master dataframe
dc_clusters_df = pd.concat(feature_df_list, axis=0)

'''Bring in station information, keeping only region_id = 42 (DC) and assign cluster to each '''
# Connect to AWS
conn, cur = uf.aws_connect()
# Query cabi_region - note that longitute should always come first to generate a geographic Point
stations_df = pd.read_sql("""SELECT lon, lat, name, short_name, name  from cabi_stations_temp WHERE region_id = 42""", con=conn)
# Loop through each station and define the point based on log and lat
assigned_cluster_list = []
for enum, row in stations_df.iterrows():
    short_name = row['short_name']
    point = Point(row['lon'], row['lat'])
    # Loop through each neighorhood cluster determine if point is in polygon
    for cluster_enum, cluster_row in dc_clusters_df.iterrows():
        if cluster_row['polygon'].contains(point):
            ngh_names = cluster_row['NBH_NAMES']
            cluster_name = cluster_row['NAME']
            cluster_row_df = pd.DataFrame([[short_name, cluster_name, ngh_names]], columns=['short_name', 'cluster_name', 'ngh_names'])
            assigned_cluster_list.append(cluster_row_df)

#Combine cluster assignments
assigned_cluster_df = pd.concat(assigned_cluster_list, axis=0)

# Merge Assigned cluster back onto station information by short name

stations_df = stations_df.merge(assigned_cluster_df, on='short_name')

stations_df.to_csv("stations_df.csv")
