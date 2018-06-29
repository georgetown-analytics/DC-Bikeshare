SELECT * FROM crosstab($$
select distinct 
nbh_names, 
operatorclean,
count(*) as total_rides
from dockless_trips as d
left join dockless_ngh_lookup n_start
on d.startlongitude = n_start.lon and d.startlatitude = n_start.lat
GROUP BY 1, 2
ORDER BY 1, 2$$
,$$SELECT unnest('{jump,lime,mobike,ofo,spin}'::text[])$$)
AS ct ("neighborhood" text, "jump" int, "lime" int, "mobike" int, "ofo" int, "spin" int);
