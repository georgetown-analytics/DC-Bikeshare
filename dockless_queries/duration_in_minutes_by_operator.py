import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Simply diagnistics of trip distance by operator
    df = pd.read_sql("""select distinct operatorclean,
                        min(EXTRACT(EPOCH FROM enddate - startdate)::int/60) as min_time_diff,
                        mean(EXTRACT(EPOCH FROM enddate - startdate)::int/60) as mean_time_diff,
                        max(EXTRACT(EPOCH FROM enddate - startdate)::int/60) as max_time_diff,
                        count(*) as trips
                        from dockless_trips
                        group by 1, 2
                        order by 1,2;
                     """, con=conn)
    print(df)


