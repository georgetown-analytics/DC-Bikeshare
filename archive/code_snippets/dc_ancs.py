import requests
import pandas as pd
import util_functions as uf
import geopandas as gpd
from shapely.geometry import Point, Polygon

# Set environmental variable
uf.set_env_path()

# Download DC ANCs From Open Data DC Website as JSON
dc_anc_url = "https://opendata.arcgis.com/datasets/fcfbf29074e549d8aff9b9c708179291_1.geojson"
dc_anc = requests.get(dc_anc_url).json()

# Loop through each feature (cluster) in GeoJson and pull our metadata and polygon
feature_df_list = []
for enum, feature in enumerate(dc_anc['features']):
    # Pull out metadata
    feature_df = pd.DataFrame(feature['properties'], index=[enum])
    # Convert Polygon geometry to geodataframe
    geometry_df = gpd.GeoDataFrame(feature['geometry'])
    # Convert geometry to polygon and add back to metadata dataframe
    feature_df['polygon'] = Polygon(geometry_df['coordinates'].iloc[0])
    feature_df_list.append(feature_df)

# Combine each Cluster into master dataframe
dc_anc_df = pd.concat(feature_df_list, axis=0)

'''Bring in station information, keeping only region_id = 42 (DC) and assign cluster to each '''
# Connect to AWS
conn, cur = uf.aws_connect()
# Query cabi_region - note that longitute should always come first to generate a geographic Point
stations_df = pd.read_sql("""SELECT lon, lat, name, short_name, name  from cabi_stations_temp WHERE region_id = 42""", con=conn)
# Loop through each station and define the point based on log and lat
assignment_list = []
for enum, row in stations_df.iterrows():
    short_name = row['short_name']
    point = Point(row['lon'], row['lat'])
    # Loop through each neighorhood cluster determine if point is in polygon
    for anc_enum, anc_row in dc_anc_df.iterrows():
        if anc_row['polygon'].contains(point):
            anc = anc_row['ANC_ID']
            ward = anc[0]
            row_df = pd.DataFrame([[short_name, anc, ward]], columns=['short_name', 'anc', 'ward'])
            assignment_list.append(row_df)
            # Should only have one ANC assignment, so break once match is found
            break

# Combine cluster assignments
assigned_df = pd.concat(assignment_list, axis=0)

# Merge Assigned cluster back onto station information by short name

stations_df = stations_df.merge(assigned_df, on='short_name')

stations_df.to_csv("stations_df_anc.csv")
