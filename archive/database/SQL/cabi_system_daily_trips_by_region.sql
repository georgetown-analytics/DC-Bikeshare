SELECT DISTINCT 
concat_ws('_to_', stations.start_region_code::text, stations.end_region_code::text) as region_to_region,
trips.start_date::timestamp::date as trip_date,
extract(dow from trips.start_date) as dow,
COUNT(*) as total_trips
FROM cabi_trips AS trips
LEFT JOIN cabi_stations_geo_temp AS stations
ON trips.start_station = stations.start_short_name AND trips.end_station = stations.end_short_name
GROUP BY 1, 2, 3;