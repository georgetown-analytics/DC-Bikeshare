SELECT ds.weather_date as date,
COUNT(DISTINCT cabi_stations.station) as stations
FROM dark_sky_raw as ds
LEFT JOIN
	((select distinct
		station,
		MIN(station_min_date) AS station_min_date,
		MAX(station_max_date) AS station_max_date
	from
	((select distinct 
		start_station as station,
		MIN(start_date::timestamp::date) AS station_min_date,
		(date_trunc('month', MAX(start_date)) + interval '1 month')::date AS station_max_date
		FROM cabi_trips
		GROUP BY 1)
	union
	(select distinct 
		end_station as station,
		MIN(start_date::timestamp::date) AS station_min_date,
		(date_trunc('month', MAX(start_date)) + interval '1 month')::date AS station_max_date
		FROM cabi_trips
		GROUP BY 1)) as stations
	GROUP BY STATION
	ORDER BY STATION)) as cabi_stations
ON ds.weather_date BETWEEN cabi_stations.station_min_date AND cabi_stations.station_max_date
GROUP BY 1;