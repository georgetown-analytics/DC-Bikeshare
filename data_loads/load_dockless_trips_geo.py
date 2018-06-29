import util_functions as uf


def create_dockless_trips_geo(cur):
    # This script creates the dockless trips AWS table
    cur.execute("""
    DROP TABLE IF EXISTS dockless_trips_geo;
    CREATE TABLE dockless_trips_geo as
    SELECT
    geo.*,
    /* Determine if Closest Start Station Cabi Station was empty at start of dockless trip */
    start_out_hist.status as st_station_status,
    CASE WHEN start_out_hist.status = 'empty' THEN 1 ELSE 0 END as st_cap_overlap
    FROM
    (SELECT DISTINCT
        dless.tripid,
        dless.uniquetripid,
        dless.operatorclean,
        dless.bikeid,
        dless.userid,
        dless.startutc,
        dless.endutc,
        start_anc.start_anc,
        end_anc.end_anc,
        dless.startlatitude,
        dless.StartLongitude,
        dless.endlatitude,
        dless.endLongitude,
        /* Calculate Trip Distance in Meters*/
        ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
        ST_SetSRID(st_makepoint(endLongitude, endlatitude),4326),
        'SPHEROID["WGS 84",6378137,298.257223563]') as TripDistance_Meters_Calc,
        /* Calculate Distance to Closest CaBi Station from Start Point*/
        ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
        ST_SetSRID(st_makepoint(start_station.lon, start_station.lat),4326),
        'SPHEROID["WGS 84",6378137,298.257223563]') as StCaBi_Distance_Meters,
        start_station.short_name as st_station,
        /* Determine if closest CaBi Station is a quarter mile or less away to start point*/
        CASE WHEN ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
        ST_SetSRID(st_makepoint(start_station.lon, start_station.lat),4326),
        'SPHEROID["WGS 84",6378137,298.257223563]') < 402.336 THEN 1 ELSE 0 END as st_geo_overlap,
        /* Calculate Distance to Closest CaBi Station from End Point*/
        ST_DistanceSpheroid(ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326),
        ST_SetSRID(st_makepoint(end_station.lon, end_station.lat),4326),
        'SPHEROID["WGS 84",6378137,298.257223563]') as EndCaBi_Distance_Meters,
        end_station.short_name as end_station,
        /* Determine if closest CaBi Station is a quarter mile or less away to end point*/
        CASE WHEN ST_DistanceSpheroid(ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326),
        ST_SetSRID(st_makepoint(end_station.lon, end_station.lat),4326),
        'SPHEROID["WGS 84",6378137,298.257223563]') < 402.336 THEN 1 ELSE 0 END as end_geo_overlap
        FROM dockless_trips as dless
        /* JOIN on closest start station*/
        CROSS JOIN LATERAL
        (SELECT short_name, lon, lat
           FROM cabi_stations_temp
           ORDER BY
             ST_SetSRID(st_makepoint(dless.StartLongitude, dless.StartLatitude),4326) <-> ST_SetSRID(st_makepoint(lon, lat),4326)
           LIMIT 1) as start_station
      /* JOIN on closest end station*/
        CROSS JOIN LATERAL
        (SELECT short_name, lon, lat
           FROM cabi_stations_temp
           ORDER BY
             ST_SetSRID(st_makepoint(dless.EndLongitude, dless.EndLatitude),4326) <-> ST_SetSRID(st_makepoint(lon, lat),4326)
           LIMIT 1) as end_station
        /* JOIN ON ANC START*/
        CROSS JOIN LATERAL
        ((SELECT anc_id as start_anc
         FROM anc
         WHERE ST_Intersects(ST_SetSRID(st_makepoint(dless.startLongitude, dless.startLatitude),4326), anc.polygon) = 't'
         )
         UNION
         (WITH  temp (start_anc) AS (VALUES (null))
          SELECT * FROM temp)
         LIMIT 1) as start_anc
        /* JOIN ANC END */
        CROSS JOIN LATERAL
        ((SELECT anc_id as end_anc
         FROM anc
         WHERE ST_Intersects(ST_SetSRID(st_makepoint(dless.endLongitude, dless.endLatitude),4326), anc.polygon) = 't'
         )
         UNION
         (WITH  temp (end_anc) AS (VALUES (null))
          SELECT * FROM temp)
         LIMIT 1) as end_anc) as geo
      /*JOIN ON CABI OUT history by time and start station*/
      LEFT JOIN (select * FROM cabi_out_hist WHERE start_time::date >='2017-9-09' and status = 'empty') as start_out_hist
      ON geo.startutc BETWEEN start_out_hist.start_time AND start_out_hist.end_time
      AND geo.st_station = start_out_hist.terminal_number;""")


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Create docklesS_trips_geo from dockless_trips
    print("Create Dockless Trips Geo")
    create_dockless_trips_geo(cur)
    # Commit changes to database
    conn.commit()
