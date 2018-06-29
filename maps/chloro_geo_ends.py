import pandas as pd
import util_functions as uf
import altair as alt
import geopandas as gpd
import json
import requests

alt.renderers.enable('notebook')


def query_geo_ends(con):
    # Query Dockless Start by ANC and Overlaps
    return pd.read_sql("""SELECT DISTINCT
                        end_anc.end_anc as ANC_ID,
                        end_anc.end_geo_overlap::text,
                        end_anc_trips/total_trips::float as end_perc
                        FROM
                        /* Count of dockless end anc trips*/
                        (SELECT DISTINCT
                        end_anc,
                        end_geo_overlap,
                        count(*) as end_anc_trips
                        FROM dockless_trips_geo
                        WHERE operatorclean != 'jump' and end_anc is not null
                        group by 1, 2) as end_anc
                        /* Count of Total Dockless Trips*/
                        LEFT JOIN
                        (SELECT DISTINCT
                        end_geo_overlap,
                        count(*) as total_trips
                        FROM dockless_trips_geo
                        where operatorclean != 'jump' and end_anc is not null
                        group by 1)  as tot
                        on end_anc.end_geo_overlap = tot.end_geo_overlap
                """, con=con)


def download_json():
    # Downloads ANC JSON from Open Data DC
    url = "https://opendata.arcgis.com/datasets/fcfbf29074e549d8aff9b9c708179291_1.geojson"
    resp = requests.get(url).json()
    return resp


def gen_chloro(title, color_column):
    # Generate Chloropeth
    chart = alt.Chart(data_geo, title=title).mark_geoshape(
        fill='lightgray',
        stroke='black'
    ).properties(
        width=400,
        height=400
    ).encode(
        alt.Color(color_column, type='quantitative', scale=alt.Scale(scheme='bluegreen'))
    )
    return chart


if __name__ == "__main__":
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Download GeoJSON of ANCs from OpenData DC and convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features((download_json()))
    # Return Dataframe of Percent of Trips by ANC
    df = query_geo_ends(con=conn)
    df.set_index(['anc_id', 'end_geo_overlap'], inplace=True)
    unstacked_df = df.unstack(level=-1)
    unstacked_df = pd.DataFrame(unstacked_df.to_records())
    unstacked_df.columns = [hdr.replace("('", "").replace("', '", "_").replace("')", "") for hdr in unstacked_df.columns]
    # Merge dataframe to append percentages to Geo data
    gdf_merged = gdf.merge(unstacked_df, left_on='ANC_ID', right_on='anc_id', how='inner')
    # Prepare GeoDataframe for Altair
    json_features = json.loads(gdf_merged.to_json())
    data_geo = alt.Data(values=json_features['features'])
    # Generate Chloropaths
    geo_yes_chart = gen_chloro(title='Geographic Overlap Ends', color_column='properties.end_perc_1')
    geo_no_chart = gen_chloro(title='Not Geographic Overlap Ends', color_column='properties.end_perc_0')
    combined_chloro = (geo_yes_chart | geo_no_chart)
    # combined_chloro = alt.Chart.configure_legend(combined_chloro, orient='bottom-left')
    combined_chloro.save('geo_end_chloro.html')

