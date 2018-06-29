/* trips where start and end timestamp are the same*/
SELECT distinct 
operatorclean,
extract(year from startutc) as year,
extract(month from startutc) as month,
count(*) as total_trips,
sum(case when startdate = enddate then 1 else 0 end) as date_same,
sum(case when startdate = enddate then 1 else 0 end)/count(*)::float as date_same_ptc,
sum(case when posct = endposct then 1 else 0 end) as postct_same,
sum(case when posct = endposct then 1 else 0 end)/count(*)::float as posct_same_ptc,
sum(case when startutc = endutc then 1 else 0 end) as utc_same,
sum(case when startutc = endutc then 1 else 0 end)/count(*)::float as utc_same_ptc
FROM dockless_trips
group by 1, 2, 3
order by 1, 2, 3;


/*distance of trips where time stamps are the same (using 'tripdistance' field)*/
SELECT distinct 
operatorclean,
extract(year from startutc) as year,
extract(month from startutc) as month,
count(*) as total_trips,
sum(case when startutc = endutc then 1 else 0 END) as nodur_trips,
min(case when startutc = endutc then tripdistance else null END) as min_nodur_tripdistance,
avg(case when startutc = endutc then tripdistance else null END) as avg_nodur_tripdistance,
max(case when startutc = endutc then tripdistance else null END) as max_nodur_tripdistance,
min(tripdistance) as min_tripdistance,
avg(tripdistance) as avg_tripdistance,
max(tripdistance) as max_tripdistance
FROM dockless_trips
group by 1, 2, 3
order by 1, 2, 3;

/*distance of trips where time stamps are the same (using "distance" field)*/
SELECT distinct 
operatorclean,
extract(year from startutc) as year,
extract(month from startutc) as month,
count(*) as total_trips,
sum(case when startutc = endutc then 1 else 0 END) as nodur_trips,
min(case when startutc = endutc then distance else null END) as min_nodur_distance,
avg(case when startutc = endutc then distance else null END) as avg_nodur_distance,
max(case when startutc = endutc then distance else null END) as max_nodur_distance,
min(distance) as min_distance,
avg(distance) as avg_distance,
max(distance) as max_distance
FROM dockless_trips
group by 1, 2, 3
order by 1, 2, 3;

/*distance of trips where time stamps are the same, calculated*/
SELECT distinct 
operatorclean,
extract(year from startutc) as year,
extract(month from startutc) as month,
count(*) as total_trips,
sum(case when startutc = endutc then 1 else 0 END) as nodur_trips,
min(case when startutc = endutc then ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]') else null END)::float * 0.000621371 as min_nodur_distance,
avg(case when startutc = endutc then ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]') else null END)::float * 0.000621371 as avg_nodur_distance,
max(case when startutc = endutc then ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]') else null END)::float * 0.000621371 as max_nodur_distance,
min(ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]'))::float  * 0.000621371 as min_distance,
avg(ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]'))::float  * 0.000621371 as avg_distance,
max(ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                        ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]'))::float * 0.000621371 as max_distance
FROM dockless_trips
group by 1, 2, 3
order by 1, 2, 3;