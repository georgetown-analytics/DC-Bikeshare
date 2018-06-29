import pandas as pd
import util_functions as uf
import altair as alt
import geopandas as gpd
import json
import requests

alt.renderers.enable('notebook')


def query_geo_ends(con):
    # Query Dockless Start by ANC and Overlaps by operator
    return pd.read_sql("""
                        SELECT * FROM crosstab($$
                            SELECT DISTINCT
                            end_anc.end_anc as ANC_ID,
                            end_anc.operatorclean as operator,
                            end_anc_trips/total_trips::float as end_perc
                            FROM
                            /* Count of dockless end anc trips*/
                            (SELECT DISTINCT
                            operatorclean,
                            end_anc,
                            count(*) as end_anc_trips
                            FROM dockless_trips_geo
                            WHERE end_geo_overlap = 0 AND end_anc is not null
                            group by 1, 2) as end_anc
                            /* Count of Total Dockless Trips*/
                            LEFT JOIN
                            (SELECT DISTINCT
                            operatorclean,
                            count(*) as total_trips
                            FROM dockless_trips_geo
                            where end_geo_overlap = 0 AND end_anc is not null
                            group by 1)  as tot
                            on end_anc.operatorclean = tot.operatorclean
                            ORDER by 1, 2$$
                        ,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
                        AS ct ("ANC_ID" text, "end_perc_jump" float, "end_perc_lime" float, "end_perc_mobike" float, "end_perc_ofo" float, "end_perc_spin" float)

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

    # Try and add ANC text labels
    '''hover = alt.selection(type='single', on='mouseover', nearest=True, fields=['geometry.coordinates'])

    text = chart.mark_text(dy=-5, align='right'
    ).encode(alt.Text('properties.ANC_ID', type='nominal'
    ), opacity=alt.condition(~hover, alt.value(0), alt.value(1))
    )'''
    return chart


if __name__ == "__main__":
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Download GeoJSON of ANCs from OpenData DC and convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features((download_json()))
    # Return Dataframe of Percent of Trips by ANC and Operator
    df = query_geo_ends(con=conn)
    df.fillna(0, inplace=True)
    # Merge dataframe to append percentages to Geo data
    gdf_merged = gdf.merge(df, on='ANC_ID', how='inner')
    # Prepare GeoDataframe for Altair
    json_features = json.loads(gdf_merged.to_json())
    data_geo = alt.Data(values=json_features['features'])
    # Generate Chloropaths
    jump_chart = gen_chloro(title='Jump', color_column='properties.end_perc_jump')
    lime_chart = gen_chloro(title='Lime', color_column='properties.end_perc_lime')
    mobike_chart = gen_chloro(title='Mobike', color_column='properties.end_perc_mobike')
    ofo_chart = gen_chloro(title='Ofo', color_column='properties.end_perc_ofo')
    spin_chart = gen_chloro(title='Spin', color_column='properties.end_perc_spin')
    combined = (mobike_chart & spin_chart) | (lime_chart & ofo_chart) | jump_chart
    combined.save('chloro_nongeo_operator_ends.html')

