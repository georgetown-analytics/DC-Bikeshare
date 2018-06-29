from dockless_exploration_graphs import *

if __name__ == '__main__':
    '''
    Distribution of Dockless Trips by Hour
    [[PLOT]]
    '''
    conn = read_only_connect_aws()
    try:
        os.mkdir('./Load Graphs')
    except FileExistsError:
        pass
    load_path = './Load Graphs/'
    google_drive_location = '1LRJWj6wLBWvyBJbN93jXA2dpgF3BLrN3'
    df_dless = pd.read_sql("""SELECT DISTINCT
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
    print(df_dless.head())

    df_cabi = pd.read_sql("""SELECT DISTINCT
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
    print(df_cabi.head())
    # Open google drive connection
    dr = open_drive()

    df_dless['trips_standardized'] = (
        df_dless['dockless_trips'] / df_dless['dockless_trips'].sum())
    df_cabi_mems = df_cabi[df_cabi['member_type'] == 'Member']
    df_cabi_cas = df_cabi[df_cabi['member_type'] == 'Casual']
    df_cabi_mems['trips_standardized'] = (
        df_cabi_mems['cabi_trips'] / df_cabi_mems['cabi_trips'].sum())
    df_cabi_cas['trips_standardized'] = (
        df_cabi_cas['cabi_trips'] / df_cabi_cas['cabi_trips'].sum())
    df = pd.concat([df_dless, df_cabi_mems, df_cabi_cas])
    df['member_type'].fillna('Dockless', inplace=True)

    g = sns.factorplot(
        x='day_of_week', y='trips_standardized',
        hue='op_status', col='member_type', data=df, kind='bar',
        palette='muted', col_order=['Member', 'Casual', 'Dockless'],
        legend=False, size=4, aspect=2)
    g.set_xticklabels(
            ['Sun', 'Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat'],
            fontsize=8)
    g.set_xlabels('Day of the Week', fontsize=10)
    g.set_ylabels('Standarized Trips', fontsize=10)
    g.fig.legend(loc='center', title='Service Block')
    all_in_one_save(
        "All Hours of the Week", load_path, dr,
        google_drive_location)
    # Delete Graphs from Directory
    shutil.rmtree(load_path)
