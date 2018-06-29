SELECT tablename 
FROM pg_catalog.pg_tables 
WHERE tableowner = 'msussman' AND schemaname='public' AND tablename LIKE '%final_db'
ORDER BY tablename DESC
LIMIT 1;