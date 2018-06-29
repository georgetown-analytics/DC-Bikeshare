import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Count of Total Bikes and Average bike age by for Operator for all Dockless Trips
    df = pd.read_sql("""select distinct
                        operatorclean,
                        count(*) as total_bikes_used,
                        avg(bike_age) as bike_age
                        from
                        (select distinct
                        operatorclean,
                        bikeid,
                        min(startutc::date) as first_ride,
                        (date_trunc('day', max(startutc)) + interval '1 day')::date as last_ride_plus,
                        (date_trunc('day', max(startutc)) + interval '1 day')::date - min(startutc::date) as bike_age
                        from dockless_trips
                        group by 1, 2) as bike_age
                        group by 1;
                     """, con=conn)
    print(df)
