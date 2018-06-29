SELECT * FROM crosstab ( 
'SELECT 
start_time::timestamp::date as db_date,
status,
SUM(duration) as duration_seconds
FROM cabi_out_hist 
GROUP BY start_time::timestamp::date, status'   ,
'SELECT DISTINCT status FROM cabi_out_hist order by 1')
 AS (
   db_date date,
   daily_empty_duration integer,
   daily_full_duration integer
 );