import psycopg2
import psycopg2.extras
import pandas as pd
import os
import time
from pathlib import Path
from dotenv import load_dotenv


def read_only_connect_aws():
    env_path = 'env_readonly.env'
    load_dotenv(dotenv_path=env_path)
    host = "bikeshare-restored.cs9te7lm3pt2.us-east-1.rds.amazonaws.com"
    port = 5432
    database = "bikeshare"

    user = os.environ.get("AWS_READONLY_USER")
    password = os.environ.get("AWS_READONLY_PASS")

    # Connect to aws postgres D
    conn = psycopg2.connect(
            host=host, user=user, port=port, password=password,
            database=database)
    return conn

# Function to load cabi data from AWS. Leaving room to add different load
# types. Right now only allowing a load of all the database


class QueryTool:

    def __init__(self, connection, table=None):
        self.connection = connection
        self.table = table

    def basic(self):
        query = (
            'SELECT * from ') + self.table
        dataframe = pd.read_sql(query, con=self.connection)
        return dataframe

    def missing_check(self):
        query = ("""
            SELECT
                COUNT(*) as total_count,
                dt.operator as operator
                FROM dockless_trips as dt
            GROUP BY
                operator;""")
        dataframe = pd.read_sql(query, con=self.connection)
        return dataframe

    def geo_metric(self, cut):
        self.cut = cut
        query = ("""
            SELECT
                stations.end_region_code,
                stations.start_region_code,
                extract({0} from subq_trip.start_date) as {0},
                COUNT(*) as total_trips
                FROM
                (SELECT * FROM {1} LIMIT 25) as subq_trip
            LEFT JOIN cabi_stations_geo_temp AS stations
            ON subq_trip.start_station = stations.start_short_name
            AND subq_trip.end_station = stations.end_short_name
            GROUP BY
            stations.end_region_code,
            stations.start_region_code,
            extract({0} from subq_trip.start_date);""").format(cut, table)
        dataframe = pd.read_sql(query, con=self.connection)
        return dataframe

    def annual(self, year):
        self.year = year
        start_string = (
            'SELECT * from cabi_trips '
            'WHERE EXTRACT(YEAR FROM start_date)=')
        query = start_string + str(self.year)
        dataframe = pd.read_sql(query, con=self.connection)
        return dataframe

    def describe_data(self):
        cur = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""select *
                   from information_schema.columns
                   where table_schema NOT IN (
                   'information_schema', 'pg_catalog')
                   order by table_schema, table_name""")
        for row in cur:
            print("schema: {schema}, table: {table}, column: {col}, \
            type: {type}".format(
                schema=row['table_schema'], table=row['table_name'],
                col=row['column_name'], type=row['data_type']))


if __name__ == '__main__':
    print('Running')
    conn = read_only_connect_aws()
    CABI_TRIPS = QueryTool(conn, 'cabi_trips')
    CABI_TRIPS.describe_data()
