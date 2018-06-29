import pandas as pd
import util_functions as uf
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Trips by Date and Operator
    df = pd.read_sql("""select distinct
                     startutc::date as trip_date,
                     OperatorClean,
                     count(*) as trips
                     from dockless_trips
                     where startutc::date >= '2017-09-20'
                     group by trip_date, OperatorClean
                     order by trip_date, OperatorClean
                     """, con=conn)
    # Unstack DataFrame
    pivot_df = df.pivot(index='trip_date', columns='operatorclean', values='trips')

    # Plot Raw Counts
    pivot_df.plot.line()
    plt.show()

    # Calculate Percent of Trips
    for column in pivot_df.columns:
        if column != "trip_date":
            pivot_df[column + "_perc"] = pivot_df[column] / pivot_df[column].sum()

    # Plot Percent of Trips
    perc_col = [col for col in pivot_df.columns if col.endswith("_perc")]
    pivot_df[perc_col].plot.line()
    plt.show()

    # Trips by Date for all Dockless compared to CaBi DC trips
    comp_df = pd.read_sql("""select trip_date,
                            dockless_trips,
                            cabi_trips
                            from 
                            (select distinct
                            startutc::date as trip_date,
                            count(*) as dockless_trips
                            FROM dockless_trips
                            where startutc::date >= '2017-09-20'
                            group by trip_date
                            ) as d
                            LEFT JOIN (select trips.start_date::date as cabi_date,
                               count(trips.*) as cabi_trips
                               from cabi_trips as trips
                               LEFT JOIN cabi_stations_geo_temp AS stations
                               ON trips.start_station = stations.start_short_name AND trips.end_station = stations.end_short_name
                               where stations.end_region_code = 'WDC' and stations.end_region_code='WDC' and trips.start_date::date >= '2017-09-20'
                               GROUP BY 1) as c
                            ON d.trip_date = c.cabi_date
                            order by trip_date
                        """, con=conn)
    comp_df.set_index('trip_date', inplace=True)
    comp_df.plot.line()
    plt.show()
    # Calculate Percent of Trips
    for column in comp_df.columns:
        if column != "trip_date":
            comp_df[column + "_perc"] = comp_df[column] / comp_df[column].sum()
    # Plot Percent of Trips
    perc_col = [col for col in comp_df.columns if col.endswith("_perc")]
    comp_df[perc_col].plot.line()
    plt.show()
