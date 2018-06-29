import pandas as pd
import util_functions as uf
import altair as alt
import geopandas as gpd
import json
import requests

alt.renderers.enable('notebook')


def query_trips(con):
    # Query CaBi and Dockless Start and End by ANC
    return pd.read_sql("""SELECT DISTINCT
                    start_anc.start_anc as ANC_ID,
                    start_anc_trips/dless_total_trips::float as dless_start_perc,
                    end_anc_trips/dless_total_trips::float as dless_end_perc,
                    cabi_trips_start/cabi_total_trips::float as cabi_start_perc,
                    cabi_trips_end/cabi_total_trips::float as cabi_end_perc
                    FROM
                    /* Count of dockless start anc trips*/
                    (SELECT DISTINCT
                    start_anc,
                    count(*) as start_anc_trips
                    FROM dockless_trips_geo
                    WHERE operatorclean != 'jump' and start_anc is not null
                    group by 1) as start_anc
                    /* Count of dockless end anc trips*/
                    LEFT JOIN
                    (SELECT DISTINCT
                    end_anc,
                    count(*) as end_anc_trips
                    FROM dockless_trips_geo
                    WHERE operatorclean != 'jump' and end_anc is not null
                    group by 1) as end_anc
                    ON start_anc.start_anc = end_anc.end_anc
                    /* Count of Total Dockless Trips*/
                    LEFT JOIN
                    (SELECT DISTINCT
                     count(*) as dless_total_trips
                     FROM dockless_trips_geo
                     where operatorclean != 'jump')  as tot
                     on start_anc.start_anc = start_anc.start_anc
                     /* Count of Total DC to DC CaBi Trips during dockless pilot*/
                     LEFT JOIN
                     (SELECT DISTINCT
                      sum(cabi_trips_wdc_to_wdc) as cabi_total_trips
                      FROM final_db
                      where dless_trips_all > 0) as cabi_tot
                      on start_anc.start_anc = start_anc.start_anc
                    /* Count CaBi trips starts*/
                    LEFT JOIN
                        (select distinct
                        start_anc,
                        count(*) as cabi_trips_start
                        from
                        (select * from
                        cabi_trips
                        where start_date::date >= '09-10-2017' and start_date::date <= '04-30-2018') as cabi_trips
                        /*keep only dc to dc cabi trips*/
                        inner join
                        (select distinct
                         start_short_name,
                         end_short_name,
                         start_anc,
                         end_anc
                         from cabi_stations_geo_temp
                         where start_anc != '' and end_anc != '') as cabi_geo
                        on cabi_trips.start_station = cabi_geo.start_short_name and cabi_trips.end_station = cabi_geo.end_short_name
                        group by 1) as cabi_starts
                    ON start_anc.start_anc = cabi_starts.start_anc
                    /* Count CaBi trip ends*/
                    LEFT JOIN
                        (select distinct
                        end_anc,
                        count(*) as cabi_trips_end
                        from
                        (select * from
                        cabi_trips
                        where start_date::date >= '09-10-2017' and start_date::date <= '04-30-2018') as cabi_trips
                        /*keep only dc to dc cabi trips*/
                        inner join
                        (select distinct
                         start_short_name,
                         end_short_name,
                         start_anc,
                         end_anc
                         from cabi_stations_geo_temp
                         where start_anc != '' and end_anc != '') as cabi_geo
                        on cabi_trips.start_station = cabi_geo.start_short_name and cabi_trips.end_station = cabi_geo.end_short_name
                        group by 1) as cabi_ends
                    ON start_anc.start_anc = cabi_ends.end_anc
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
    df = query_trips(con=conn)
    # Merge dataframe to append percentages to Geo data
    gdf_merged = gdf.merge(df, left_on='ANC_ID', right_on='anc_id', how='inner')
    # Prepare GeoDataframe for Altair
    json_features = json.loads(gdf_merged.to_json())
    data_geo = alt.Data(values=json_features['features'])
    # Generate Chloropaths
    # cabi_start_chart = gen_chloro(title='Cabi Starts', color_column='properties.cabi_start_perc')
    cabi_end_chart = gen_chloro(title='Cabi Ends', color_column='properties.cabi_end_perc')
    # dless_start_chart = gen_chloro(title='Dockess Starts', color_column='properties.dless_start_perc')
    dless_end_chart = gen_chloro(title='Dockess Ends', color_column='properties.dless_end_perc')
    combined_chloro = (cabi_end_chart | dless_end_chart)
    # combined_chloro = alt.Chart.configure_legend(combined_chloro, orient='bottom-left')
    combined_chloro.save('combined_chloro.html')

