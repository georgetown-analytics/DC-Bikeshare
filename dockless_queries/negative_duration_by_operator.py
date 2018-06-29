import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Diagnostics of negative duration trips (end timestamp is earlier than start timestamp) by operator
    df = pd.read_sql("""select distinct operatorclean,
                        count(*) as trips,
                        AVG(EXTRACT(EPOCH FROM endutc - startutc))/60 as avg_duration
                        from dockless_trips
                        where EXTRACT(EPOCH FROM endutc - startutc) < 0
                        group by 1;
                     """, con=conn)
    print(df)


