import pandas as pd
import util_functions as uf

if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Trips by Date and Operator
    df = pd.read_sql("""select distinct
                     OperatorClean,
                     count(*) as trips
                     from dockless_trips
                     group by OperatorClean
                     order by OperatorClean
                     """, con=conn)
    print(df)
