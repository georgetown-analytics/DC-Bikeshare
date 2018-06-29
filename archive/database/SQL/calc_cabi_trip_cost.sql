SELECT cabi_trips.trip_id,
CASE WHEN cabi_trips.member_type = 'Member' THEN cabi_price.member_cost
     ELSE cabi_price.casual_cost + 2 END AS trip_cost
FROM cabi_trips 
LEFT JOIN cabi_price
ON cabi_trips.duration/1000 BETWEEN cabi_price.min_seconds AND cabi_price.max_seconds;