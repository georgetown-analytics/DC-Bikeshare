import pandas as pd


def dockless_trips_by_operator(conn):
    # Dockless Trips by Operator
    df = pd.read_sql("""SELECT * FROM crosstab($$
                        SELECT DISTINCT
                        main.startutc::date AS date,
                        main.operatorclean,
                        COUNT(*) AS trips
                        FROM dockless_trips AS main
                        GROUP BY 1, 2
                        ORDER BY 1, 2$$
                        ,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
                        AS ct ("date" date, "dless_trips_jump" int, "dless_trips_lime" int, "dless_trips_mobike" int, "dless_trips_ofo" int, "dless_trips_spin" int);
                                     """, con=conn)
    return df


def dockless_trip_distance_total(conn):
    # Calculate total dockless trip distance
    df = pd.read_sql("""SELECT * FROM crosstab($$
                        SELECT DISTINCT
                        main.startutc::date AS date,
                        main.operatorclean,
                        SUM(ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]')) AS trip_dist
                        FROM dockless_trips AS main
                        GROUP BY 1, 2
                        ORDER BY 1, 2$$
                        ,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
                    AS ct ("date" date, "dless_tripdist_tot_jump" numeric, "dless_tripdist_tot_lime" numeric, "dless_tripdist_tot_mobike" numeric, "dless_tripdist_tot_ofo" numeric, "dless_tripdist_tot_spin" numeric);
                     """, con=conn)
    return df


def dockless_trip_distance_avg(conn):
    # Calculate average dockless trip distance
    df = pd.read_sql("""SELECT * FROM crosstab($$
                        SELECT DISTINCT
                        main.startutc::date AS date,
                        main.operatorclean,
                        AVG(ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]')) AS trip_dist
                        FROM dockless_trips AS main
                        GROUP BY 1, 2
                        ORDER BY 1, 2$$
                        ,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
                    AS ct ("date" date, "dless_tripdist_avg_jump" numeric, "dless_tripdist_avg_lime" numeric, "dless_tripdist_avg_mobike" numeric, "dless_tripdist_avg_ofo" numeric, "dless_tripdist_avg_spin" numeric);
                     """, con=conn)
    return df


def dockless_overlap(conn):
    # Aggregate if Dockless trip start and ends with quarter mile of Cabi Station and if the Cabi station is empty at trip start time
    df = pd.read_sql("""SELECT DISTINCT
                        startutc::date as date,
                        operatorclean as operator,
                        SUM(st_geo_overlap) / COUNT(*) :: float as dless_geo_start,
                        SUM(end_geo_overlap) / COUNT(*) :: float as dless_geo_end,
                        SUM(st_cap_overlap) / COUNT(*) :: float as dless_cap_start
                        FROM dockless_trips_geo
                        GROUP BY 1, 2
                        ORDER BY 1, 2
                     """, con=conn)
    return df


def dockless_duration_cost(conn):
    # Average trip duration and cost where trips are great than a minute and less than a day.  Mobike not included
    df = pd.read_sql("""SELECT DISTINCT
                        startutc::date as date,
                        operatorclean as operator,
                        /* Convert Duration to Seconds*/
                        AVG(EXTRACT('hours' FROM (endutc - startutc)) * 3600 +
                        EXTRACT('minutes' FROM (endutc - startutc)) * 60 +
                        EXTRACT('seconds' FROM (endutc - startutc))) as dless_dur,
                        /* Assign appropriate price based on operator*/
                        AVG(COALESCE(
                        CASE WHEN operatorclean = 'lime' THEN price.limebike ELSE NULL END,
                        CASE WHEN operatorclean = 'ofo' THEN price.ofo ELSE NULL END,
                        CASE WHEN operatorclean = 'spin' THEN price.spin ELSE NULL END,
                        CASE WHEN operatorclean = 'jump' THEN jump_price.cost ELSE NULL END)) as dless_cost
                        FROM dockless_trips as trip_dur
                        /*Join on non-jump operator pricing*/
                        LEFT JOIN dockless_price as price
                        ON trip_dur.operatorclean != 'jump' AND EXTRACT('hours' FROM (endutc - startutc)) * 3600 +
                        EXTRACT('minutes' FROM (endutc - startutc)) * 60 +
                        EXTRACT('seconds' FROM (endutc - startutc)) BETWEEN price.min_seconds and price.max_seconds
                        /*Join on jump operator pricing*/
                        LEFT JOIN jump_price as jump_price
                        ON trip_dur.operatorclean = 'jump' AND EXTRACT('hours' FROM (endutc - startutc)) * 3600 +
                        EXTRACT('minutes' FROM (endutc - startutc)) * 60 +
                        EXTRACT('seconds' FROM (endutc - startutc)) BETWEEN jump_price.min_seconds and jump_price.max_seconds
                        WHERE endutc > startutc
                        AND '1 minute' < endutc - startutc
                        AND endutc - startutc < '1 day'
                        AND operatorclean != 'mobike'
                        GROUP BY 1, 2
                     """, con=conn)
    return df


