SELECT ds.weather_date as date,
COUNT(DISTINCT cabi_bikes.bike_number) as cabi_bikes_available
FROM dark_sky_raw as ds
LEFT JOIN
	(SELECT DISTINCT bike_number,
	MIN(start_date::timestamp::date) AS bike_min_date,
    (date_trunc('month', MAX(start_date)) + interval '1 month')::date AS bike_max_date

	FROM cabi_trips
	GROUP BY 1) as cabi_bikes
ON ds.weather_date BETWEEN cabi_bikes.bike_min_date AND cabi_bikes.bike_max_date
GROUP BY 1;