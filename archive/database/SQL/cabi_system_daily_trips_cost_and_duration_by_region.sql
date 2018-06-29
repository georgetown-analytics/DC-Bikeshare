SELECT DISTINCT 
concat_ws('_to_', stations.end_region_code::text, stations.start_region_code::text) as region_to_region,
trips.member_type,
trips.start_date::timestamp::date as trip_date,
extract(dow from trips.start_date) as dow,
COUNT(*) as total_trips,
AVG(CASE WHEN trips.member_type = 'Member' THEN cabi_price.member_cost ELSE cabi_price.casual_cost + 2 END) AS avg_trip_cost,
AVG(trip.duration/1000) as avg_trip_duration
FROM cabi_trips AS trips
LEFT JOIN cabi_stations_geo_temp AS stations
ON trips.start_station = stations.start_short_name AND trips.end_station = stations.end_short_name
LEFT JOIN cabi_price 
ON trips.duration/1000 BETWEEN cabi_price.min_seconds AND cabi_price.max_seconds
GROUP BY 1, 2, 3, 4;