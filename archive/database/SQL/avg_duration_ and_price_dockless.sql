SELECT 
tripid,
operatorclean,
startutc::date as start_date,
/* Convert Duration to Seconds*/
EXTRACT('hours' FROM (endutc - startutc)) * 3600 + 
EXTRACT('minutes' FROM (endutc - startutc)) * 60 + 
EXTRACT('seconds' FROM (endutc - startutc)) as dur_seconds,
/* Assign appropriate price based on operator*/
COALESCE(
CASE WHEN operatorclean = 'lime' THEN price.limebike ELSE NULL END,
CASE WHEN operatorclean = 'ofo' THEN price.ofo ELSE NULL END,
CASE WHEN operatorclean = 'spin' THEN price.spin ELSE NULL END,
CASE WHEN operatorclean = 'jump' THEN jump_price.cost ELSE NULL END) as trip_cost
FROM dockless_trips as trip_dur
/*Join on non-jump operator pricing*/
LEFT JOIN dockless_price as price
ON trip_dur.operatorclean != 'jump' AND EXTRACT('hours' FROM (endutc - startutc)) * 3600 + 
EXTRACT('minutes' FROM (endutc - startutc)) * 60 + 
EXTRACT('seconds' FROM (endutc - startutc)) BETWEEN price.min_seconds and price.max_seconds
/*Join on jump operator pricing*/
LEFT JOIN jump_price as jump_price
ON trip_dur.operatorclean = 'jump' AND EXTRACT('hours' FROM (endutc - startutc)) * 3600 + 
EXTRACT('minutes' FROM (endutc - startutc)) * 60 + 
EXTRACT('seconds' FROM (endutc - startutc)) BETWEEN jump_price.min_seconds and jump_price.max_seconds
WHERE endutc > startutc 
AND '1 minute' < endutc - startutc 
AND endutc - startutc < '1 day' 
AND operatorclean != 'mobike';
