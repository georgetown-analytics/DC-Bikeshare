SELECT closest_station.*,
CASE WHEN closest_station.dist_miles <= 0.25 then 1 else 0 end as geo_start_overlap,
CASE WHEN out_hist.status = 'empty' and closest_station.dist_miles <= 0.25 then 1 else 0 end as capacity_overlap 
FROM
/* Find the closest CaBi station and calculate the distance in miles*/
(SELECT dan.location_id,
dan.created, 
station.short_name,
ST_Distance(dan.location, ST_SetSRID(st_makepoint(station.lon, station.lat),4326)) * 0.000621371 as dist_miles
FROM dan_dockless as dan
CROSS JOIN LATERAL
(SELECT short_name, lon, lat
   FROM cabi_stations_temp
   ORDER BY
     dan.location <-> ST_SetSRID(st_makepoint(lon, lat),4326)
   LIMIT 1) as station) as closest_station
/* IMPORTANT: For the real dockless data we'll need to determine if the end point is also a geo overlap*/
/* For the closest CaBi station, look up if there is an CaBi outage at said station when the ride started*/
LEFT JOIN cabi_out_hist as out_hist
ON (closest_station.short_name = out_hist.terminal_number) AND (closest_station.created BETWEEN out_hist.start_time AND out_hist.end_time)
;

/* Find the closest CaBi station and calculate the distance in miles*/
SELECT 
dless.operatorclean,
dless.startutc,
dless.endutc,
start_station.short_name as start_short_name,
end_station.short_name as end_short_name,
start_out_hist.status as status_station_status,
ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326), 
    ST_SetSRID(st_makepoint(start_station.lon, start_station.lat),4326), 
    'SPHEROID["WGS 84",6378137,298.257223563]') as closest_start_station_dist,
ST_DistanceSpheroid(ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326),
    ST_SetSRID(st_makepoint(end_station.lon, end_station.lat),4326), 
    'SPHEROID["WGS 84",6378137,298.257223563]') as closest_end_station_dist
FROM dockless_trips as dless
CROSS JOIN LATERAL
(SELECT short_name, lon, lat
   FROM cabi_stations_temp
   ORDER BY
     ST_SetSRID(st_makepoint(dless.StartLongitude, dless.StartLatitude),4326) <-> ST_SetSRID(st_makepoint(lon, lat),4326)
   LIMIT 1) as start_station
CROSS JOIN LATERAL
(SELECT short_name, lon, lat
   FROM cabi_stations_temp
   ORDER BY
     ST_SetSRID(st_makepoint(dless.EndLongitude, dless.EndLatitude),4326) <-> ST_SetSRID(st_makepoint(lon, lat),4326)
   LIMIT 1) as end_station
LEFT JOIN cabi_out_hist as start_out_hist
ON (start_station.short_name = start_out_hist.terminal_number) AND (dless.startutc BETWEEN start_out_hist.start_time AND start_out_hist.end_time)

WHERE dless.startutc::date = '2017-09-20';
