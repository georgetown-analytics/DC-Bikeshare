import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Determine trips by operator that start or end outside DC
    df = pd.read_sql("""select distinct
                        operatorclean,
                        count(*) as total_rides,
                        sum(case when start_anc is null then 1 else 0 end) as start_outside_dc,
                        sum(case when end_anc is null then 1 else 0 end) as end_outside_dc,
                        sum(case when (start_anc is null) or (end_anc is null) then 1 else 0 end) as start_or_end_outside_dc,
                        sum(case when (start_anc is null) and (end_anc is null) then 1 else 0 end) as start_and_end_outside_dc,
                        sum(case when (start_anc is null) or (end_anc is null) then 1 else 0 end)/count(*)::float as pct_start_or_end
                        from dockless_trips_geo
                        group by 1;
                     """, con=conn)
    print(df)


