import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Validate Distance Fields provided in DDOT data
    df = pd.read_sql("""SELECT operatorclean,
                        StartLongitude,
                        StartLatitude,
                        EndLongitude,
                        EndLatitude,
                        /* no idea what trip distance is all about*/
                        tripdistance,
                        /*distance is in miles*/
                        distance,
                        /* able to match exactly to distance field, we should use ours since we can produce more decimals*/
                        ST_DistanceSpheroid(ST_SetSRID(st_makepoint(StartLongitude, StartLatitude),4326),
                            ST_SetSRID(st_makepoint(EndLongitude, EndLatitude),4326), 'SPHEROID["WGS 84",6378137,298.257223563]') * 0.000621371 as trip_distance_calc
                        FROM dockless_trips
                        where startutc::date = '2017-12-01' and tripdistance != distance;
                     """, con=conn)
    print(df)


