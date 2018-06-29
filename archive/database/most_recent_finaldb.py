from psycopg2 import sql
import util_functions as uf
import pandas as pd
from psycopg2 import sql


def most_recent_final_df(conn, cur):
    # Grab the name of the most recent final database
    cur.execute('''SELECT tablename
                   FROM pg_catalog.pg_tables
                   WHERE tableowner = 'msussman' AND schemaname='public' AND tablename LIKE '%final_db_%'
                   ORDER BY tablename DESC
                   LIMIT 1''')
    final_db = cur.fetchone()[0]
    return final_db


def sample_final_df_select(final_db, conn):
    # Sample select from final db
    df = pd.read_sql(sql.SQL("SELECT date FROM {}").format(sql.Identifier(final_db)), con=conn)
    return df


if __name__ == "__main__":
    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    final_db = most_recent_final_df(conn, cur)
    print(final_db)
    sample_df = sample_final_df_select(final_db, conn)
    print(sample_df)
