SELECT dockless.operatorclean,
dockless.StartLongitude,
dockless.StartLatitude, 
dockless.EndLongitude,
dockless.EndLatitude, 
start_station.name as start_cabi_station,
start_station.lon as start_cabi_lon,
start_station.lat as start_cabi_lon,
ST_Distance(ST_SetSRID(st_makepoint(dockless.StartLongitude, dockless.StartLatitude),4326), 
    ST_SetSRID(st_makepoint(start_station.lon, start_station.lat),4326)) * 62.1371 as start_station_dist_miles,
end_station.name as end_cabi_station,
end_station.lon as end_cabi_lon,
end_station.lat as end_cabi_lon,
ST_Distance(ST_SetSRID(st_makepoint(dockless.EndLongitude, dockless.EndLatitude),4326), 
    ST_SetSRID(st_makepoint(end_station.lon, end_station.lat),4326)) * 62.1371 as end_station_dist_miles
FROM dockless_trips as dockless
CROSS JOIN LATERAL
(SELECT *
   FROM cabi_stations_temp
   ORDER BY
     ST_SetSRID(st_makepoint(dockless.StartLongitude, dockless.StartLatitude),4326) <-> ST_SetSRID(st_makepoint(lon, lat),4326)
   LIMIT 1) as start_station
CROSS JOIN LATERAL
(SELECT *
   FROM cabi_stations_temp
   ORDER BY
     ST_SetSRID(st_makepoint(dockless.EndLongitude, dockless.EndLatitude),4326) <-> ST_SetSRID(st_makepoint(lon, lat),4326)
   LIMIT 1) as end_station
 order by end_station_dist_miles;