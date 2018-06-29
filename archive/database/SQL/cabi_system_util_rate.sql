SELECT DISTINCT 
trips.start_date::timestamp::date as trip_date,
COUNT(*)/COUNT(DISTINCT bike_number)::float as cabi_system_util_rate
FROM cabi_trips  AS trips
GROUP BY trips.start_date::timestamp::date;