select distinct 
mt.member_type,
ct.member_type as member_type_org,
count(*) as trips
FROM cabi_trips_membertype as mt
LEFT JOIN cabi_trips as ct
ON 
mt.startdate::date = ct.start_date::date
AND extract(hour from mt.startdate) = extract(hour from ct.start_date)
AND extract(minute from mt.startdate) = extract(minute from ct.start_date)
AND mt.enddate::date = ct.end_date::date
AND extract(hour from mt.enddate) = extract(hour from ct.end_date)
AND extract(minute from mt.enddate) = extract(minute from ct.end_date)
AND mt.bikenumber =  ct.bike_number
group by 1, 2;