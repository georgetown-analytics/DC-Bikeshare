import requests
import util_functions as uf
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon


def jump_proxy():
    # Connect to Social Bike API and pull hubs data
    JUMP_URL = "https://app.socialbicycles.com/api/hubs"
    username = os.environ.get("JUMP_USER")
    password = os.environ.get("JUMP_PASS")
    resp = requests.get(JUMP_URL, auth=requests.auth.HTTPBasicAuth(username, password))
    return resp.json()


def extract_json(jump_resp):
    # Loop through each feature in GeoJson and pull our metadata and polygon
    # Define empty list for concat
    item_df_list = []
    for enum, item in enumerate(jump_resp['items']):
        # Pull out metadata
        item_df = pd.DataFrame(item, index=[enum])
        # Convert Polygon geometry to geodataframe
        polygon_df = gpd.GeoDataFrame(item['polygon'])
        # Convert polygon to polygon and add back to metadata dataframe
        item_df['polygon'] = Polygon(polygon_df['coordinates'].iloc[0])
        # Convert center point to Point and add back to metadata dataframe
        item_df['middle_point'] = Point(item['middle_point']['coordinates'])
        item_df_list.append(item_df)
    # Combine each Cluster into master dataframe
    combined_df = pd.concat(item_df_list, axis=0)
    return combined_df


if __name__ == "__main__":
    uf.set_env_path()
    jump_resp = jump_proxy()
    combined_df = extract_json(jump_resp)
    print(combined_df)
