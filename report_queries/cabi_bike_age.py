import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Count of Total Bikes and Average bike age for all CaBi Trips
    df = pd.read_sql("""select distinct
                        count(*) as total_bikes_used,
                        avg(bike_age) as bike_age
                        from
                        (select distinct
                        bike_number,
                        min(start_date) as first_ride,
                        (date_trunc('day', max(start_date)) + interval '1 day')::date as last_ride_plus,
                        (date_trunc('day', max(start_date)) + interval '1 day')::date - min(start_date::date) as bike_age
                        from cabi_trips
                        group by 1) as bike_age;
                     """, con=conn)
    print(df)
