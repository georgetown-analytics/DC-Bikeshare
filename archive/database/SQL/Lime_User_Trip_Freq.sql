SELECT DISTINCT trips, count(*) as freq
from 
(SELECT distinct userid, count(*) as trips
FROM dockless_trips
WHERE operatorclean = 'lime'
group by userid
order by count(*)) as user_count
group by trips;