def dockless_active_users(conn):
    # Activate users by dockless operator
    df = pd.read_sql("""SELECT * FROM crosstab($$
                        SELECT
                        ds.weather_date as date,
                        dless_users.operatorclean,
                        COUNT(DISTINCT dless_users.userid) as dless_active_users
                        FROM dark_sky_raw as ds
                        /*lime, spin and mobike users*/
                        LEFT JOIN((select distinct
                        max_month_trips.operatorclean,
                        max_month_trips.userid,
                        min(max_month_trips.start_active_date) as start_active_date,
                        max(max_month_trips.end_active_date)::date as end_active_date
                        from (select distinct
                            trips.operatorclean,
                            trips.userid,
                            max_month.max_month,
                            min(trips.startutc)::date as start_active_date,
                            /*IF LAST month of available data then pad to end of month*/
                            CASE when max_month.max_month = extract(month from max(trips.startutc)::date)
                            THEN (date_trunc('month', MAX(trips.startutc)) + interval '1 month')::date - 1
                            ELSE max(trips.startutc)::date END AS end_active_date
                            from dockless_trips as trips
                            LEFT JOIN(select distinct
                            operatorclean,
                            extract(month from max(startutc)::date) as max_month
                            from dockless_trips
                            where operatorclean not in ('ofo')
                            group by 1
                            order by 1) as max_month
                            on trips.operatorclean = max_month.operatorclean
                            where trips.operatorclean not in ('ofo')
                            group by 1, 2, 3
                            order by 1, 2, 3) as max_month_trips
                        group by 1, 2
                        order by 1, 2)
                        union
                        /*ofo users*/
                        (select distinct
                        'ofo' as operatorclean,
                        userid,
                        min(usage_month)::date as start_active_date,
                        (date_trunc('month', MAX(usage_month)) + interval '1 month')::date - 1 AS end_active_date
                        from ofo_users
                        group by 1, 2
                        order by 1, 2)
                        ) as dless_users
                        ON ds.weather_date BETWEEN dless_users.start_active_date AND dless_users.end_active_date
                        where ds.weather_date>= '2017-09-09'
                        GROUP BY 1, 2
                        ORDER BY 1, 2
                        $$
                    ,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
                    AS ct ("date" date, "dless_users_jump" int, "dless_users_lime" int, "dless_users_mobike" int, "dless_users_ofo" int, "dless_users_spin" int)
                    ;
                     """, con=conn)
    return df


def dockless_bikes_available(conn):
    # Bikes available by dockless operator
    df = pd.read_sql("""SELECT * FROM crosstab($$
                         /* Join dockless trip date to bikes available */
                        SELECT DISTINCT
                        trips.startutc::date as date,
                        trips.operatorclean,
                        /* OFO and MOBIKE always 400, the use API, the use DDOT summary*/
                        CASE WHEN trips.operatorclean in ('ofo', 'mobike') THEN 400
                        ELSE CASE WHEN api.bikes_available is null THEN summary.totalbikes
                        ELSE api.bikes_available END END::int as dless_bikes_avail
                        FROM dockless_trips AS trips
                        /*Join on API data first */
                        LEFT JOIN dockless_bikes_api as api
                        ON trips.startutc::date = api.date AND trips.operatorclean = api.operator
                        /*Join on DDOT summary next by year and month*/
                        LEFT JOIN dockless_summary as summary
                        ON EXTRACT('month' FROM trips.startutc) = EXTRACT('month' FROM summary.month)
                        AND EXTRACT('year' FROM trips.startutc) = EXTRACT('year' FROM summary.month)
                        AND trips.operatorclean = summary.operator
                        ORDER BY 1, 2;
                         $$
                           ,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
                        AS ct ("date" date, "dless_bikes_jump" int, "dless_bikes_lime" int, "dless_bikes_mobike" int, "dless_bikes_ofo" int, "dless_bikes_spin" int)
                        ;
                        """, con=conn)
    return df
