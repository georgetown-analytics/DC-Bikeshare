import requests
import pandas as pd
import util_functions as uf


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


def create_cabi_system(cur):
    # This script creates the CaBi System AWS table
    cur.execute("""
    DROP TABLE cabi_system;
    CREATE TABLE cabi_system(
        region_id serial PRIMARY KEY,
        name varchar(100),
        code text
    )
            """)


if __name__ == "__main__":
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
    # Create Table
    create_cabi_system(cur)
    # Load to Database
    uf.aws_load(outname, "cabi_system", cur)
    # Commit changes to database
    conn.commit()
