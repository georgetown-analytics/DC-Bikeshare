import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Diagnostics of percent of duration trips (start timestamp equals end timestamp ) by operator
    df = pd.read_sql("""select distinct operatorclean,
                        count(*) as total_trips,
                        sum(CASE WHEN EXTRACT(EPOCH FROM endutc - startutc) = 0 then 1
                             ELSE 0 END) as total_zero_trips,
                        sum(CASE WHEN EXTRACT(EPOCH FROM endutc - startutc) = 0 then 1
                             ELSE 0 END)/count(*)::float * 100 as perc_zero_dur
                        from dockless_trips
                        group by 1;
                     """, con=conn)
    print(df)


