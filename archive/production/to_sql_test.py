import requests
import pandas as pd
import util_functions as uf
from sqlalchemy import create_engine


def pull_region_info():
    # Load CaBI region information from API
    region_url = "https://gbfs.capitalbikeshare.com/gbfs/en/system_regions.json"
    regions = requests.get(region_url).json()
    regions_df = pd.DataFrame(regions['data']['regions'])
    return regions_df


def region_code():
    # Extract game information from schedule
    region_code = {'Washington, DC': 'WDC',
                   'Arlington, VA': 'ARL',
                   'Montgomery County, MD (South)': 'MCS',
                   'Montgomery County, MD (North)': 'MCN',
                   'Alexandria, VA': 'ALX',
                   'Fairfax, VA': 'FFX'}
    region_codes = pd.Series(region_code, name='code')
    region_codes_df = region_codes.to_frame().reset_index()
    region_codes_df.columns = ['name', 'code']
    return region_codes_df


if __name__ == "__main__":

    DB_TYPE = 'postgresql'
    DB_DRIVER = 'psycopg2'
    DB_USER = 
    DB_PASS = 
    DB_HOST = 'capstone-bikeshare.cs9te7lm3pt2.us-east-1.rds.amazonaws.com'
    DB_PORT = '5432'
    DB_NAME = 'bikeshare'
    POOL_SIZE = 50
    SQLALCHEMY_DATABASE_URI = '%s+%s://%s:%s@%s:%s/%s' % (DB_TYPE, DB_DRIVER, DB_USER,
                                                          DB_PASS, DB_HOST, DB_PORT, DB_NAME)
    ENGINE = create_engine(
        SQLALCHEMY_DATABASE_URI, pool_size=POOL_SIZE, max_overflow=0)

    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()
    # Pull CaBi System Regions
    regions_df = pull_region_info()
    # Merge on region code
    regions_df = regions_df.merge(region_code(), on='name', how='left')
    regions_df = regions_df[['region_id', 'name', 'code']]
    # Output dataframe as CSV
    outname = "CaBi_System"
    regions_df.to_csv(outname + ".csv", index=False, sep='|')
    # Load to Database
    # uf.aws_load(outname, "cabi_system", cur)
    regions_df.to_sql("cabi_system_test", ENGINE, if_exists='replace', index=False)

    # Commit changes to database
    conn.commit()
