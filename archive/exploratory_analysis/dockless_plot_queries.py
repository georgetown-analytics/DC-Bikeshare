import pandas as pd
import numpy as np
import util_functions as uf


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    '''Single Trips as % of all CaBi passes (not memberships) purchased monthly
        [[PLOT]]
    '''
    df = pd.read_sql("""select
                        month,
                        (single_trip_pass_purch/(multi_day_pass_purch + single_day_pass_purch + single_trip_pass_purch)) as single_pass_perc
                        from cabi_membership
                        where single_trip_pass_purch>0;
                     """, con=conn)
    print(df.tail())
    '''
    Notes for Noah:
        * The goal here is show that the vast majority of casual rides would be impacted by increase in dockless demand
          as our ML will hopefully prove out.
        * This is just a first cut, but wanted to give all the relevant variables and table names.
    '''
    '''
    Percentage of Total Rides: Dockless vs. CaBi (Total and CaBI)
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        date,
                        /*Get Daily Percentage by taking daily totals and dividing by pilot totals*/
                        (cabi_trips_wdc_to_wdc/cabi_trips_wdc_to_wdc_pilot)*100 as "Total CaBi DC to DC",
                        (cabi_trips_wdc_to_wdc_casual/cabi_trips_wdc_to_wdc_casual_pilot)*100 as "Total CaBi DC to DC, Casual",
                        (dless_trips_all/dless_trips_all_pilot)*100 as "Total Dockless Trips"
                        from final_db as db
                        left join
                        /*Aggregate Trips for the entire Pilot for CaBi and Dockless Totals*/
                        (select
                        sum(cabi_trips_wdc_to_wdc) as cabi_trips_wdc_to_wdc_pilot,
                        sum(cabi_trips_wdc_to_wdc_casual) as cabi_trips_wdc_to_wdc_casual_pilot,
                        sum(cabi_trips_wdc_to_wdc_member) as cabi_trips_wdc_to_wdc_member_pilot,
                        sum(dless_trips_all) as dless_trips_all_pilot
                        from final_db
                        where dless_trips_all > 0 and date > '2017-09-10') as tot
                        on db.date = db.date
                        where dless_trips_all > 0 and date > '2017-09-10';
                     """, con=conn)
    print(df.head())

    '''
    Notes for Noah:
        * Should be two plots Cabi Total vs Dockless Total and Cabi Casual Vs Dockless Total
        * X axis should be "date", either figure out how only show every n x-tick or hide x axis tick label and
          describe x axis in overall label such as "Day in Dockless Pilot (9/9/2017 - 2/28/2018).
    '''

    '''Total Dockless Trips (Aggregate) by day of pilot vs Total CaBi Trips by day of pilot (Total and Casual)
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        date,
                        sum(cabi_trips_wdc_to_wdc) as cabi_trips_wdc_to_wdc_pilot,
                        sum(cabi_trips_wdc_to_wdc_casual) as cabi_trips_wdc_to_wdc_casual_pilot,
                        sum(dless_trips_all) as dless_trips_all_pilot
                        from final_db
                        where dless_trips_all > 0
                        group by 1;
                     """, con=conn)
    print(df.head())

    '''
    Notes for Noah:
        * This was originally monthly, but might be more interesting at the daily level.daily and will match plot above
        * X axis should be "date", either figure out how only show every n x-tick or hide x axis tick label and
          describe x axis in overall label such as "Day in Dockless Pilot (9/9/2017 - 4/30/2018).
    '''

    '''
    Frequency of Trips per user (Pareto Chart) for each dockless operator (except for Mobike, no user ids)
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        user_freqs.operatorclean,
                        user_freqs.user_trips,
                        count(*) as freq_user_trips
                        from
                        ((select distinct
                        operatorclean,
                        userid,
                        count(*) as user_trips
                        from dockless_trips
                        where operatorclean in ('lime', 'spin', 'jump')
                              AND userid != '0'
                        group by 1, 2
                        order by operatorclean, count(*))
                        union
                        /*ofo users*/
                        (select distinct
                        'ofo' as operatorclean,
                        userid,
                        sum(trips) as user_trips
                        from ofo_users
                        group by 1, 2
                        order by operatorclean, sum(trips))) as user_freqs
                        group by 1, 2
                        order by 1, 2;
                     """, con=conn)

    # Initialize Excel Instance
    writer = pd.ExcelWriter('Dockless_User_Frequency_Analysis.xlsx')

    for operator in df['operatorclean'].drop_duplicates().tolist():
        operator_df = df[df['operatorclean'] == operator].copy()

        # Calculate Cumulative Sum and Perc
        operator_df['cumulative_sum'] = operator_df['freq_user_trips'].cumsum()
        operator_df['cumulative_percent'] = operator_df['cumulative_sum'] / operator_df['freq_user_trips'].sum()

        # Output to Excel
        operator_df.to_excel(writer, sheet_name=operator, index=False)
    writer.save()
    print(df.head())
    '''
    Notes for Noah:
        * This query since it  will be leveraged for next plot
    '''

    '''
    Stacked Bar Chart showing % of trips taken by users who took 5 trips or less vs greater than 5 trips.
    One bar for each operator for the entire pilot (except Mobike)
    [[PLOT]]'''
    df['le_5'] = np.where(df['user_trips'] <= 5, 'LEQ 5 Trips', "GT 5 Trips")
    le_5_df = df.groupby(['operatorclean', 'le_5'])['freq_user_trips'].sum()
    print(le_5_df)
    '''
    Notes for Noah:
        * Use "le_5_df" for the plot which has a multi-index of "operatorclean" and "le_5"
        * Mobike was kept in here in case we get better userids'
    '''

    '''
    Distribution of Trips by Hour
    [[PLOT]]
    '''
    # Dockless
    df = pd.read_sql("""SELECT DISTINCT
                        op_trips.*,
                        dow_total_trips,
                        op_trips.dockless_trips/dow_total_trips::float as op_perc
                        FROM
                        /* Get dockless trips by day of week and metro operating status*/
                        (SELECT DISTINCT
                        day_of_week,
                        op_status,
                        COUNT(trips.*) AS dockless_trips
                        from dockless_trips AS trips
                        LEFT JOIN metro_hours AS hours
                        ON extract('DOW' FROM trips.startutc) = hours.day_of_week
                        AND trips.startutc::time BETWEEN hours.start_time AND hours.end_time
                        where operatorclean != 'mobike'
                        GROUP BY 1, 2
                        ORDER BY 1, 2) as op_trips
                        /* Get dockless trips by day of week to calculate % of DOW for each metro operating status*/
                        LEFT JOIN
                            (SELECT DISTINCT extract('DOW' FROM startutc) as dow,
                                             count(*) as dow_total_trips
                                             from dockless_trips
                                             where operatorclean != 'mobike'
                                             group by 1) as dow_trips
                        ON dow_trips.dow = op_trips.day_of_week
                        ORDER BY 1, 2;
                        """, con=conn)
    print(df.head())
    # CaBi
    df = pd.read_sql("""SELECT DISTINCT
                        op_trips.*,
                        dow_total_trips,
                        op_trips.cabi_trips/dow_total_trips::float as op_perc
                        FROM
                        /* Get dockless trips by day of week and metro operating status*/
                        (SELECT DISTINCT
                        day_of_week,
                        op_status,
                        member_type,
                        COUNT(trips.*) AS cabi_trips
                        from cabi_trips AS trips
                        /* Join on metro hours*/
                        LEFT JOIN metro_hours AS hours
                        ON extract('DOW' FROM trips.start_date) = hours.day_of_week
                        /* Join region to start station*/
                        JOIN
                        (SELECT distinct short_name, lat, lon, cabi_system.code AS region_code
                        FROM cabi_stations_temp
                        LEFT JOIN cabi_system
                        ON cabi_stations_temp.region_id = cabi_system.region_id) as start_st
                        ON trips.start_station = start_st.short_name
                        /* Join region to end station*/
                        JOIN
                       (SELECT distinct short_name, lat, lon, cabi_system.code AS region_code
                        FROM cabi_stations_temp
                        LEFT JOIN cabi_system
                        ON cabi_stations_temp.region_id = cabi_system.region_id) as end_st
                        ON trips.end_station = end_st.short_name
                                AND trips.start_date::time BETWEEN hours.start_time AND hours.end_time
                                WHERE member_type != 'Unknown'
                                AND start_date >= '09-10-2017'
                                AND start_st.region_code = 'WDC'
                                AND end_st.region_code = 'WDC'
                                GROUP BY 1, 2, 3
                                ORDER BY 1, 2, 3
                                ) as op_trips
                        /* Get cabi trips by day of week and member type to calculate % of DOW for each metro operating status*/
                        LEFT JOIN
                            (SELECT DISTINCT extract('DOW' FROM start_date) as dow,
                         member_type,
                                             count(*) as dow_total_trips
                                             from cabi_trips as trips
                        /* Join region to start station*/
                         JOIN
                         (SELECT distinct short_name, lat, lon, cabi_system.code AS region_code
                          FROM cabi_stations_temp
                          LEFT JOIN cabi_system
                          ON cabi_stations_temp.region_id = cabi_system.region_id) as start_st
                          ON trips.start_station = start_st.short_name
                        /* Join region to end station*/
                         JOIN
                         (SELECT distinct short_name, lat, lon, cabi_system.code AS region_code
                          FROM cabi_stations_temp
                          LEFT JOIN cabi_system
                          ON cabi_stations_temp.region_id = cabi_system.region_id) as end_st
                          ON trips.end_station = end_st.short_name
                                             where start_date >= '09-10-2017'
                                             AND member_type != 'Unknown'
                                             AND start_st.region_code = 'WDC'
                                             AND end_st.region_code = 'WDC'
                                             group by 1,2
                                             ) as dow_trips
                        ON dow_trips.dow = op_trips.day_of_week
                        AND dow_trips.member_type= op_trips.member_type
                        ORDER BY 1, 2
                        """, con=conn)
    print(df.head())
    '''
    Daily Active Users (Dockless) vs CaBi Members
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        date,
                        /* Active Users for Individual Dockless Operators*/
                        dless_users_jump,
                        dless_users_lime,
                        dless_users_mobike,
                        dless_users_ofo,
                        dless_users_spin,
                        /* Total Active Users for Dockless Operators*/
                        (dless_users_jump +
                         dless_users_lime +
                         dless_users_mobike +
                         dless_users_ofo +
                         dless_users_spin) as dless_users_total,
                        /* Total Active Users */
                        (cabi_active_members_day_key +
                        cabi_active_members_monthly +
                        cabi_active_members_annual) as cabi_active_members_total
                        from final_db
                        where dless_trips_all > 0
                        """, con=conn)
    print(df.tail())

    '''
    Notes for Noah:
        * Mobike was kept in here in case we get better userids'
        * Don't have active users for Jump for February will potentially need to get some DDOT
        * This should be done at the daily basis as Lime, Spin and Mobike figures change daily
    '''

    '''
    Geographic Overlap by Operator Over Time
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        date,
                        /* % of trips that Start within quarter mile of CaBi Station*/
                        dless_geo_start_jump,
                        dless_geo_start_lime,
                        dless_geo_start_mobike,
                        dless_geo_start_ofo,
                        dless_geo_start_spin,
                        /* % of trips that End within quarter mile of CaBi Station*/
                        dless_geo_end_jump,
                        dless_geo_end_lime,
                        dless_geo_end_mobike,
                        dless_geo_end_ofo,
                        dless_geo_end_spin
                        from final_db
                        where dless_trips_all > 0
                        """, con=conn)
    print(df.tail())

    '''
    Notes for Noah:
        * Updated Script 6/12/2018 to add back in Jump based on anticipation of new data arriving
    '''

    '''
    Capacity Overlap by Operator Over Time
    [[PLOT]]
    '''
    df = pd.read_sql("""select distinct
                        date,
                        /* % of trips that Start within quarter mile of CaBi Station when said Station is Empty*/
                        dless_cap_start_jump::float,
                        dless_cap_start_lime::float,
                        dless_cap_start_mobike::float,
                        dless_cap_start_ofo::float,
                        dless_cap_start_spin::float
                        from final_db
                        where dless_trips_all > 0
                        """, con=conn)
    print(df.tail())

    '''
    Notes for Noah:
        * Updated Script 6/12/2018 to add back in Jump based on anticipation of new data arriving
        * We only care about dockless starts because where a person ends a dockless trip has no bearing on CaBi station Capacity
    '''
    '''
    % of total trips by Operator per ANC vs CaBi - TWO plots trip starts and trip ends
    [[PLOT]]
    '''
    df = pd.read_sql("""SELECT DISTINCT
                            start_anc.start_anc,
                            start_anc_trips,
                            end_anc_trips,
                            dless_total_trips,
                            start_anc_trips/dless_total_trips::float as dless_start_perc,
                            end_anc_trips/dless_total_trips::float as dless_end_perc,
                            cabi_trips_start,
                            cabi_trips_end,
                            cabi_total_trips,
                            cabi_trips_start/cabi_total_trips::float as cabi_start_perc,
                            cabi_trips_end/cabi_total_trips::float as cabi_end_perc
                            FROM
                            /* Count of dockless start anc trips*/
                            (SELECT DISTINCT
                            start_anc,
                            count(*) as start_anc_trips
                            FROM dockless_trips_geo
                            WHERE start_anc is not null
                            group by 1) as start_anc
                            /* Count of dockless end anc trips*/
                            LEFT JOIN
                            (SELECT DISTINCT
                            end_anc,
                            count(*) as end_anc_trips
                            FROM dockless_trips_geo
                            WHERE end_anc is not null
                            group by 1) as end_anc
                            ON start_anc.start_anc = end_anc.end_anc
                            /* Count of Total Dockless Trips*/
                            LEFT JOIN
                            (SELECT DISTINCT
                             count(*) as dless_total_trips
                             FROM dockless_trips_geo
                             )  as tot
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
                        """, con=conn)
    print(df.tail())

    '''
    Notes for Noah:
        * Updated Script 6/12/2018 to add back in Jump based on anticipation of new data arriving
        * We'll need to adjust the cabi_trip data manually to line up with pilot depending on what data we get
        * This query takes about a minute to run, be patient

    '''

    ''' Daily Utilization using only API data for Jump, Spin and Lime vs CaBi System Wide
        [[PLOT]]
    '''
    df = pd.read_sql("""SELECT
                        api.*,
                        cabi_bikes_avail,
                        cabi_trips,
                        dless_trips_jump,
                        dless_trips_lime,
                        dless_trips_spin,
                        (dless_trips_jump / dless_bikes_jump) as jump_util_rate,
                        (dless_trips_lime / dless_bikes_lime) as lime_util_rate,
                        (dless_trips_spin / dless_bikes_spin) as spin_util_rate,
                        cabi_util_rate
                        FROM
                        (SELECT * FROM crosstab($$
                         /* Join dockless trip date to bikes available */
                        SELECT DISTINCT
                        date,
                        operator,
                        bikes_available
                        FROM dockless_bikes_api
                        WHERE date <= '04-30-2018'
                        ORDER BY 1, 2;
                         $$
                           ,$$SELECT unnest('{jump,lime,spin}'::text[])$$)
                        AS ct ("date" date, "dless_bikes_jump" int, "dless_bikes_lime" int, "dless_bikes_spin" int)) as api
                        LEFT JOIN
                        (select
                        date,
                        cabi_trips,
                        cabi_bikes_avail,
                        cabi_util_rate,
                        dless_trips_jump,
                        dless_trips_lime,
                        dless_trips_spin
                        from final_db) as db
                        on api.date = db.date
                     """, con=conn)
    df.to_csv('util_rate.csv')
    '''
    Notes for Noah:
        * The goal here is show that dockless bike utilization has been much lower than CaBi due to such few bikes being available
        * Also should be interesting to see how the scooters have impacted Lime utilization in March and April (scooters introed on March 12th)
        * This table will only be for the time period we have API data, so mid February to April
        * Just emailed Daniel and should get refreshed API data by this weekend (written 6/1/2018)
    '''
    import sys
    sys.exit()
