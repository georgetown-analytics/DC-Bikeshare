import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Diagnostics of min, max, min of positive duration trips (start timestampis earlier than end timestamp ) by operator
    df = pd.read_sql("""select distinct operatorclean,
                        count(*) as trips,
                        min(EXTRACT(EPOCH FROM enddate - startdate)::int/60) as min_duration,
                        avg(EXTRACT(EPOCH FROM enddate - startdate)::int/60) as avg_duration,
                        max(EXTRACT(EPOCH FROM enddate - startdate)::int/60) as max_duration
                        from dockless_trips
                        where EXTRACT(EPOCH FROM enddate - startdate)::int/60 > 0
                        group by 1;
                     """, con=conn)
    print(df)


