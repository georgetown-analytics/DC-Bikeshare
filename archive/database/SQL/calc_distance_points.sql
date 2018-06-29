select dist_miles - dist_sql as diff
from
(select dist_miles, 
       ST_Distance_Spheroid(
                ST_SetSRID(st_makepoint(start_lon, start_lat),4326),
                ST_SetSRID(st_makepoint(end_lon, end_lat),4326),
                'SPHEROID["WGS 84",6378137,298.257223563]') * 0.000621371 as dist_sql
       
from cabi_stations_geo_temp
limit 10) as aa;