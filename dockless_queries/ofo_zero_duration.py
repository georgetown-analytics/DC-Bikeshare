import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Zero Duration Trips Percentage by Month for Ofo
    df = pd.read_sql("""select distinct
                        extract('year' from startutc) as year,
                        extract('month' from startutc) as month,
                        count(*) as total_trips,
                        sum(CASE WHEN (endutc = startutc) then 1
                             ELSE 0 END) as total_zero_trips,
                        sum(CASE WHEN (endutc = startutc) then 1
                             ELSE 0 END)/count(*)::float * 100 as perc_zero_dur
                        from dockless_trips
                        where operatorclean ='ofo'
                        group by 1, 2
                        order by 1, 2;
                     """, con=conn)
    print(df)

    df = pd.read_sql("""select distinct
                        extract('year' from startutc) as year,
                        extract('month' from startutc) as month,
                        count(*) as total_trips,
                        sum(CASE WHEN EXTRACT(EPOCH FROM endutc - startutc) = 0 then 1
                             ELSE 0 END) as total_zero_trips,
                        sum(CASE WHEN EXTRACT(EPOCH FROM endutc - startutc) = 0 then 1
                             ELSE 0 END)/count(*)::float * 100 as perc_zero_dur
                        from dockless_trips_org
                        where operatorclean ='ofo'
                        group by 1, 2
                        order by 1, 2;
                     """, con=conn)
    print(df)
